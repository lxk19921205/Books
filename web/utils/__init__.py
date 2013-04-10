"""
@author: Andriy Lin
@description: Provide handful functions used in the whole project
@content:
    @function: random_string(), generate random strings
"""

import string
import random

def random_string(length=8):
    """ Generate random strings with the provided length. """
    src = string.letters
    return ''.join(random.choice(src) for _ in xrange(length))
