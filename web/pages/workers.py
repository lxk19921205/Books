'''
@author: Andriy Lin
@description: Handling the requests for task queue.
'''

import webapp2
from google.appengine.ext import db

import utils
from api import tongji
from books.book import Book


class ClearWorker(webapp2.RequestHandler):
    """ Clearing all the datastore.
        Only used in testing.
    """

    def post(self):
        cls = self.request.get('cls')
        if not cls:
            return

        cursor = db.GqlQuery("SELECT * FROM " + cls + " WHERE ANCESTOR IS :parent_key ",
                             parent_key=utils.get_key_book())
        while True:
            next = cursor.get()
            if not next:
                break
            next.delete()
        return


class TongjiWorker(webapp2.RequestHandler):
    """ Handling refreshing a book in Tongji Library. """

    def post(self):
        isbn = self.request.get('isbn')
        if not isbn:
            return

        url, datas = tongji.get_by_isbn(isbn)
        b = Book.get_by_isbn(isbn)
        if b:
            b.set_tongji_info(url, datas)
        return


class DoubanWorker(webapp2.RequestHandler):
    """ Doing importing from douban. """

    def post(self):
        pass
