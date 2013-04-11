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

def random_string(length=8):
    """ Generate random strings with the provided length. """
    src = string.letters
    return ''.join(random.choice(src) for _ in xrange(length))
