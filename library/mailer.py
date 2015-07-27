import os
from library.grab_bag import o

base_url = os.environ.get('FAXROBOT_URL')
email_support = os.environ.get('EMAIL_SUPPORT')
email_feedback = os.environ.get('EMAIL_FEEDBACK')
project = os.environ.get('PROJECT_NAME')

def email_registration(account):
    message = {
        'subject': 'Welcome to %s!' % project,
        'html': ('<p>Thanks for registering for %s! Your new account is '
                 'ready. To log in, visit <a href="%s/accounts/login">%s'
                 '/accounts/login</a>.</p><p>I\'ll send you emails with '
                 'important account-related updates, like a notification when '
                 'your faxes are sent (or they fail to send for some reason). '
                 'I respect your email address and won\'t send you junk email. '
                 'You can change your email notification preferences by '
                 'visiting <a href="%s/account">%s/account</a>.</p><p>I hope '
                 'you have as much fun using the service as I do '
                 'sending faxes on your behalf.</p><p>Thanks again,</p><p>%s'
                 '</p>') % (project, base_url, base_url, base_url, base_url,
                 project)
    }

    send_email(message, account)

def email_password_change(account):
    message = {
        'subject': '%s password changed' % project,
        'html': ('<p>Just a heads up: your %s password was changed.</p>'
                 '<p>If you weren\'t aware of this, please email '
                 '<a href="mailto:%s">%s</a> '
                 'as soon as possible.</p><p>--%s</p>') % (project,
                 email_support, email_support, project)
    }
    send_email(message, account)

def email_api_key_change(account):
    message = {
        'subject': '%s API key changed' % project,
        'html': ('<p>Just a heads up: your %s API key was changed.</p>'
                 '<p>If you weren\'t aware of this, please email '
                 '<a href="mailto:%s">%s</a> '
                 'as soon as possible.</p><p>--%s</p>') % (project,
                 email_support, email_support, project)
    }
    send_email(message, account)

def email_payment(account, charged, transaction_id, payment_last4,
        temporary_password = None):

    from datetime import datetime

    if temporary_password:
        html = ('<p><strong>Your temporary password is: <em>%s</em></strong>'
                '</p><p>Thanks for your business! Your purchase of %s '
                'Credit allows you to send faxes any '
                'time, without worrying about monthly subscription fees. We '
                'hope you enjoy using the service. If you have any questions '
                'or feedback, please email '
                '<a href="mailto:%s">%s</a>.</p>'
                '<p>You can log into your account at '
                '<a href="%s/accounts/login">%s/accounts/login</a>.') % (
                temporary_password, project, email_feedback, email_feedback,
                base_url, base_url)
        subject = 'Welcome to %s! Here\'s your receipt.' % project
    else:
        html = '<h2>Thanks for being a %s customer!</h2>' % project
        subject = '%s payment receipt' % project

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
                 '<p>--%s</p>') % (account.email, transaction_id,
                 datetime.now().strftime('%B %d, %Y'), payment_last4, charged,
                 base_url, base_url, project)

    message = {
        'subject': subject,
        'html': html
    }
    send_email(message, account)

def email_recharge_payment(account, charged, transaction_id, payment_last4):

    from datetime import datetime

    message = {
        'subject': '%s payment receipt' % project,
        'html': ('<h2>Thanks for being a %s customer!</h2><p>Your '
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
                 '<p>--%s</p>') % (project, charged, base_url, base_url,
                 account.email, transaction_id,
                 datetime.now().strftime('%B %d, %Y'), payment_last4, charged,
                 base_url, base_url, project)
    }
    send_email(message, account)

def email_fail(job, msg, code, status, debug_data=None):

    from datetime import datetime

    account = job.account

    body = ('<p><strong><a href="%s/job/%s">Visit the fax details page to '
             'retry.</a></strong></p><p>An error occurred while sending '
             'your fax:</p>'
             '<p><strong>Job ID:</strong> %s<br/>'
             '<strong>Destination:</strong> %s<br/>'
             '<strong>Error:</strong> %s (Code %s)<br/>'
             '<strong>Date:</strong> %s<br/>'
             ) % (base_url, job.access_key, job.id, job.destination,
             'Internal error' if status == 'internal_error' else msg,
             code, datetime.now().strftime('%B %d, %Y'))

    if job.account.debug_mode and debug_data:

        if debug_data["device"]:
            body += '<strong>Device:</strong> %s<br/>' % debug_data["device"]

        if debug_data["output"]:
            body += '<strong>Output:</strong> %s<br/>' % debug_data["output"]

    body +=('</p><p>If you\'re having trouble, please email '
             '<a href="mailto:%s">%s</a> '
             'and we\'ll do our best to help.</p><p>To change your email '
             'notification preferences, visit '
             '<a href="%s/account">%s/account</a>.</p><p>--%s</p>') % (
                email_support, email_support, base_url, base_url, project)

    message = {
        'subject': 'Your fax could not be sent :(',
        'html': body
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
                 '<a href="%s/account">%s/account</a>.</p><p>--%s</p>'
                 ) % (job.destination, base_url, job.access_key, base_url, 
                 base_url, project)
    }
    send_email(message, account)

def email_password_reset(email, password_reset, account):

    message = {
        'subject': 'Reset your %s password' % project,
        'html': ('<p>To reset your %s password, click on the link '
                 'below:</p><p><a href="%s/reset/%s">%s/reset/%s</a></p><p>If '
                 'you weren\'t expecting this email, or weren\'t trying to '
                 'reset your password, please contact '
                 '<a href="mailto:%s">%s</a>'
                 '</p><p>--%s</p>'
                 ) % (project, base_url, password_reset.reset_hash, base_url, 
                 password_reset.reset_hash, email_support, email_support,
                 project)
    }
    send_email(message, account)

def send_email(message, account = None):

    if not os.environ.get('MANDRILL_API_KEY'):
        return False

    import mandrill
    client = mandrill.Mandrill(os.environ.get('MANDRILL_API_KEY'))

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
        o('A mandrill error occurred: %s - %s' % (e.__class__, e))