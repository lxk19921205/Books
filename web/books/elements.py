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
    isbn = db.StringProperty(required=True, indexed=True)


class Rating(_UserBookElement):
    """ User's rating to a book. """
    score = db.IntegerProperty()
    max_score = db.IntegerProperty()
    min_score = db.IntegerProperty()

    @db.transactional
    def update_to(self, another):
        """ Completely update to another Rating. """
        self.score = another.score
        self.max_score = another.max_score
        self.min_score = another.min_score
        self.put()

    @classmethod
    def get_by_user_isbn(cls, user, isbn):
        """ Query via User & ISBN """
        cursor = db.GqlQuery("SELECT * FROM Rating WHERE ANCESTOR IS :parent_key" +
                             " AND user = :u AND isbn = :i LIMIT 1",
                             parent_key=utils.get_key_book(),
                             u=user,
                             i=isbn)
        return cursor.get()


class Tags(_UserBookElement):
    """ User's tags attached to a book. """
    names = db.StringListProperty()

    @db.transactional
    def update_to(self, another):
        """ Completely update to another Tags. """
        self.names = another.names
        self.put()

    @classmethod
    def get_by_user_isbn(cls, user, isbn):
        """ Query via User & ISBN """
        cursor = db.GqlQuery("SELECT * FROM Tags WHERE ANCESTOR IS :parent_key" +
                             " AND user = :u AND isbn = :i LIMIT 1",
                             parent_key=utils.get_key_book(),
                             u=user,
                             i=isbn)
        return cursor.get()

    @classmethod
    def get_by_isbns(cls, user, isbns):
        """ Query a list of tags by a list of isbns.
            @param isbns: a list of isbns. If there are more than 30 items in it,
                          it will use the first 30 ones.
            @returns: an iterable object returned by datastore.
        """
        # at most 30 fetches at one time in datastore
        isbns = isbns[:30]
        cursor = db.GqlQuery("SELECT names FROM Tags WHERE ANCESTOR IS :parent_key" +
                             " AND user = :u AND isbn IN :lt",
                             parent_key=utils.get_key_book(),
                             u=user,
                             lt=isbns)
        return cursor.run()


class Comment(_UserBookElement):
    """ User's comments on a book. """
    comment = db.TextProperty()

    @db.transactional
    def update_to(self, another):
        """ Completely update to another Comment. """
        self.comment = another.comment
        self.put()

    @classmethod
    def get_by_user_isbn(cls, user, isbn):
        """ Query via User & ISBN """
        cursor = db.GqlQuery("SELECT * FROM Comment WHERE ANCESTOR IS :parent_key" +
                             " AND user = :u AND isbn = :i LIMIT 1",
                             parent_key=utils.get_key_book(),
                             u=user,
                             i=isbn)
        return cursor.get()
