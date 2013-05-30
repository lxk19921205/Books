'''
@author: Andriy Lin
@description: Handling the requests for task queue.
'''

import webapp2
from google.appengine.ext import db

import utils


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
        pass
