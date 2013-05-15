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

import jinja2
from google.appengine.ext import db

import keys
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
    """ Return the isbn if it's valid, otherwise throws an error """
    try:
        result = isbn.validate(isbn_str)
        if not result:
            raise Exception()
    except Exception:
        # some data has such isbn: SH10019-1999, this may cause an exception, what is that?!
        raise ValueError("The provided ISBN (%s) is invalid." % isbn)
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
