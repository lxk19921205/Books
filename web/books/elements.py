'''
@author: Andriy Lin
@description:
    Provide elements attached to a specific book and a specific user, such as Review, Rating, Tags, etc.
'''

from google.appengine.ext import db


class _UserBookElement(db.Model):
    """ The base class for those related to a specific user and a specific book. """
    user = db.ReferenceProperty(required=True)
    isbn = db.StringProperty(required=True)


class Rating(_UserBookElement):
    """ User's rating to a book. """
    score = db.IntegerProperty()
    max_score = db.IntegerProperty()
    min_score = db.IntegerProperty()


class Tags(_UserBookElement):
    """ User's tags attached to a book. """
    names = db.StringListProperty()


class Comment(_UserBookElement):
    """ User's comments on a book. """
    comment = db.TextProperty()
