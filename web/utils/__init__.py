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


def validate_isbn(isbn):
    """ Return the isbn if it's valid, otherwise throws an error """
    length = len(isbn)
    if length == 10:
        # TODO validate the 10-digit ISBN
        return isbn
    elif length == 13:
        # TODO validate the 13-digit ISBN
        return isbn
    else:
        # TODO some data has such isbn: SH10019-1999, what is that?
        return isbn
#        raise ValueError("The provided ISBN (%s) is invalid." % isbn)


# used in get_jinja_env()
jinja_env = None

def get_jinja_env():
    """ Return shared jinja environment for rendering html templates. """
    global jinja_env
    if jinja_env is None:
        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.realpath("./static/html/")),
                               autoescape=True)
    return jinja_env
