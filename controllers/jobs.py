import os
from flask import Blueprint, request, render_template, jsonify, current_app
from models import db
from library.grab_bag import fix_ip, o
from library.errors import api_error, ValidationError
from models.job import Job
from models.account import Account
from rq import Queue
from redis import Redis
from workers.jobs import initial_process, send_fax
from datetime import datetime

jobs = Blueprint('jobs', __name__, url_prefix='/jobs')

@jobs.route('/create', methods=['GET', 'POST'])
def create():
    """Creates a new outgoing fax"""

    account_id = Account.authorize(request.values.get('api_key'))
    if account_id == None:
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    ip = fix_ip(request.headers.get('x-forwarded-for', request.remote_addr))

    if request.method == 'POST':

        uploaded_file = request.files['file']
        v = request.values.get

        if uploaded_file or v('body'):

            data = {
                'account_id':       account_id,
                'ip_address':       ip,
                'destination':      v('destination'),
                'send_authorized':  v('send_authorized', 0),
                'cover':            v('cover', 0),
                'cover_name':       v('cover_name'),
                'cover_address':    v('cover_address'),
                'cover_city':       v('cover_city'),
                'cover_state':      v('cover_state'),
                'cover_zip':        v('cover_zip'),
                'cover_country':    v('cover_country'),
                'cover_phone':      v('cover_phone'),
                'cover_email':      v('cover_email'),
                'cover_company':    v('cover_company'),
                'cover_to_name':    v('cover_to_name'),
                'cover_cc':         v('cover_cc'),
                'cover_subject':    v('cover_subject'),
                'cover_status':     v('cover_status','review'),
                'cover_comments':   v('cover_comments'),
                'callback_url':     v('callback_url')
            }
            if uploaded_file:
                data['filename']    = uploaded_file.filename
            else:
                data['body']        = v('body')

            o(data)

            try:
                job = Job(**data);
                job.validate()
            except ValidationError, err:
                return jsonify(api_error(err.ref)), 400

            db.session.add(job)
            db.session.commit()

            if uploaded_file:
                binary = uploaded_file.stream.read()
            else:
                binary = job.body.replace("\r\n", "\n").encode('utf-8')

            redis_conn = Redis.from_url(current_app.config['REDIS_URI'])
            q = Queue('high', connection=redis_conn)
            q.enqueue_call(func=initial_process, args=(job.id, binary),
                           timeout=300)

            return jsonify(job.public_data())
        else:
            return jsonify(api_error("JOBS_NO_ATTACHMENT")), 400

    else:
        return render_template('jobs_create.html')


@jobs.route('/update/<access_key>', methods=['POST'])
def update(access_key):
    """Updates a fax"""

    account_id = Account.authorize(request.values.get('api_key'))
    if not account_id:
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    v = request.values.get

    jobs = Job.query.filter_by(access_key = access_key)
    job = jobs.first()

    if job == None:
        return jsonify(api_error('API_UNAUTHORIZED')), 401
    elif job.account_id and not job.account_id == account_id:
        return jsonify(api_error('API_UNAUTHORIZED')), 401
    elif not job.status == 'ready' and not job.status == 'new' and \
            not job.status == 'uploading':
        return jsonify(api_error('JOBS_NOT_READY')), 401

    if job.data_deleted:
        return jsonify(api_error('JOBS_DATA_DELETED')), 400

    ip = fix_ip(request.headers.get('x-forwarded-for', request.remote_addr))

    job.ip_address = ip
    job.account_id = account_id

    try:
        if v('destination'):
            job.destination = v('destination')

        if v('send_authorized') and v('send_authorized').lower() != "false" \
                and v('send_authorized') != "0":
            job.send_authorized = 1;

        if v('cover') and v('cover').lower() != "false" and v('cover') != "0":
            job.cover = 1;

        if v('cover_name'):
            job.cover_name = v('cover_name')

        if v('cover_address'):
            job.cover_address = v('cover_address')

        if v('cover_city'):
            job.cover_city = v('cover_city')

        if v('cover_state'):
            job.cover_state = v('cover_state')

        if v('cover_zip'):
            job.cover_zip = v('cover_zip')

        if v('cover_country'):
            job.cover_country = v('cover_country')

        if v('cover_phone'):
            job.cover_phone = v('cover_phone')

        if v('cover_email'):
            job.cover_email = v('cover_email')

        if v('cover_company'):
            job.cover_company = v('cover_company')

        if v('cover_to_name'):
            job.cover_to_name = v('cover_to_name')

        if v('cover_cc'):
            job.cover_cc = v('cover_cc')

        if v('cover_subject'):
            job.cover_subject = v('cover_subject')

        if v('cover_status'):
            job.cover_status = v('cover_status')

        if v('cover_comments'):
            job.cover_comments = v('cover_comments')

        if v('callback_url'):
            job.callback_url = v('callback_url')

        job.mod_date = datetime.now()
        job.validate()

        if job.status == 'ready' and job.send_authorized:
            job.status = 'queued'
            db.session.commit()
            redis_conn = Redis.from_url(os.environ.get('REDIS_URI'))
            q = Queue(job.account.get_priority(), connection=redis_conn)
            q.enqueue_call(func=send_fax, args=(job.id,), timeout=3600)
        else:
            db.session.commit()

    except ValidationError, err:
        return jsonify(api_error(err.ref)), 400

    return jsonify(job.public_data())


@jobs.route('/get/<access_key>', methods=['GET'])
def get(access_key):
    """Get the status of a job"""

    account_id = Account.authorize(request.values.get('api_key'))

    jobs = Job.query.filter_by(access_key = access_key)
    job = jobs.first()

    if job == None or (job.account_id != 0 and (not account_id or \
            account_id != job.account_id)):
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    return jsonify(job.public_data())

@jobs.route('/get_by_id/<id>', methods=['GET'])
def get_by_id(id):
    """Get the status of a job by id"""

    account_id = Account.authorize(request.values.get('api_key'))

    jobs = Job.query.filter_by(id = id)
    job = jobs.first()

    if job == None or not account_id or job.account_id != account_id:
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    return jsonify(job.public_data())

@jobs.route('/restart/<access_key>', methods=['POST'])
def restart(access_key):
    """Restarts a failed job"""

    account_id = Account.authorize(request.values.get('api_key'))

    jobs = Job.query.filter_by(access_key = access_key)
    job = jobs.first()
    
    if job == None or not account_id or not account_id == job.account_id:
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    if not job.failed:
        return jsonify(api_error('JOBS_NOT_RESTARTABLE')), 400

    if job.data_deleted:
        return jsonify(api_error('JOBS_DATA_DELETED')), 400

    ip = fix_ip(request.headers.get('x-forwarded-for', request.remote_addr))

    job.ip_address = ip
    job.failed = 0
    job.fail_code = 0
    job.status = 'queued'
    db.session.commit()
    redis_conn = Redis.from_url(os.environ.get('REDIS_URI'))
    q = Queue(job.account.get_priority(), connection=redis_conn)
    q.enqueue_call(func=send_fax, args=(job.id,), timeout=3600)

    return jsonify(job.public_data())

@jobs.route('/delete_data/<access_key>', methods=['POST', 'GET'])
def delete(access_key):
    """Deletes data associated with a job."""

    account_id = Account.authorize(request.values.get('api_key'))

    jobs = Job.query.filter_by(access_key = access_key)
    job = jobs.first()
    
    if job == None or (job.account_id != 0 and (not account_id or \
            account_id != job.account_id)):
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    if not job.status == 'ready' and not job.status == 'sent' and \
            not job.status == 'failed':
        return jsonify(api_error('JOBS_CANNOT_DELETE_NOW')), 401   

    job.delete_data()

    return jsonify(job.public_data())

@jobs.route('/list', methods=['GET'])
def list():
    """List faxes"""

    v = request.values.get

    account_id = Account.authorize(v('api_key'))
    if not account_id:
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    try:
        page = int(v('page', 1))
        if page < 1:
            raise
    except:
        return jsonify(api_error('JOBS_BAD_PAGINATION_VALUE')), 400

    if v('filter'):
        jobs = Job.query.filter_by(account_id= account_id, status= v('filter'))
    else:
        jobs = Job.query.filter_by(account_id= account_id)
    jobs = jobs.order_by(Job.create_date.desc()).paginate(page, 20, False)

    return jsonify({
        'page':     jobs.page,
        'pages':    jobs.pages,
        'per_page': jobs.per_page,
        'total':    jobs.total,
        'has_next': jobs.has_next,
        'has_prev': jobs.has_prev,
        'jobs':     [job.public_data() for job in jobs.items]
    })