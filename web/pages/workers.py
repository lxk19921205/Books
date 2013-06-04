'''
@author: Andriy Lin
@description: Handling the requests for task queue.
'''

import webapp2
import logging
import json
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import taskqueue

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

        cursor = db.GqlQuery("SELECT * FROM " + cls)
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
    """ Refresh public book information from douban. """

    def post(self):
        isbn = self.request.get('isbn')
        if not isbn:
            return

        try:
            b = douban.get_book_by_isbn(isbn)
        except Exception:
            return

        if not b:
            return

        b_db = Book.get_by_isbn(isbn)
        if b_db:
            b_db.update_to(b)
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

    def _fetch(self, user):
        """ Fetch book data from douban.
            When done, add tasks to parse them and save into datastore.
        """
        list_type = self.request.get('list_type')
        if not list_type:
            return

        try:
            raw_datas = douban.get_book_list_raw(user, list_type)
        except utils.errors.ParseJsonError as err:
            logging.error("ERROR while importing from Douban, user_key: " + user.key() +
                          " list_type: " + list_type)
            logging.error(err)
            self._log(err)
            return

        bl = BookList.get_or_create(user, list_type)
        bl.start_importing(len(raw_datas))
        # also clear those in memcache
        helper = SortHelper(user)
        helper.clear(list_type)

        for raw in raw_datas:
            # for each json object, dumps it and new a task
            params = {
                'user_key': user.key(),
                'action': 'parse',
                'list_type': list_type,
                'data': json.dumps(raw)
            }
            t = taskqueue.Task(url='/workers/import', params=params)
            t.add(queue_name="douban")
        return

    def _parse(self, user):
        """ Parsing and saving the data fetched. """
        data = self.request.get('data')
        list_type = self.request.get('list_type')
        if not data or not list_type:
            return

        obj = json.loads(data)
        related = douban.parse_book_related_info(obj, user)

        # also added into memcache in merge_into_datastore()
        b = related.merge_into_datastore(user, update_book=False)
        if b:
            # when already such book there, b will be None
            url, datas = tongji.get_by_isbn(b.isbn)
            b.set_tongji_info(url, datas)

        # check if has finished importing
        bl = BookList.get_or_create(user, list_type)
        if len(bl.isbn_times) >= bl.douban_amount:
            bl.douban_amount = None
            bl.put()
        return

    def post(self):
        user_key = self.request.get('user_key')
        if not user_key:
            return
        user = User.get(user_key)

        action = self.request.get('action')
        if action == 'fetch':
            # load from douban
            # however, this won't be called now, since the fetching is done outside task queue
            self._fetch(user)
        elif action == 'parse':
            # parse and save into datastore
            self._parse(user)
        return
