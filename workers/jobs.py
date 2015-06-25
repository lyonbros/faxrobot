import os
from time import sleep
from models import db
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from library.errors import worker_error
from library.grab_bag import o
from models.job import Job
from models.transaction import Transaction
from models.failed_payment import FailedPayment

engine = create_engine(os.environ.get('DATABASE_URI').strip())
Session = sessionmaker(bind=engine)
session = Session()

def initial_process(id, data = None):

    from boto.s3.connection import S3Connection
    from boto.s3.key import Key
    from subprocess import call, check_output, CalledProcessError
    from os.path import isfile, join
    import redis
    from rq import Worker, Queue, Connection
    
    from poster.encode import multipart_encode
    from poster.streaminghttp import register_openers
    import urllib2

    import requests

    job = session.query(Job).get(id)
    job.mod_date = datetime.now()
    job.status = 'uploading'
    session.commit()

    ########################################################################
    #   G3 TIFF CONVERSION PHASE
    ########################################################################

    path = './tmp/' + job.access_key
    o('Creating temporary directory: %s' % path) ###########################

    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except:
        return fail('JOBS_CREATE_DIR_FAIL', job, db)

    if job.filename:
        file_prefix, file_extension = os.path.splitext(job.filename)
    elif job.body:
        file_extension = '.txt'
    else:
        return fail('JOBS_NO_ATTACHMENT_FOUND', job, db)

    if file_extension == '.docx' or file_extension == '.doc':

        if not os.environ.get('SERVEOFFICE2PDF_URL'):
            return fail('JOBS_NO_SERVEOFFICE2PDF', job, db)

        try:
            save_local_file(job.access_key, job.filename, data)
        except:
            return fail('JOBS_LOCAL_SAVE_FAIL', job, db)

        o('Calling ServeOffice2PDF to convert DOCX to PDF.') ###############

        office_url  = os.environ.get('SERVEOFFICE2PDF_URL').strip()
        files       = {"data": open('%s/%s' % (path, job.filename), 'rb')}
        params      = {'filename': job.filename}
        response    = requests.post(office_url, files=files, data=params)

        if not response.status_code == 200:
            return fail('JOBS_PDF_CONVERT_FAIL', job, db)

        o('Successfully converted file to PDF. Now converting to tiff.') ###
        pdf_file = open('%s/%s.pdf' % (path, job.filename), 'wb')
        pdf_file.write(response.content)
        pdf_file.close()

        try:
            convert_to_tiff(job.access_key, job.filename + '.pdf')
        except CalledProcessError, e:
            return fail('JOBS_IMG_CONVERT_FAIL', job, db, str(e))

    elif file_extension == '.pdf':

        try:
            save_local_file(job.access_key, job.filename + ".pdf", data)
        except:
            return fail('JOBS_LOCAL_SAVE_FAIL', job, db)

        try:
            convert_to_tiff(job.access_key, job.filename + ".pdf")
        except CalledProcessError, e:
            return fail('JOBS_IMG_CONVERT_FAIL', job, db, str(e))

    elif file_extension == '.txt':

        txt_filename = job.filename if job.filename else "fax.txt"

        
        save_local_file(job.access_key, txt_filename, data)
        
        try:
            convert_txt_to_ps(job.access_key, txt_filename + ".ps")
        except CalledProcessError, e:
            return fail('JOBS_TXT_CONVERT_FAIL', job, db, str(e))

        try:
            convert_to_tiff(job.access_key, txt_filename + ".ps")
        except CalledProcessError, e:
            return fail('JOBS_IMG_CONVERT_FAIL', job, db, str(e))

    else:
        return fail('JOBS_UNSUPPORTED_FORMAT', job, db)

    files = [ f for f in os.listdir(path) if isfile(join(path,f)) ]

    num_pages = 0

    for f in files:
        file_prefix, file_extension = os.path.splitext(f)
        if file_extension == '.tiff':
            num_pages = num_pages + 1

    if job.account.base_rate:
        cost_per_page = job.account.base_rate
    else:
        cost_per_page = float(os.environ.get('DEFAULT_COST_PER_PAGE', '0.06'))

    job.status = 'processing'
    job.mod_date = datetime.now()
    job.num_pages = num_pages
    job.cost = cost_per_page * num_pages
    job.cover_cost = cost_per_page
    session.commit()

    ########################################################################
    #   OPTIONAL AMAZON S3 UPLOAD PHASE
    ########################################################################

    if os.environ.get('AWS_STORAGE') == "on":
        o('Connecting to S3') ##############################################
        try:
            conn = S3Connection(os.environ.get('AWS_ACCESS_KEY'),
                                    os.environ.get('AWS_SECRET_KEY'))
            bucket = conn.get_bucket(os.environ.get('AWS_S3_BUCKET'))
        except:
            return fail('JOBS_CONNECT_S3_FAIL', job, db)
    
        for f in files:
            try:
                file_prefix, file_extension = os.path.splitext(f)

                if file_extension == '.tiff':
                    o('Uploading to S3: ' + f) #############################
                    k = Key(bucket)
                    k.key = 'fax/' + job.access_key + '/' + f
                    k.set_contents_from_filename(path + '/' + f)
                    k.set_acl('public-read')
            except:
                return fail('JOBS_UPLOAD_S3_FAIL', job, db)

    job.mod_date = datetime.now()

    if job.send_authorized:
        job.status = 'queued'
        session.commit()
        redis_conn = redis.from_url(os.environ.get('REDIS_URI'))
        q = Queue('default', connection=redis_conn)
        q.enqueue_call(func=send_fax, args=(id,), timeout=3600)
    else:
        job.status = 'ready'
        session.commit()
        if job.callback_url:
            send_job_callback(job, db)   

    return "SUCCESS: %s" % id

def send_fax(id):

    from boto.s3.connection import S3Connection
    from boto.s3.key import Key
    from datetime import date
    from subprocess import check_output, CalledProcessError, STDOUT
    import stripe
    import traceback
    import json
    from library.mailer import email_recharge_payment, email_success
    from rq import Worker

    device = Worker.MODEM_DEVICE

    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

    job = session.query(Job).get(id)

    if not job.status == 'ready' and not job.status == 'queued':
        return fail('JOBS_CANNOT_SEND_NOW', job, db)

    if job.data_deleted:
        return fail('JOBS_FAIL_DATA_DELETED', job, db)

    cost = job.cost if not job.cover else job.cost + job.cover_cost

    ########################################################################
    #   MAKE SURE THE CUSTOMER ACTUALLY HAS MONEY PHASE
    ########################################################################

    if os.environ.get('REQUIRE_PAYMENTS') == 'on':
        if job.account.credit - cost < 0 and not job.account.allow_overflow:
            if job.account.stripe_card and job.account.auto_recharge:
                try:
                    charge = stripe.Charge.create(
                        amount=1000,
                        currency="usd",
                        customer=job.account.stripe_token,
                        description="Auto-recharging account %s"% job.account.id
                    )
                    data = {
                        'account_id':       job.account.id,
                        'amount':           10,
                        'source':           'stripe',
                        'source_id':        charge["id"],
                        'job_id':           job.id,
                        'job_destination':  job.destination,
                        'ip_address':       job.ip_address,
                        'initial_balance':  job.account.credit,
                        'trans_type':       'auto_recharge'
                    }
                    trans = Transaction(**data)
                    session.add(trans)
                    session.commit()

                    job.account.add_credit(10, session)
                    email_recharge_payment(job.account, 10, trans.id,
                        charge.source.last4)

                except:
                    payment = {'_DEBUG': traceback.format_exc()}
                    data = {
                        'amount':       10,
                        'account_id':   job.account.id,
                        'source':       'stripe',
                        'debug':        json.dumps(payment),
                        'ip_address':   job.ip_address,
                        'payment_type': 'auto_recharge'
                    }
                    failed_payment = FailedPayment(**data)
                    session.add(failed_payment)
                    session.commit()
                    # JL TODO ~ Notify customer that the card was declined
                    return fail('JOBS_CARD_DECLINED', job, db)    
            else:
                return fail('JOBS_INSUFFICIENT_CREDIT', job, db)

    job.mod_date = datetime.now()
    job.start_date = datetime.now()
    job.attempts = job.attempts + 1
    job.status = 'started'
    session.commit()

    files_to_send = []

    ########################################################################
    #   COVER SHEET GENERATION PHASE
    ########################################################################

    path = './tmp/' + job.access_key
    o('Touching temporary directory: %s' % path) ###########################

    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except:
        return fail('JOBS_CREATE_DIR_FAIL', job, db)

    if job.cover:
        o('Generating cover sheet') ########################################

        try:
            o('Generating cover.png') ######################################

            cmd = ["convert", "-density", "400", "-flatten",
                   "./media/cover_sheets/default.pdf", "-gravity",
                   "None"]
            v = 300

            if job.cover_name:
                cmd.extend(["-annotate", "+468+%s" % v, job.cover_name])
                cmd.extend(["-annotate", "+2100+1215", job.cover_name])
                v = v + 80

            if job.cover_address:
                cmd.extend(["-annotate", "+468+%s" % v, job.cover_address])
                v = v + 80

            if job.cover_city or job.cover_state or job.cover_zip:
                cmd.extend(["-annotate", "+468+%s" % v, 
                    "%s, %s %s" % (job.cover_city, job.cover_state,
                    job.cover_zip)])
                v = v + 80

            if job.cover_country:
                cmd.extend(["-annotate", "+468+%s" % v, job.cover_country])
                v = v + 80

            if job.cover_phone:
                cmd.extend(["-annotate", "+468+%s" % v, job.cover_phone])
                v = v + 80

            if job.cover_email:
                cmd.extend(["-annotate", "+468+%s" % v, job.cover_email])
                v = v + 80

            if job.cover_to_name:
                cmd.extend(["-annotate", "+800+1215", job.cover_to_name])

            if job.cover_subject:
                cmd.extend(["-annotate", "+800+1340", job.cover_subject])

            cmd.extend(["-annotate", "+2100+1340", "%s" % job.num_pages])
            cmd.extend(["-annotate", "+800+1465", "%s" % date.today()])

            if job.cover_cc:
                cmd.extend(["-annotate", "+2100+1465", job.cover_cc])

            if "urgent" in job.cover_status:
                cmd.extend(["-annotate", "+473+1740", "X"])

            if "review" in job.cover_status:
                cmd.extend(["-annotate", "+825+1740", "X"])

            if "comment" in job.cover_status:
                cmd.extend(["-annotate", "+1285+1740", "X"])

            if "reply" in job.cover_status:
                cmd.extend(["-annotate", "+1910+1740", "X"])

            if "shred" in job.cover_status:
                cmd.extend(["-annotate", "+2420+1740", "X"])

            cmd.extend([
                "-pointsize",
                "11",
                "./tmp/" + job.access_key + "/cover.png"
            ])
            output = check_output(cmd)
        except CalledProcessError, e:
            return fail('JOBS_COVER_MAIN_FAIL', job, db, str(e))

        if job.cover_company:
            try:
                o('Generating company.png') ################################

                cmd = ["convert", "-density", "400", "-gravity", "Center",
                       "-background", "black", "-fill", "white",
                       "-pointsize", "20", "-size", "1400x",
                       "caption:%s" % job.cover_company, "-bordercolor",
                       "black", "-border", "30",
                       "./tmp/" + job.access_key + "/company.png"]
                output = check_output(cmd)
            except CalledProcessError, e:
                return fail('JOBS_COVER_COMPANY_FAIL', job, db, str(e))

            try:
                o('Overlaying company.png on cover.png') ###################

                cmd = ["composite", "-density", "400", "-gravity",
                       "NorthEast", "-geometry", "+300+200",
                       "./tmp/" + job.access_key + "/company.png",
                       "./tmp/" + job.access_key + "/cover.png",
                       "./tmp/" + job.access_key + "/cover.png"]
                output = check_output(cmd)
            except CalledProcessError, e:
                return fail('JOBS_COVER_OVERLAY_FAIL', job, db, str(e))

        if job.cover_comments:
            try:
                o('Generating comments.png') ###############################

                cmd = ["convert", "-density", "400", "-gravity",
                       "NorthWest", "-background", "white", "-fill",
                       "black", "-pointsize", "11", "-size", "2437x2000",
                       "-font", "Liberation-Mono-Regular",
                       "caption:%s" % job.cover_comments,
                       "./tmp/" + job.access_key + "/comments.png"]
                output = check_output(cmd)
            except CalledProcessError, e:
                return fail('JOBS_COVER_COMMENTS_FAIL', job, db, str(e))

            try:
                o('Overlaying comments.png on cover.png') ##################

                cmd = ["composite", "-density", "400", "-gravity", "None",
                       "-geometry", "+468+2000",
                       "./tmp/" + job.access_key + "/comments.png",
                       "./tmp/" + job.access_key + "/cover.png",
                       "./tmp/" + job.access_key + "/cover.png"]
                output = check_output(cmd)
            except CalledProcessError, e:
                return fail('JOBS_COVER_OVERLAY_FAIL', job, db, str(e))

        try:
            o('Converting cover.png to G3 .tiff') ##########################

            cmd = ["convert", "-scale", "50%",
                   "./tmp/" + job.access_key + "/cover.png",
                   "fax:./tmp/" + job.access_key + "/cover.tiff"]
            output = check_output(cmd)
        except CalledProcessError, e:
            return fail('JOBS_COVER_TIFF_FAIL', job, db, str(e))

        files_to_send.append(u'%s/cover.tiff' % path)

    ########################################################################
    #   LOAD FILES PHASE
    ########################################################################

    filename = job.filename if job.filename else "fax.txt"

    if os.environ.get('AWS_STORAGE') == "on":
        o('Connecting to S3') ##################################################
        try:
            conn = S3Connection(os.environ.get('AWS_ACCESS_KEY'),
                                os.environ.get('AWS_SECRET_KEY'))
            bucket = conn.get_bucket(os.environ.get('AWS_S3_BUCKET'))
        except:
            return fail('JOBS_CONNECT_S3_FAIL', job, db)

        try:
            for i in range(0, job.num_pages):

                num = ("0%s" % i) if i < 10 else "%s" % i

                o('Download: %s/%s.%s.tiff' % (job.access_key, filename, num))

                k = Key(bucket)
                k.key = 'fax/%s/%s.%s.tiff' %(job.access_key, filename, num)
                k.get_contents_to_filename('%s/%s.%s.tiff' % (path,
                        filename, num))

                files_to_send.append('%s/%s.%s.tiff' %(path, filename, num))
        except:
            return fail('JOBS_DOWNLOAD_S3_FAIL', job, db)
    else:
        for i in range(0, job.num_pages):
            num = ("0%s" % i) if i < 10 else "%s" % i
            files_to_send.append('%s/%s.%s.tiff' %(path, filename, num))

    ########################################################################
    #   SEND FAX PHASE
    ########################################################################
    try:
        o('Modem dialing: 1%s' % job.destination)

        cmd = ["efax", "-d", device, "-o1flll ", "-t",
               "1%s" % job.destination]
        cmd.extend(files_to_send)
        output = check_output(cmd, stderr=STDOUT)
        o('%s' % output)

    except CalledProcessError, e:

        output = str(e.output)

        if "No Answer" in output:
            if os.environ.get('REQUIRE_PAYMENTS') == 'on':
                o('No answer. Charge the customer anyway for wasting our time.')
                o('Debiting $%s on account ID %s' % (cost, job.account.id))
                commit_transaction(job, cost, 'no_answer_charge')            

            return fail('JOBS_TRANSMIT_NO_ANSWER', job, db, output)

        elif "number busy or modem in use" in output:
            o('Line busy.')
            return fail('JOBS_TRANSMIT_BUSY', job, db, output)

        else:
            o('Transmit error: %s' % output)
            return fail('JOBS_TRANSMIT_FAIL', job, db, output)

    o('Job completed without error!')
    job.debug = output
    job.mod_date = datetime.now()
    job.end_date = datetime.now()
    job.status = 'sent'
    session.commit()

    o('Deleting data lol.')
    job.delete_data(session)

    if job.account.email_success:
        email_success(job)

    if job.callback_url:
        send_job_callback(job, db)

    if os.environ.get('REQUIRE_PAYMENTS') == 'on':
        o('Debiting $%s on account ID %s' % (cost, job.account.id))
        commit_transaction(job, cost, 'job_complete')

def commit_transaction(job, cost, trans_type, note = None):
    data = {
        'account_id':       job.account.id,
        'amount':           cost * -1,
        'job_id':           job.id,
        'job_destination':  job.destination,
        'ip_address':       job.ip_address,
        'initial_balance':  job.account.credit,
        'trans_type':       trans_type
    }
    if note:
        data['note'] = note

    transaction = Transaction(**data)
    session.add(transaction)
    session.commit()

    job.account.subtract_credit(cost, session)

def convert_to_tiff(access_key, filename):

    from subprocess import check_output

    o('Convert %s to .tiff' % filename) ########################################

    file_prefix, file_extension = os.path.splitext(filename)

    command = [
        "convert",
        "-density",
        "200 ",
        "-resize",
        "1700x2200 ",
        "./tmp/" + access_key + "/" + filename,
        # "-flatten", # lol
        "fax:./tmp/" + access_key + "/"+ file_prefix +".%02d.tiff"
    ]
    output = check_output(command)

def convert_txt_to_ps(access_key, filename):

    from subprocess import check_output

    o('Convert %s to .ps' % filename) ########################################

    file_prefix, file_extension = os.path.splitext(filename)

    command = [
        "paps",
        "--font",
        "Droid Sans Mono",
        "--cpi",
        " 12",
        # "--header", # JL NOTE ~ probably don't want to have this
        file_prefix
    ]
    output = check_output(command, cwd="./tmp/"+access_key)

    f = open('./tmp/' + access_key + '/' + filename, 'wb')
    f.write(output)
    f.close()

def save_local_file(access_key, filename, data):

    o('Saving local file: %s' % filename) ######################################

    f = open('./tmp/' + access_key + '/' + filename, 'wb')
    f.write(data)
    f.close()

def fail(ref, job, db, debug=None):

    from library.mailer import email_fail

    o('JOB FAILED: %s (%s)' % (ref, debug))

    error = worker_error(ref)
    job.failed = 1
    job.fail_code = error["code"]
    job.fail_date = datetime.now()
    job.mod_date = datetime.now()
    job.status = 'failed'
    job.debug = error["msg"] if debug == None else debug
    session.commit()

    if job.account.email_fail:
        email_fail(job, error["msg"], error["code"], error["status"])

    if job.callback_url:
        send_job_callback(job, db)

    return "FAILED"

def send_job_callback(job, db):
    import requests
    import traceback

    job.callback_date = datetime.now()

    try:
        r = requests.post(job.callback_url, data=job.public_data(), timeout=5)
        r.raise_for_status()
        o("Sent callback: %s; (HTTP 200)" % job.callback_url)
    except:
        o("CALLBACK FAIL: %s / %s" % (job.callback_url, traceback.format_exc()))
        job.callback_fail = job.callback_fail + 1
    
    session.commit()
    

    
