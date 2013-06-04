'''
@author: Xuankang
@description: Provide the definition and implementation of @class BookList
'''

import time
from datetime import datetime
from google.appengine.ext import db

import utils

# the identifiers for 3 predefined lists
LIST_READING = "Reading"
LIST_INTERESTED = "Interested"
LIST_DONE = "Done"
# a collection for traversal
LIST_NAMES = [
    LIST_READING,
    LIST_INTERESTED,
    LIST_DONE
]


class BookList(db.Model):
    '''
    A BookList is a collection of many Books.
    '''

    name = db.StringProperty(required=True)
    user = db.ReferenceProperty(required=True)
    note = db.TextProperty()

    DELIMITER = ','

    # each item is in format: isbn,updated_time
    # updated time is the time when it is added into this booklist
    isbn_times = db.StringListProperty()

    douban_amount = db.IntegerProperty()

    def _to_seconds(self, t):
        """ Convert a datetime object to a float.
            @param t: the datetime object to parse.
            @returns: a string of seconds
        """
        return str(time.mktime(t.timetuple()))

    def _to_datetime(self, t):
        """ Convert a float to a datetime object.
            @param t: how many seconds it has passed since the epoch.
            @returns: a datetime object
        """
        return datetime.fromtimestamp(float(t))

    def size(self):
        """ @returns: how many books are there in this booklist. """
        return len(self.isbn_times)

    @db.transactional
    def start_importing(self, amount):
        del self.isbn_times[:]
        self.douban_amount = amount
        self.put()
        return

    @db.transactional
    def remove_all(self):
        del self.isbn_times[:]
        self.put()
        return

    @db.transactional
    def finish_importing(self):
        self.douban_amount = None
        self.put()
        return

    def is_importing(self):
        if self.douban_amount is None:
            return False
        return len(self.isbn_times) < self.douban_amount

    def importing_progress(self):
        """ @returns: a number that represents how many percent has finished. """
        if self.douban_amount is None:
            return None
        return len(self.isbn_times) / float(self.douban_amount) * 100

    @db.transactional
    def add_isbn(self, isbn, updated_time=None, front=False):
        """ If the book is already there, update the time.
            Otherwise, append it and the time.
        """
        if updated_time is None:
            updated_time = datetime.now()

        for idx in xrange(len(self.isbn_times)):
            prev_isbn = self.isbn_times[idx].split(self.DELIMITER)[0]
            if prev_isbn == isbn:
                time = self._to_seconds(updated_time)
                self.isbn_times[idx] = prev_isbn + self.DELIMITER + time
                self.put()
                return

        # not in the list, append it or insert it
        output = isbn + self.DELIMITER + self._to_seconds(updated_time)
        if front:
            self.isbn_times.insert(0, output)
        else:
            self.isbn_times.append(output)
        self.put()
        return

    @db.transactional
    def remove_isbn(self, isbn):
        """ Remove the book of the isbn and its updated_time. """
        for idx in xrange(len(self.isbn_times)):
            prev_isbn = self.isbn_times[idx].split(self.DELIMITER)[0]
            if prev_isbn == isbn:
                self.isbn_times.pop(idx)
                self.put()
                return
    # end of remove_isbn()

    def isbns(self):
        """ @returns: a list of isbn. """
        def _helper(src, delim):
            return src.split(delim)[0]

        return [_helper(src, self.DELIMITER) for src in self.isbn_times]

    def isbns_after(self, t):
        """ @returns: a list of isbns which was added after @param t.
            @param t: a datetime object to compare with.
        """
        results = []
        for src in self.isbn_times:
            [isbn, updated] = src.split(self.DELIMITER)
            updated_time = self._to_datetime(updated)
            if updated_time >= t:
                results.append(isbn)

        return results

    def isbn_times_pair(self):
        """ @returns: A list of (isbn, updated_time) """
        def _helper(src):
            [one, two] = src.split(self.DELIMITER)
            return (one, self._to_datetime(two))

        return [_helper(src) for src in self.isbn_times]

    def get_updated_time(self, isbn):
        """ @return: a datetime object representing the isbn's book's updated time if it is in this list, otherwise None. """
        for idx in xrange(len(self.isbn_times)):
            [prev_isbn, time] = self.isbn_times[idx].split(self.DELIMITER)
            if prev_isbn == isbn:
                return self._to_datetime(time)

        return None

    @classmethod
    def get_by_user_name(cls, user, name):
        """ Query via User & BookList's name. """
        cursor = db.GqlQuery("SELECT * FROM BookList WHERE ANCESTOR IS :parent_key " +
                             "AND user = :u AND name = :n LIMIT 1",
                             parent_key=utils.get_key_private('BookList', user),
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
            bl = BookList(name=name, user=user, parent=utils.get_key_private('BookList', user))
            bl.put()

        return bl

    @classmethod
    def get_all_booklists(cls, user):
        """ Query all booklists of a user. """
        cursor = db.GqlQuery("SELECT * FROM BookList WHERE ANCESTOR IS :parent_key " +
                             "AND user = :u",
                             parent_key=utils.get_key_private('BookList', user),
                             u=user)
        # since there are at most 3 lists now
        return cursor.run(limit=len(LIST_NAMES))

    @classmethod
    def find(cls, user, isbn):
        """ @returns: the name of booklist in which there is @param isbn.
            @returns None when not found.
        """
        bls = cls.get_all_booklists(user)
        for bl in bls:
            for src in bl.isbn_times:
                prev_isbn = src.split(cls.DELIMITER)[0]
                if prev_isbn == isbn:
                    return bl.name
        return None
