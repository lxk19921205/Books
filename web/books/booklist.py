'''
@author: Xuankang
@description: Provide the definition and implementation of @class BookList
'''

from datetime import datetime
from google.appengine.ext import db

import utils

# the identifiers for 3 predefined lists
LIST_READING = "Reading"
LIST_INTERESTED = "Interested"
LIST_DONE = "Done"


class BookList(db.Model):
    '''
    A BookList is a collection of many Books.
    '''

    name = db.StringProperty(required=True)
    user = db.ReferenceProperty(required=True)
    note = db.TextProperty()
    # TODO tags may not be useful currently
    # tags = db.StringListProperty()

    # the isbn for each book
    isbns = db.StringListProperty()
    # the updated time for each book (when is it added into this booklist)
    times = db.ListProperty(item_type=datetime)

    douban_amount = db.IntegerProperty()


    @db.transactional
    def start_importing(self, amount):
        del self.isbns[:]
        del self.times[:]
        self.douban_amount = amount
        self.put()

    def is_importing(self):
        if self.douban_amount is None:
            return False
        return len(self.isbns) != self.douban_amount

    def importing_progress(self):
        if self.douban_amount is None:
            return None
        return len(self.isbns) / float(self.douban_amount) * 100

    @db.transactional
    def add_book(self, book, updated_time=None):
        """ If the book is already there, update the time.
            Otherwise, append it and the time.
        """
        if updated_time is None:
            updated_time = datetime.now()

        for idx in xrange(len(self.isbns)):
            if self.isbns[idx] == book.isbn:
                self.times[idx] = updated_time
                self.put()
                return

        # not in the list, append it
        self.isbns.append(book.isbn)
        self.times.append(updated_time)
        self.put()
        return

    @db.transactional
    def remove_book(self, book):
        """ Remove the book and its updated_time. """
        for idx in xrange(len(self.isbns)):
            if self.isbns[idx] == book.isbn:
                self.isbns.pop(idx)
                self.times.pop(idx)
                self.put()
                return
    # end of remove_book()

    def isbn_times(self):
        """ @return: A list of (isbn, updated_time) """
        return zip(self.isbns, self.times)

    @classmethod
    def get_by_user_name(cls, user, name):
        """ Query via User & BookList's name. """
        cursor = db.GqlQuery("select * from BookList where ancestor is :parent_key " +
                             "and user = :u and name = :n",
                             parent_key=utils.get_key_book(),
                             u=user,
                             n=name)
        return cursor.get()

    @classmethod
    def get_or_create(cls, user, name):
        """ Query via User & BookList's name.
            If it is not there, create one and save it into datastore.
        """
        bl = cls.get_by_user_name(user, name)
        if not bl:
            bl = BookList(name=name, user=user, parent=utils.get_key_book())
            bl.put()

        return bl
