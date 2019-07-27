import os
from flask import Blueprint, request, render_template, jsonify, current_app, \
                  make_response
from models import db
from sqlalchemy.exc import IntegrityError
from library.grab_bag import fix_ip, password_hash, random_hash, o
from library.errors import api_error, ValidationError
from library.phaxio import valid_signature
from models.account import Account
from models.transaction import Transaction
from models.failed_payment import FailedPayment
from models.incoming_number import IncomingNumber
from models.incoming_fax import IncomingFax
import stripe
import json
import requests
import traceback

incoming = Blueprint('incoming', __name__, url_prefix='/incoming')

@incoming.route('/provision', methods=['POST', 'OPTIONS'])
def provision():
    """Provision a Phaxio fax number"""

    from library.mailer import email_provision_info

    ip = fix_ip(request.headers.get('x-forwarded-for', request.remote_addr))

    account_id = Account.authorize(request.values.get('api_key'))
    if account_id == None:
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    account = Account.query.get(account_id)

    if len(account.incoming_numbers) > 0:
        return jsonify(api_error('INCOMING_NUMBER_EXISTS')), 400

    if account.credit < 6 and not account.allow_overflow:
        if account.stripe_card and account.auto_recharge:
            if not auto_recharge(account, ip) == True:
                return jsonify(api_error('INCOMING_CARD_DECLINED')), 401
        else:
            return jsonify(api_error('INCOMING_INSUFFICIENT_CREDIT')), 401

    payload = {
        "area_code": request.values.get("area_code"),
        "api_key": os.environ.get('PHAXIO_API_KEY'),
        "api_secret": os.environ.get('PHAXIO_API_SECRET')
    }
    if os.environ.get('PHAXIO_OVERRIDE_RECEIVED'):
        payload["callback_url"] = os.environ.get('PHAXIO_OVERRIDE_RECEIVED')

    try:
        url = "https://api.phaxio.com/v1/provisionNumber"
        r = requests.post(url, data=payload)
        response = json.loads(r.text)

        if response["success"] == False or not "data" in response \
            or not "number" in response["data"]:
            return jsonify(api_error('INCOMING_BOGUS_AREA_CODE')), 400
    except:
        return jsonify(api_error('INCOMING_FAILED_TO_PROVISION')), 500

    data = {
        'account_id':   account_id,
        'fax_number':   response["data"]["number"],
    }
    incoming_number = IncomingNumber(**data);
    db.session.add(incoming_number)
    db.session.commit()

    data2 = {
        'account_id':       account.id,
        'amount':           -6.00,
        'source':           "phaxio",
        'source_id':        data["fax_number"],
        'ip_address':       ip,
        'initial_balance':  account.credit,
        'trans_type':       "incoming_autopay"
    }
    trans = Transaction(**data2)
    db.session.add(trans)
    db.session.commit()

    account.subtract_credit(6)
    email_provision_info(account, data["fax_number"])

    return jsonify(account.public_data())

@incoming.route('/deprovision', methods=['POST', 'OPTIONS'])
def deprovision():
    """Derovision a Phaxio fax number"""

    from library.mailer import email_registration

    ip = fix_ip(request.headers.get('x-forwarded-for', request.remote_addr))

    account_id = Account.authorize(request.values.get('api_key'))
    if account_id == None:
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    account = Account.query.get(account_id)

    if len(account.incoming_numbers) == 0:
        return jsonify(api_error('INCOMING_CANNOT_REMOVE')), 400

    if not delete_number_from_phaxio(account.incoming_numbers[0].fax_number):
        return jsonify(api_error('INCOMING_FAILED_TO_DEPROVISION')), 500

    db.session.delete(account.incoming_numbers[0])
    db.session.commit()

    return jsonify({"success": True})

@incoming.route('/webhook', methods=['POST', 'OPTIONS'])
def webhook_received():
    """Webhook for Phaxio Receive Faxes"""

    from library.mailer import email_receive_fail, email_admin, email_fax
    from boto.s3.connection import S3Connection
    from boto.s3.key import Key
    from werkzeug.utils import secure_filename

    sig = request.headers.get("X-Phaxio-Signature")
    url = request.base_url

    if not valid_signature(os.environ.get("PHAXIO_CALLBACK_TOKEN"), url,
        request.values, request.files, sig):
        return ":("
    
    if not request.values.get("success") or not request.files.get("filename"):
        return ":("

    fax = json.loads(request.values.get("fax"))
    file = request.files.get("filename")

    external_id = fax["id"]
    num_pages = fax["num_pages"]
    from_number = fax["from_number"].replace("+1", "")
    to_number = fax["to_number"].replace("+1", "")

    incoming_numbers = IncomingNumber.query.filter_by(fax_number = to_number)

    if not incoming_numbers or incoming_numbers.first() == None:
        return ":("

    incoming_number = incoming_numbers.first()
    account = incoming_number.account

    if account.base_rate:
        page_cost = account.base_rate
    else:
        page_cost = float(os.environ.get('DEFAULT_COST_PER_PAGE', '0.10'))

    cost = num_pages * page_cost

    if account.credit < cost and not account.allow_overflow:
        if account.stripe_card and account.auto_recharge:
            if not auto_recharge(account, ip) == True:
                email_receive_fail(account, "DECLINE", external_id, from_number,
                    num_pages, cost)
        else:
            email_receive_fail(account, "NO_FUNDS", external_id, from_number,
                num_pages, cost)
            return ":("

    data = {
        'account_id':       account.id,
        'external_id':      external_id,
        'num_pages':        num_pages,
        'cost':             cost,
        'from_number':      from_number,
        'to_number':        to_number,
    }
    incoming_fax = IncomingFax(**data)

    try:
        filename = secure_filename(file.filename)
        file.save("./tmp/%s" % filename)
    except:
        email_admin("Could not save file for Phaxio: %s" % external_id)
        return ":("

    try:
        conn = S3Connection(os.environ.get('AWS_ACCESS_KEY'),
                            os.environ.get('AWS_SECRET_KEY'))
        bucket = conn.get_bucket(os.environ.get('AWS_S3_BUCKET'))
    except:
        email_admin("AWS S3 connect fail for Phaxio: %s" % external_id)
        return ":("

    try:
        k = Key(bucket)
        k.key = 'incoming/' + incoming_fax.access_key + '/fax.pdf'
        k.set_contents_from_filename("./tmp/%s" % filename)
        k.set_acl('public-read')
        incoming_fax.hosted_url = k.generate_url(expires_in=0, query_auth=False)
    except:
        email_admin("AWS S3 write fail for Phaxio: %s" % external_id)
        return ":("

    db.session.add(incoming_fax)
    db.session.commit()

    data2 = {
        'account_id':       account.id,
        'amount':           0 - cost,
        'source':           'phaxio',
        'source_id':        from_number,
        'initial_balance':  account.credit,
        'trans_type':       'received_fax'
    }
    trans = Transaction(**data2)
    db.session.add(trans)
    db.session.commit()

    account.subtract_credit(cost)

    email_fax(account, external_id, from_number, num_pages, cost,
        "./tmp/%s" % filename, incoming_fax.access_key)

    return jsonify({"kthx": "bai"})

@incoming.route('/list', methods=['GET'])
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
        return jsonify(api_error('INCOMING_BAD_PAGINATION_VALUE')), 400


    faxes = IncomingFax.query.filter_by(account_id= account_id)
    faxes = faxes.order_by(IncomingFax.create_date.desc()).paginate(page, 20,
            False)

    return jsonify({
        'page':     faxes.page,
        'pages':    faxes.pages,
        'per_page': faxes.per_page,
        'total':    faxes.total,
        'has_next': faxes.has_next,
        'has_prev': faxes.has_prev,
        'faxes':    [fax.public_data() for fax in faxes.items]
    })

@incoming.route('/view', methods=['GET'])
def view():
    """View a fax"""

    import urllib
    from library.mailer import email_admin

    v = request.values.get

    ip = fix_ip(request.headers.get('x-forwarded-for', request.remote_addr))

    account_id = Account.authorize(v('api_key'))
    if not account_id:
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    try:
        faxes = IncomingFax.query.filter_by(access_key = v('access_key'))
        fax = faxes.first()

        f = urllib.urlopen(fax.hosted_url)
        data = f.read()

        response = make_response(data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=fax.pdf'
        return response
    except:
        msg = ("<h1>Something weird is going on.</h1>"
               "<p><strong>endpoint:</strong> /incoming/view<br/>"
               "<strong>api_key:</strong> %s<br/>"
               "<strong>access_key:</strong> %s<br/>"
               "<strong>ip:</strong> %s<br/>") % (v('api_key'), v('access_key'),
               ip)

        email_admin(msg, "Security alert!")

        return ("<h1>File not found.</h1><p>Apologies for the glitch! Our staff"
                " has been notified in order to better assist you.</p>"), 401

@incoming.route('/delete', methods=['POST', 'OPTIONS'])
def delete():
    """Delete an incoming fax"""

    from library.mailer import email_admin
    from boto.s3.connection import S3Connection
    from boto.s3.key import Key

    v = request.values.get

    access_key = v('access_key')
    account_id = Account.authorize(v('api_key'))

    if not account_id:
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    faxes = IncomingFax.query.filter_by(access_key = access_key)
    fax = faxes.first()

    db.session.delete(fax)
    db.session.commit()

    try:
        conn = S3Connection(os.environ.get('AWS_ACCESS_KEY'),
                            os.environ.get('AWS_SECRET_KEY'))
        bucket = conn.get_bucket(os.environ.get('AWS_S3_BUCKET'))
        k = Key(bucket)
        k.key ='incoming/' + access_key + '/fax.pdf'
        k.delete()
    except:
        email_admin("AWS S3 connect fail for fax deletion: %s" % access_key)

    return jsonify({"success": True})

def auto_recharge(account, ip, session = None):

    if not session:
        session = db.session

    try:
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

        charge = stripe.Charge.create(
            amount=1000,
            currency="usd",
            customer=account.stripe_token,
            description="Fax Robot service for account #%s"% account.id
        )
        data = {
            'account_id':       account.id,
            'amount':           10,
            'source':           'stripe',
            'source_id':        charge["id"],
            'ip_address':       ip,
            'initial_balance':  account.credit,
            'trans_type':       'auto_recharge'
        }
        trans = Transaction(**data)
        session.add(trans)
        session.commit()

        account.add_credit(10, session)

        return True

    except:
        payment = {'_DEBUG': traceback.format_exc()}
        data = {
            'amount':       10,
            'account_id':   account.id,
            'source':       'stripe',
            'debug':        json.dumps(payment),
            'ip_address':   ip,
            'payment_type': 'auto_recharge'
        }
        failed_payment = FailedPayment(**data)
        session.add(failed_payment)
        session.commit()
        return False

def delete_number_from_phaxio(fax_number):
    payload = {
        "number": fax_number,
        "api_key": os.environ.get('PHAXIO_API_KEY'),
        "api_secret": os.environ.get('PHAXIO_API_SECRET')
    }

    try:
        url = "https://api.phaxio.com/v1/releaseNumber"
        r = requests.post(url, data=payload)
        response = json.loads(r.text)

        if response["success"] == False:
            return False
    except:
        return False

    return True