import hashlib
import hmac

def valid_signature(token, url, parameters, files, signature):
    # sort the post fields and add them to the URL
    for key in sorted(parameters.keys()):
        url += '{}{}'.format(key, parameters[key])

    # sort the files and add their SHA1 sums to the URL
    for filename in sorted(files.keys()):
        file_hash = hashlib.sha1()
        file_hash.update(files[filename].read())
        url += '{}{}'.format(filename, file_hash.hexdigest())

    return signature == hmac.new(key=token.encode('utf-8'), msg=url.encode('utf-8'), digestmod=hashlib.sha1).hexdigest()

