'''
@author: Xuankang
@description: Provide the definition and implementation of @class Book
'''

from google.appengine.ext import db


class Book(db.Model):
    '''
    the Book class contains everything related to the book. It will be saved in datastore.
    '''
    
    # use ISBN as the unique identifier
    isbn = db.StringProperty(required=True)
    title = db.StringProperty(required=True)
    # TODO much more attributes are to be added

    def validateISBN(self):
        """ Check whether the self.isbn is valid. """
        length = len(self.isbn)
        if length == 10:
            # TODO validate the 10-digit ISBN
            return True
        elif length == 13:
            # TODO validate the 13-digit ISBN
            return True
        else:
            return False

    @classmethod
    def parseJson(cls, j):
        """ Construct a Book according to the provided json object. """
        # TODO
        return
