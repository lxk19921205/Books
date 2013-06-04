# coding=utf-8
"""
@author: Andriy Lin
@description: Provide handful functions used in the whole project
@content:
    @function: random_string(), generate random strings
@attention:
    keys.py will not be added to git. In other words, it will remain private for safety purpose
"""

import os
import string
import random
import re

import jinja2
from google.appengine.ext import db

import isbn


def random_string(length=8):
    """ Generate random strings with the provided length. """
    src = string.letters
    return ''.join(random.choice(src) for _ in xrange(length))


def random_book_id():
    """ Randomly generate a book id (str) to fetch information from Douban. """
    src = '0123456789'
    nonzero_src = '123456789'
    return random.choice(nonzero_src) + ''.join(random.choice(src) for _ in xrange(6))


def validate_isbn(isbn_str):
    """ Return the isbn if it's valid, otherwise throws an error.
        Some old data are 全国统一书号, such as SH10019-1999, SH2017-279, SH10019-1198, SH11018-1034
        They are also valid
    """
    def validate_sh():
        match = re.search(r"SH\d+-\d+", isbn_str)
        return match

    try:
        result = isbn.validate(isbn_str)
        if not result:
            raise Exception()
    except Exception:
        # check again for the SH___-__
        if not validate_sh():
            raise ValueError("The provided ISBN (%s) is invalid." % isbn_str)
# end of validate_isbn()


# used in get_jinja_env()
jinja_env = None


def get_jinja_env():
    """ Return shared jinja environment for rendering html templates. """
    global jinja_env
    if jinja_env is None:
        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.realpath("./static/html/")),
                                       autoescape=True)
    return jinja_env


# the saved keys
PUBLIC_KEY_DICT = {}
PRIVATE_KEY_DICT = {}


def get_key_public(cls_name):
    """ Get the key used in public information such as Book.
        GAE guarantees "final consistency", but it may take seconds, using parent=key... could resolve this.
        @param cls_name: used in which class.
    """
    if cls_name not in PUBLIC_KEY_DICT:
        # there must be even number of params (non-empty)..
#        k = db.Key.from_path('AndriyBooks', 'public_info', 'cls_name', cls_name)
#        k = db.Key.from_path('AndriyBooks', cls_name)
#        PUBLIC_KEY_DICT[cls_name] = str(db.Key.from_path('AndriyBooks', 'public_info', 'cls_name', cls_name))
        PUBLIC_KEY_DICT[cls_name] = db.Key.from_path('AndriyBooks', 'public_info')
        # TODO: remove this line

    return PUBLIC_KEY_DICT[cls_name]


def get_key_private(cls_name, user_key):
    """ Get the key used in public information such as Book.
        GAE guarantees "final consistency", but it may take seconds, using parent=key... could resolve this.
        @param cls_name: used in which class.
        @param user_key: the user's key in datastore.
    """
    return db.Key.from_path('AndriyBooks', 'private_info', cls_name, user_key)
