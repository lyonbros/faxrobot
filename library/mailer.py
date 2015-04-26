import mandrill
import os

client = mandrill.Mandrill(os.environ.get('MANDRILL_API_KEY'))
base_url = os.environ.get('FAXROBOT_URL')

def email_registration(account):
    message = {
        'subject': 'Welcome to Fax Robot!',
        'html': ('<p>Thanks for registering for Fax Robot! Your new account is '
                 'ready. To log in, visit <a href="%s/accounts/login">%s'
                 '/accounts/login</a>.</p><p>I\'ll send you emails with '
                 'important account-related updates, like a notification when '
                 'your faxes are sent (or they fail to send for some reason). '
                 'I respect your email address and won\'t send you junk email. '
                 'You can change your email notification preferences by '
                 'visiting <a href="%s/account">%s/account</a>.</p><p>I hope '
                 'you have as much fun using the service as I do '
                 'sending faxes on your behalf.</p><p>Thanks again,</p><p>Fax '
                 'Robot</p>') % (base_url, base_url, base_url, base_url)
    }

    send_email(message, account)

def email_password_change(account):
    message = {
        'subject': 'Fax Robot password changed',
        'html': ('<p>Just a heads up: your Fax Robot password was changed.</p>'
                 '<p>If you weren\'t aware of this, please email '
                 '<a href="mailto:support@faxrobot.io">support@faxrobot.io</a> '
                 'as soon as possible.</p><p>--Fax Robot</p>')
    }
    send_email(message, account)

def email_api_key_change(account):
    message = {
        'subject': 'Fax Robot API key changed',
        'html': ('<p>Just a heads up: your Fax Robot API key was changed.</p>'
                 '<p>If you weren\'t aware of this, please email '
                 '<a href="mailto:support@faxrobot.io">support@faxrobot.io</a> '
                 'as soon as possible.</p><p>--Fax Robot</p>')
    }
    send_email(message, account)

def email_payment(account, charged, transaction_id, payment_last4,
        temporary_password = None):

    from datetime import datetime

    if temporary_password:
        html = ('<p><strong>Your temporary password is: <em>%s</em></strong>'
                '</p><p>Thanks for your business! Your purchase of Fax Robot '
                'Credit allows you to send faxes any '
                'time, without worrying about monthly subscription fees. We '
                'hope you enjoy using the service. If you have any questions '
                'or feedback, please email '
                '<a href="mailto:human@faxrobot.io">human@faxrobot.io</a>.</p>'
                '<p>You can log into your account at '
                '<a href="%s/accounts/login">%s/accounts/login</a>.') % (
                temporary_password, base_url, base_url)
        subject = 'Welcome to Fax Robot! Here\'s your receipt.'
    else:
        html = '<h2>Thanks for being a Fax Robot customer!</h2>'
        subject = 'Fax Robot payment receipt'

    html = html + ('<hr/>'
                 '<p><strong>Account:</strong> %s<br/>'
                 '<strong>Transaction ID:</strong> %s<br/>'
                 '<strong>Payment Date:</strong> %s<br/>'
                 '<strong>Payment Card:</strong> %s<br/>'
                 '<strong>Amount:</strong> $%.2f</p>'
                 '<p>This is your receipt of payment against your credit card. '
                 'Thanks!</p><p>For account information '
                 'and current balance, please visit '
                 '<a href="%s/account">%s/account</a>.</p>'
                 '<p>--Fax Robot</p>') % (account.email, transaction_id,
                 datetime.now().strftime('%B %d, %Y'), payment_last4, charged,
                 base_url, base_url)

    message = {
        'subject': subject,
        'html': html
    }
    send_email(message, account)

def email_recharge_payment(account, charged, transaction_id, payment_last4):

    from datetime import datetime

    message = {
        'subject': 'Fax Robot payment receipt',
        'html': ('<h2>Thanks for being a Fax Robot customer!</h2><p>Your '
                 'remaining account credit dropped to $0, so we recharged it '
                 'by $%.2f. You can manage your stored payment information and '
                 'auto-recharge preferences at '
                 '<a href="%s/account">%s/account</a>.</p><hr/>'
                 '<p><strong>Account:</strong> %s<br/>'
                 '<strong>Transaction ID:</strong> %s<br/>'
                 '<strong>Payment Date:</strong> %s<br/>'
                 '<strong>Payment Card:</strong> %s<br/>'
                 '<strong>Amount:</strong> $%.2f</p>'
                 '<p>This is your receipt of payment against your credit card. '
                 'Thanks!</p><p>For account information '
                 'and current balance, please visit '
                 '<a href="%s/account">%s/account</a>.</p>'
                 '<p>--Fax Robot</p>') % (charged, base_url, base_url,
                 account.email, transaction_id,
                 datetime.now().strftime('%B %d, %Y'), payment_last4, charged,
                 base_url, base_url)
    }
    send_email(message, account)

def email_fail(job, msg, code, status):

    from datetime import datetime

    account = job.account

    message = {
        'subject': 'Your fax could not be sent :(',
        'html': ('<p><strong><a href="%s/job/%s">Visit the fax details page to '
                 'retry.</a></strong></p><p>An error occurred while sending '
                 'your fax:</p>'
                 '<p><strong>Job ID:</strong> %s<br/>'
                 '<strong>Destination:</strong> %s<br/>'
                 '<strong>Error:</strong> %s (Code %s)<br/>'
                 '<strong>Date:</strong> %s<br/></p>'
                 '<p>If you\'re having trouble, please email '
                 '<a href="mailto:support@faxrobot.io">support@faxrobot.io</a> '
                 'and we\'ll do our best to help.</p><p>To change your email '
                 'notification preferences, visit '
                 '<a href="%s/account">%s/account</a>.</p><p>--Fax Robot</p>'
                 ) % (base_url, job.access_key, job.id, job.destination,
                 'Internal error' if status == 'internal_error' else msg,
                 code, datetime.now().strftime('%B %d, %Y'), base_url, base_url)
    }
    send_email(message, account)

def email_success(job):

    from datetime import datetime

    account = job.account

    message = {
        'subject': 'Your fax was sent!',
        'html': ('<p>Great news! Your fax to %s was sent.</p>'
                 '<p><strong><a href="%s/job/%s">Visit the fax details page '
                 'for more info.</a></strong></p><p>To change your email '
                 'notification preferences, visit '
                 '<a href="%s/account">%s/account</a>.</p><p>--Fax Robot</p>'
                 ) % (job.destination, base_url, job.access_key, base_url, 
                 base_url)
    }
    send_email(message, account)

def email_password_reset(email, password_reset, account):

    message = {
        'subject': 'Reset your Fax Robot password',
        'html': ('<p>To reset your Fax Robot password, click on the link '
                 'below:</p><p><a href="%s/reset/%s">%s/reset/%s</a></p><p>If '
                 'you weren\'t expecting this email, or weren\'t trying to '
                 'reset your password, please contact '
                 '<a href="mailto:support@faxrobot.io">support@faxrobot.io</a>'
                 '</p><p>--Fax Robot</p>'
                 ) % (base_url, password_reset.reset_hash, base_url, 
                 password_reset.reset_hash)
    }
    send_email(message, account)

def send_email(message, account = None):
    message['from_email'] = os.environ.get('EMAIL_FROM')
    message['from_name'] = os.environ.get('EMAIL_FROM_NAME')

    if account:
        if account.first_name and account.last_name:
            message['to'] = [{
                'email': account.email,
                'name': account.first_name + ' ' + account.last_name
            }]
        else:
            message['to'] = [{'email': account.email}]

    try:
        client.messages.send(message=message, async=True)
    except mandrill.Error, e:
        print 'A mandrill error occurred: %s - %s' % (e.__class__, e)