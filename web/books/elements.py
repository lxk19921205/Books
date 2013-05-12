'''
@author: Andriy Lin
@description:
    Provide elements attached to a specific book and a specific user, such as Review, Rating, Tags, etc.
'''

from google.appengine.ext import db
import utils


class _UserBookElement(db.Model):
    """ The base class for those related to a specific user and a specific book. """
    user = db.ReferenceProperty(required=True)
    isbn = db.StringProperty(required=True)


class Rating(_UserBookElement):
    """ User's rating to a book. """
    score = db.IntegerProperty()
    max_score = db.IntegerProperty()
    min_score = db.IntegerProperty()

    def update_to(self, another):
        """ Completely update to another Rating. """
        self.score = another.score
        self.max_score = another.max_score
        self.min_score = another.min_score

    @classmethod
    def get_by_user_isbn(cls, user, isbn):
        """ Query via User & ISBN """
        cursor = db.GqlQuery("select * from Rating where ancestor is :parent_key" + 
                             " and user = :u and isbn = :i",
                             parent_key=utils.get_key_book(),
                             u=user,
                             i=isbn)
        return cursor.get()


class Tags(_UserBookElement):
    """ User's tags attached to a book. """
    names = db.StringListProperty()

    def update_to(self, another):
        """ Completely update to another Tags. """
        self.names = another.names

    @classmethod
    def get_by_user_isbn(cls, user, isbn):
        """ Query via User & ISBN """
        cursor = db.GqlQuery("select * from Tags where ancestor is :parent_key" + 
                             " and user = :u and isbn = :i",
                             parent_key=utils.get_key_book(),
                             u=user,
                             i=isbn)
        return cursor.get()


class Comment(_UserBookElement):
    """ User's comments on a book. """
    comment = db.TextProperty()

    def update_to(self, another):
        """ Completely update to another Comment. """
        self.comment = another.comment

    @classmethod
    def get_by_user_isbn(cls, user, isbn):
        """ Query via User & ISBN """
        cursor = db.GqlQuery("select * from Comment where ancestor is :parent_key" + 
                             " and user = :u and isbn = :i",
                             parent_key=utils.get_key_book(),
                             u=user,
                             i=isbn)
        return cursor.get()
