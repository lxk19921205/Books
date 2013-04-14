'''
@author: Xuankang
@description: Provide the definition and implementation of @class BookList
'''

from google.appengine.ext import db


class BookList(db.Model):
    '''
    A BookList is a collection of many Books.
    '''

    books = db.StringListProperty(required=True)
    # TODO some more attributes?