'''
@author: Andriy Lin
@description: Handling the requests for task queue.
'''

import webapp2
import logging
from google.appengine.ext import db
from google.appengine.api import memcache

import utils
from auth.user import User
from api import douban
from api import tongji
from books import SortHelper
from books.book import Book
from books.booklist import BookList


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


class ImportWorker(webapp2.RequestHandler):
    """ Doing importing from douban. """

    def _log(self, msg):
        client = memcache.Client()
        key = "logs"
        while True:
            logs = client.gets(key)
            if logs is None:
                if client.add(key, [msg]):
                    break
            else:
                logs.append(msg)
                if client.cas(key, logs):
                    break
        return

    def post(self):
        self._log("in post method")
        user_key = self.request.get('user_key')
        list_type = self.request.get('type')
        if not user_key or not list_type:
            self._log("param not enough: " + user_key + " || " + list_type)
            return

        self._log("OK, params done.")
        user = User.get(user_key)
        try:
            all_book_related = douban.get_book_list(user, list_type)
        except utils.errors.ParseJsonError as err:
            logging.error("ERROR while importing from Douban, user_key: " + user_key +
                          " list_type: " + list_type)
            logging.error(err)

            self._log(err)
            return

        helper = SortHelper(user)
        bl = BookList.get_or_create(user, list_type)
        bl.start_importing(len(all_book_related))
        # also clear those in memcache
        helper.clear(list_type)

        for related in all_book_related:
            # also added into memcache in merge_into_datastore()
            b = related.merge_into_datastore(user, update_book=False)
            if b:
                # when already such book there, b will be None
                url, datas = tongji.get_by_isbn(b.isbn)
                b.set_tongji_info(url, datas)

        # has to re-get this instance, for it is retrieved inside merge_into_datastore()
        # the current instance may not be up-to-date
        bl = BookList.get_or_create(user, list_type)
        bl.finish_importing()
        return
