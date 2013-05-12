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

    books = db.StringListProperty(required=True)
    # TODO some more attributes?
