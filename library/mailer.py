import os
from library.grab_bag import o

base_url = os.environ.get('FAXROBOT_URL')
email_support = os.environ.get('EMAIL_SUPPORT')
email_feedback = os.environ.get('EMAIL_FEEDBACK')
project = os.environ.get('PROJECT_NAME')
email_headers = {
    "Authorization": os.environ.get('SPARKPOST_API_KEY'),
    "Content-Type": "application/json"
}

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

def email_pending_deletion_warning(account, reason, fax_number):

    msg = '<p>Hello!</p>'

    if reason == "NO_FUNDS":
        msg += ("<p>Your %s account does not have sufficient funds for this "
                "month's incoming fax service, and automatic payments are "
                "disabled for your account.</p>") % project
    else:
        msg += ("<p>Your credit card was declined and your %s account has "
                "insufficient remaining funds for this month's incoming "
                "fax service.</p>") % project

    msg += ("<p>Please update your payment information in your "
            "<a href=\"%s/account\"><strong>Account Settings</strong></a> as "
            "soon as possible. If we are still unable to charge your account "
            "after 7 days, your fax number will automatically be suspended."
            "</p><p>Need assistance? Please reply to this email or contact "
            "<a href=\"mailto:%s\">%s</a>.</p><p>Thanks!</p><p>--%s</p>") % (
            base_url, email_support, email_support, project)

    message = {
        'subject': 'Payment overdue for your incoming fax number',
        'html': msg
    }
    send_email(message, account)

def email_deleted_number(account):
    message = {
        'subject': 'Your fax number was suspended :(',
        'html': ('<p>Your monthly payment for incoming fax service could '
                 'not be processed, and so the service was automatically '
                 'suspended. For more information, please contact '
                 '<a href="mailto:%s">%s</a> '
                 'as soon as possible.</p><p>--%s</p>') % (
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

def email_provision_info(account, fax_number):
    message = {
        'subject': 'Your fax number is activated!',
        'html': ('<h2>Congratulations! You can now receive faxes at %s.</h2>'
                 '<p>Your %s account will be charged $6 per month to '
                 'keep your number active. You can manage your subscription by '
                 'visiting your <a href="%s/account"><strong>Account Settings'
                 '</strong></a> page.</p><p>Happy faxing!</p><p>--%s</p>') % (
                 fax_number, project, base_url, project)
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

def email_receive_fail(account,reason,external_id,from_number,num_pages,cost):

    html = ("<p>%s was unable to deliver an incoming fax from <strong>%s"
            "</strong> due to insufficient funds in your account.</p>") % (
            project, from_number)
    
    if reason == "NO_FUNDS":
        html += ("<p>Please visit your <strong><a href=\"%s/account\">Account "
                 "Settings</a></strong> page to add funds, and consider turning"
                 " on the automatic charging feature. ") % base_url
    else:
        html += ("<p>Your credit card was declined. Please visit "
                 "your <strong><a href=\"%s/account\">Account Settings</a>"
                 "</strong> page to update your credit card info.") % base_url

    html += ("</p><p>Once your account is funded, please reply to this email "
             "and we can deliver your fax.</p>")

    html += ("<hr/>"
             "<p><strong>Reference #:</strong> %s<br/>"
             "<strong>From:</strong> %s<br/>"
             "<strong>Pages:</strong> %s<br/>"
             "<strong>Cost:</strong> $%.2f</p>") % (external_id, from_number,
             num_pages, cost)

    message = {
        "subject": "Unable to receive fax :(",
        "html": html
    }
    send_email(message, account)

def email_fax(account, external_id, from_number, num_pages, cost,
        filename, access_key):

    html = ("<h1>You've received a fax from %s</h1><p>Your fax is attached. "
            "You can also download or delete it from "
            "<a href=\"%s/jobs/received\"><strong>%s</strong></a>.</p>") % (
            from_number, base_url, project)

    html += ("<hr/>"
             "<p><strong>Reference #:</strong> %s<br/>"
             "<strong>From:</strong> %s<br/>"
             "<strong>Pages:</strong> %s<br/>"
             "<strong>Cost:</strong> $%.2f</p><hr/><p>"
             "<strong>Remaining Account Balance:</strong> $%.2f</p>") % (
             external_id, from_number, num_pages, cost, account.credit)

    message = {
        "subject": "Received fax from %s" % from_number,
        "html": html
    }
    send_email(message, account, "%s.pdf" % external_id, filename,
        "application/pdf")

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
            output = "<br />".join(debug_data["output"].split("\n"))
            body += '<strong>Output:</strong> %s<br/>' % output

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

def send_email(message, account = None, attach_name=None, attach_file=None,
    attach_mime=None):

    if not os.environ.get('SPARKPOST_API_KEY'):
        return False

    import requests
    import base64

    url = 'https://api.sparkpost.com/api/v1/transmissions'

    payload = {}

    payload['content'] = message
    payload['content']['from'] = {
        "name": os.environ.get('EMAIL_FROM_NAME'),
        "email": os.environ.get('EMAIL_FROM')
    }
    
    if account:
        if account.first_name and account.last_name:
            payload['recipients'] = [{
                'address': {
                    'email': account.email,
                    'name': account.first_name + ' ' + account.last_name
                }
            }]
        else:
            payload['recipients'] = [{'address': account.email}]

    if attach_name and attach_file and attach_mime:

        with open(attach_file) as f:
            attach_data = base64.b64encode(f.read())

        payload['content']['attachments'] = [
            {
                "type": attach_mime,
                "name": attach_name,
                "data": attach_data
            }
        ]

    try:
        response = requests.post(url, headers=email_headers, json=payload)
    except:
        o('SparkPost API Fail: %s' % response.text)

def email_admin(message, subject = None):

    if not os.environ.get('SPARKPOST_API_KEY'):
        return False

    import requests

    url = 'https://api.sparkpost.com/api/v1/transmissions'

    payload = {
        "content": {
            "subject": subject if subject else "%s CRITICAL ERROR" % project,
            "html": message,
            "from": {
                "name": os.environ.get('EMAIL_FROM_NAME'),
                "email": os.environ.get('EMAIL_FROM')
            }
        },
        "recipients": [{'address': os.environ.get('EMAIL_FROM')}]
    }

    try:
        response = requests.post(url, headers=email_headers, json=payload)
    except:
        o('SparkPost API Fail: %s' % response.text)




