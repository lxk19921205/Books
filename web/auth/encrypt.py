'''
@author: Xuankang
@description: Provide handful functions used in package auth
@content:
    @function encode(), encode src string with its hashed value
'''

import hmac
import utils

from hashlib import sha256


# randomly generated string, used in hmac
# TODO in production, save this string to some private places
_SECRET = "JTxiuUkVrEKJQHZY"


def encode(src, delim='|'):
    """ Encode source string with its hashed value.
    Format: SRC and HASHED separated by DELIM.
    """
    return src + delim + hmac.new(_SECRET, src, sha256).hexdigest()

def check_encoded(src, encoded, delim='|'):
    """ Decode the encoded string and check whether it is made by encode(). """
    tmp = encode(src, delim)
    return tmp == encoded


def hash_pwd(email, pwd, salt=None):
    """ Hash the raw password.
    So that the hashed string can be saved into datastore as pwd instead.
    Since the encrypted string won't contain ',', use comma as delimiter
    """
    if salt is None:
        salt = utils.random_string()
    
    hashed = hmac.new(_SECRET, email + pwd + salt, sha256).hexdigest()
    return hashed + ',' + salt

def check_pwd(email, pwd, hashed):
    """ Check whether the provided email & pwd match those saved in datastore. """
    salt = hashed.split(',')[1]
    return hash_pwd(email, pwd, salt) == hashed
