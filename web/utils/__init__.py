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
import keys


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


# GAE guarantees "final consistency", but it may take seconds, using parent=key... may resolve this.
key_auth_related = None
key_book_related = None


def get_key_auth():
    """ Get the key used in objects used in authentication. """
    global key_auth_related
    if key_auth_related is None:
        key_auth_related = db.Key.from_path('AndriyBooks', 'auth_related')

    return key_auth_related


def get_key_book():
    """ Get the key used in objects corresponding to books. """
    global key_book_related
    if key_book_related is None:
        key_book_related = db.Key.from_path('AndriyBooks', 'book_related')

    return key_book_related
