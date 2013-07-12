# udacity
# unit 4 functions

import random
import string
import hashlib
import hmac

def check_secure_val(h):
    #h is a string of the format "str|hashedstr"
    split = h.split("|")
    s = split[0]
    HASH = split[1]
    if hash_str(s) == HASH:
        return s
    else:
        return None

def make_salt():
    letters = string.ascii_letters
    salt = '' 
    for i in range(5):
        salt += random.choice(letters)
    return salt

def make_pw_hash(name, pw, salt=None):
    #Returns a string of the format "sha246 str of name+pw+salt | saltstr"
    if not salt:
        salt = make_salt()
    return "%s|%s" % (hashlib.sha256(name+pw+salt).hexdigest(), salt)

def valid_pw(name, pw, h):
    salt = h.split('|')[1]
    if h == make_pw_hash(name, pw, salt):
        return True
    else:
        return None