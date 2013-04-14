"""
@author: Andriy Lin
@description: Provide handful functions used in the whole project
@content:
    @function: random_string(), generate random strings
@attention:
    keys.py will not be added to git. In other words, it will remain private for safety purpose
"""

import string
import random

import keys

def random_string(length=8):
    """ Generate random strings with the provided length. """
    src = string.letters
    return ''.join(random.choice(src) for _ in xrange(length))

def random_book_id():
    """ Randomly generate a book id (str) to fetch information from Douban. """
    src = '0123456789'
    return ''.join(random.choice(src) for _ in xrange(7))


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
        raise ValueError("The provided ISBN is invalid.")
