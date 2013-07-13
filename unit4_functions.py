# udacity
# unit 4 functions

import random
import string
import hashlib
import hmac
import re

def valid_username(username):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return USER_RE.match(username)

def valid_password(password):
    PASSWORD_RE = re.compile(r"^.{3,20}$")
    return PASSWORD_RE.match(password)

def valid_verify(password, verify):
    if password == verify:
        return True
    else:
        return None

def valid_email(email):
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
    return EMAIL_RE.match(email)

def hmac_hash_str(s, secret): 
    return hmac.new(secret, s).hexdigest()

def make_secure_val(val, secret):
    return '%s|%s' % (val, hmac_hash_str(val, secret))    

def check_secure_val(h, secret):
    #h is a string of the format "str|hashedstr"
    split = h.split("|")
    s = split[0]
    HASH = split[1]
    if hmac_hash_str(s, secret) == HASH:
        return s
    else:
        return None

def make_salt(length=5):
    letters = string.ascii_letters
    salt = '' 
    for i in range(length):
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
