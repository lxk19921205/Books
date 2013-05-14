'''
@author: Xuankang
@description: Provide the definition and implementation of @class BookList
'''

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
    isbns = db.StringListProperty()
    note = db.TextProperty()
    # TODO tags may not be useful currently
    # tags = db.StringListProperty()

    douban_amount = db.IntegerProperty()


    @db.transactional
    def start_importing(self, amount):
        del self.isbns[:]
        self.douban_amount = amount
        self.put()

    def is_importing(self):
        return len(self.isbns) == self.douban_amount

    @db.transactional
    def add_book(self, book):
        if book.isbn in self.isbns:
            return False
        else:
            self.isbns.append(book.isbn)
            self.put()
            return True

    @db.transactional
    def remove_book(self, book):
        if book.isbn in self.isbns:
            self.isbns.remove(book.isbn)
            self.put()
        return True

    @db.transactional
    def remove_all(self):
        del self.isbns[:]
        self.put()
        return True

    @db.transactional
    def set_name(self, name):
        if name:
            self.name = name
            self.put()
            return True
        else:
            return False

    @db.transactional
    def set_note(self, note):
        if note:
            self.note = note
            self.put()
            return True
        else:
            return False

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

    @classmethod
    def init_predefined_lists(cls, user):
        """ After signing up, user need to have predefined lists already. """
        cls.get_or_create(user, LIST_READING)
        cls.get_or_create(user, LIST_INTERESTED)
        cls.get_or_create(user, LIST_DONE)
