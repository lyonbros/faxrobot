import os
from flask import Blueprint, request, render_template, jsonify, current_app
from models import db
from sqlalchemy.exc import IntegrityError
from rq import Queue
from redis import Redis
from library.grab_bag import fix_ip, password_hash, random_hash, o
from library.errors import api_error, ValidationError
from models.account import Account
from models.transaction import Transaction
from models.failed_payment import FailedPayment
from models.password_reset import PasswordReset

accounts = Blueprint('accounts', __name__, url_prefix='/accounts')

@accounts.route('/create', methods=['GET', 'POST', 'OPTIONS'])
def create():
    """Creates a new user account"""

    from library.mailer import email_registration

    ip = fix_ip(request.headers.get('x-forwarded-for', request.remote_addr))

    if request.method == 'POST':

        v = request.values.get
        data = {
            'email':        v('email'),
            'password':     v('password'),
            'first_name':   v('first_name'),
            'last_name':    v('last_name'),
            'address':      v('address'),
            'address2':     v('address2'),
            'city':         v('city'),
            'state':        v('state'),
            'zip':          v('zip'),
        }
        try:
            account = Account(**data)
            account.validate()
        except ValidationError, err:
            return jsonify(api_error(err.ref)), 400

        try:
            db.session.add(account)
            db.session.commit()
        except IntegrityError:
            return jsonify(api_error('ACCOUNTS_CREATE_FAIL')), 400

        email_registration(account)

        return jsonify(account.public_data())

    else:
        return render_template('accounts_create.html');

@accounts.route('/login', methods=['GET', 'POST'])
def login():
    """Logs into a user account"""

    if request.method == 'POST':
        v = request.values.get
        emails = Account.query.filter_by(email=v('email'))
        account = emails.first()

        if account == None:
            return jsonify(api_error('ACCOUNTS_LOGIN_ERROR')), 401
        elif account.password != password_hash(v('password')):
            return jsonify(api_error('ACCOUNTS_LOGIN_ERROR')), 401

        return jsonify(account.public_data())
    else:
        return render_template('accounts_login.html');

@accounts.route('/get', methods=['GET'])
def get():
    """Gets the account information, provided a correct api_key is specified."""
    account_id = Account.authorize(request.values.get('api_key'))
    if account_id == None:
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    account = Account.query.get(account_id)

    return jsonify(account.public_data())

@accounts.route('/update', methods=['POST'])
def update():
    """Updates an account"""

    from datetime import datetime
    import stripe
    import traceback
    import json
    from library.mailer import email_password_change

    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

    ip = fix_ip(request.headers.get('x-forwarded-for', request.remote_addr))

    account_id = Account.authorize(request.values.get('api_key'))
    if not account_id:
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    account = Account.query.get(account_id)

    v = request.values.get

    try:
        if v('email'):

            existing = Account.query.filter_by(email=v('email'))

            if existing.first() and not existing.first().id == account.id:
                raise ValidationError('ACCOUNTS_EMAIL_TAKEN')

            account.email = v('email')

        if v('password'):

            if not v('old_password'):
                raise ValidationError('ACCOUNTS_INVALID_OLD_PASSWORD')

            if not account.password == password_hash(v('old_password')):
                raise ValidationError('ACCOUNTS_INVALID_OLD_PASSWORD')

            account.password = password_hash(v('password'))

        if v('first_name'):
            account.first_name = v('first_name')

        if v('last_name'):
            account.last_name = v('last_name')

        if v('address'):
            account.address = v('address')

        if v('address2'):
            account.address2 = v('address2')

        if v('city'):
            account.city = v('city')

        if v('state'):
            account.state = v('state')

        if v('zip'):
            account.zip = v('zip')

        if v('auto_recharge') != None:
            account.auto_recharge = 1 if v('auto_recharge') == "1" else 0

        if v('email_success') != None:
            account.email_success = 1 if v('email_success') == "1" else 0

        if v('email_fail') != None:
            account.email_fail = 1 if v('email_fail') == "1" else 0

        if v('email_list') != None:
            account.email_list = 1 if v('email_list') == "1" else 0

        if v('stripe_token') and v('last4'):
            try:
                customer = stripe.Customer.create(
                    description="%s Customer %s" % (
                        os.environ.get('PROJECT_NAME'), account.id),
                    email=account.email,
                    source=v('stripe_token') # 'trol'
                )
                account.stripe_token = customer["id"]
                account.stripe_card = customer["sources"]["data"][0]["id"]
                account.last4 = v('last4')
            except:
                payment = {'_DEBUG': traceback.format_exc()}
                data = {
                    'amount':       0,
                    'account_id':   account.id,
                    'source':       'stripe',
                    'debug':        json.dumps(payment),
                    'ip_address':   ip,
                    'payment_type': 'stored_payment'
                }
                failed_payment = FailedPayment(**data)
                db.session.add(failed_payment)
                db.session.commit()
                return jsonify(api_error('ACCOUNTS_STORED_PAYMENT_FAIL')), 400

        account.mod_date = datetime.now()
        account.validate()
        db.session.commit()

        # Send notification email for password / API key change
        if v('password'):
            email_password_change(account)

        info = account.public_data()
        info['mod_date'] = datetime.now()

    except ValidationError, err:
        return jsonify(api_error(err.ref)), 400

    return jsonify(info)

@accounts.route('/reset_api_key', methods=['POST'])
def reset_api_key():
    """Resets the API key for an account"""

    from library.mailer import email_api_key_change
    from datetime import datetime

    account_id = Account.authorize(request.values.get('api_key'))
    if not account_id:
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    account = Account.query.get(account_id)
    if account.password != password_hash(request.values.get('password')):
        return jsonify(api_error('ACCOUNTS_LOGIN_ERROR')), 401

    account.api_key = random_hash("%s%s" % (account.email, account.password))
    account.mod_date = datetime.now()
    db.session.commit()

    email_api_key_change(account)

    return jsonify({
        'api_key': account.api_key
    })
        

@accounts.route('/remove_card', methods=['POST'])
def remove_card():
    """Removes stored credit card info from the account"""

    from datetime import datetime
    import json
    import stripe

    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

    account_id = Account.authorize(request.values.get('api_key'))
    if not account_id:
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    account = Account.query.get(account_id)

    if account.stripe_token and account.stripe_card:
        try:
            customer = stripe.Customer.retrieve(account.stripe_token)
            customer.sources.retrieve(account.stripe_card).delete()
        except:
            pass # oh well, whatever. fuck it.

    account.stripe_token = None
    account.stripe_card = None
    account.last4 = None
    account.mod_date = datetime.now()
    db.session.commit()

    return jsonify(account.public_data())

@accounts.route('/bootstrap', methods=['GET', 'POST', 'OPTIONS'])
def bootstrap():
    """
    Implicitly creates a user account and logs them in by processing a Stripe
    payment and email. If the email address belongs to a registered account, it
    requires the account password to authorize the payment and login attempt.
    """
    import json
    import stripe
    import sys
    import traceback
    from library.mailer import email_payment
    from datetime import datetime

    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

    account_id = Account.authorize(request.values.get('api_key'))
    ip = fix_ip(request.headers.get('x-forwarded-for', request.remote_addr))

    if request.method == 'POST':

        v = request.values.get
        emails = Account.query.filter_by(email=v('email'))
        account = emails.first()

        o("Received bootstrap payment login: %s" % v('email'))

        if account_id and account != None and account.id != account_id:
            o("Account exists but user is logged in as someone else. Error.")
            return jsonify(api_error('ACCOUNTS_LOGIN_ERROR')), 401
            
        if account != None and account.password != password_hash(v('password'))\
                and not account_id:
            o("Account exists but password mismatch. Erroring out.")
            return jsonify(api_error('ACCOUNTS_LOGIN_ERROR')), 401

        temporary_password = None

        if account == None:
            o("Creating account with temporary password.")
            temporary_password = random_hash(v('email'))[:8]
            data = {
                'email':        v('email'),
                'password':     temporary_password
            }
            try:
                account = Account(**data)
            except ValidationError, err:
                return jsonify(api_error(err.ref)), 400

            try:
                account.validate()
                db.session.add(account)
            except IntegrityError:
                return jsonify(api_error('ACCOUNTS_CREATE_FAIL')), 400

        o("Verifying payment with Stripe API.")
        failed = False

        try:
            payment = stripe.Charge.create(
                amount=int(float(v('amount')) * 100),
                currency="usd",
                source=v('stripe_token'),
                description="Bootstrap payment"
            )
        except:
            o("STRIPE UNEXPECTED ERROR:", sys.exc_info()[0])
            failed = True
            payment = {'_DEBUG': traceback.format_exc()}

        o(payment)

        if not failed and payment and payment.status == "succeeded":
            o("Payment success.")
            db.session.commit()
            data = {
                'account_id':       account.id,
                'amount':           v('amount'),
                'source':           'stripe',
                'source_id':        payment.id,
                'ip_address':       ip,
                'initial_balance':  account.credit,
                'trans_type':       'payment'
            }
            trans = Transaction(**data)
            db.session.add(trans)
            db.session.commit()

            o("Adding credit to account.")
            charged = float(payment.amount) / float(100)
            account.add_credit(charged)
            email_payment(account, charged, trans.id, payment.source.last4,
                    temporary_password)

        else:
            o("--- PAYMENT FAIL. LOGGING INFO ---")
            db.session.expunge_all()
            data = {
                'amount':       v('amount'),
                'account_id':   account.id,
                'source':       'stripe',
                'debug':        json.dumps(payment),
                'ip_address':   ip,
                'payment_type': 'bootstrap'
            }
            failed_payment = FailedPayment(**data)
            db.session.add(failed_payment)
            db.session.commit()
            return jsonify(api_error('ACCOUNTS_PAYMENT_FAIL')), 400

        result = account.public_data()
        if temporary_password:
            result['temporary_password'] = temporary_password

        return jsonify(result)

    else:
        return render_template('accounts_bootstrap.html');

@accounts.route('/transactions', methods=['GET'])
def transactions():
    """List transactions"""

    v = request.values.get

    page = int(v('page', 1))

    account_id = Account.authorize(v('api_key'))
    if not account_id:
        return jsonify(api_error('API_UNAUTHORIZED')), 401

    account = Account.query.get(account_id)

    res = Transaction.query.filter_by(account_id= account_id)
    res = res.order_by(Transaction.create_date.desc()).paginate(page, 15, False)

    return jsonify({
        'page':         res.page,
        'pages':        res.pages,
        'per_page':     res.per_page,
        'total':        res.total,
        'has_next':     res.has_next,
        'has_prev':     res.has_prev,
        'transactions': [trans.public_data() for trans in res.items]
    })

@accounts.route('/email_password_reset', methods=['GET', 'POST'])
def email_password_reset():
    """Emails a password reset"""

    if request.method == 'POST':

        from library.mailer import email_password_reset

        v = request.values.get

        emails = Account.query.filter_by(email=v('email'))
        account = emails.first()

        if account:
            password_reset = PasswordReset(account.id)
            db.session.add(password_reset)
            db.session.commit()
            email_password_reset(v('email'), password_reset, account)

        return jsonify({'ok': 'whatever'})
    else:
        return render_template('accounts_email_password_reset.html');


@accounts.route('/reset_password', methods=['POST'])
def reset_password():
    """Actually reset a password using the hash"""

    from datetime import datetime

    v = request.values.get

    reset_hash = PasswordReset.query.filter_by(reset_hash=v('reset_hash'))
    reset_hash = reset_hash.first()

    if not reset_hash:
        return jsonify(api_error('ACCOUNTS_INVALID_RESET_HASH')), 401

    if reset_hash.used:
        return jsonify(api_error('ACCOUNTS_INVALID_RESET_HASH')), 401

    account = Account.query.get(reset_hash.account_id)
    account.password = account.password = password_hash(v('password'))
    account.mod_date = datetime.now()
    reset_hash.used = 1
    reset_hash.mod_date = datetime.now()
    db.session.commit()

    return jsonify(account.public_data())