import sys

def fix_ip(ip_address):
    """Fixes an ugly, broken IP address string that came from Heroku"""

    if "," in ip_address:
        ips = ip_address.split(", ")
        ip_address = ips[0]

    return ip_address

def random_hash(entropy):

    import time, hashlib, os
    _str = "%s%s%s" % (entropy, time.time()*1000, os.environ.get('GLOBAL_SALT'))
    return hashlib.sha256(_str).hexdigest()

def password_hash(password):

    import hashlib, os
    _str = "%s%s" % (password, os.environ.get('GLOBAL_SALT'))
    return hashlib.sha256(_str).hexdigest()

def o(output):
    print >> sys.stderr, output