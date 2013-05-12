'''
@author: Xuankang
@description: Provide the definition and implementation of @class BookList
'''

from google.appengine.ext import db


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
    isbns = db.StringListProperty(required=True)
    note = db.TextProperty()
    # TODO tags may not be useful currently
    # tags = db.StringListProperty()

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
