'''
@author: Andriy Lin
@description: Handlers for manipulating book lists
'''

import webapp2
import urllib
import logging
import json
from google.appengine.api import taskqueue

import utils
import auth
from api import douban
from api import tongji
import books
from books import booklist
from books import SortHelper
from books.booklist import BookList


def _import_worker(user_key, list_type):
    """ Called in Task Queue, for importing from douban.
        Since there may be lots of information to import, it may take some time.
        Doing this in Task Queue is more proper.
        @param user_key: DO NOT pass the user, otherwise it would raise exceptions (due to cache??)
        @param list_type: for subclasses to reuse
    """
    user = auth.user.User.get(user_key)
    try:
        all_book_related = douban.get_book_list(user, list_type)
    except utils.errors.ParseJsonError as err:
        logging.error("ERROR while importing from Douban, user_key: " + user_key +
                      " list_type: " + list_type)
        logging.error(err)
    else:
        helper = books.SortHelper(user)
        bl = booklist.BookList.get_or_create(user, list_type)
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
        bl = booklist.BookList.get_or_create(user, list_type)
        bl.finish_importing()
# end of _import_worker()


def _refresh_tj_worker(user_key, list_type):
    """ Called in Task Queue to refresh all the status of the books in a list.
        @param user_key: DO NOT pass the user, otherwise it would raise exceptions (due to cache??)
        @param list_type: for subclasses to reuse
    """
    user = auth.user.User.get(user_key)
    bl = booklist.BookList.get_by_user_name(user, list_type)
    for isbn in bl.isbns():
        url, datas = tongji.get_by_isbn(isbn)
        b = books.book.Book.get_by_isbn(isbn)
        b.set_tongji_info(url, datas)
# end of _refresh_tj_worker()


class _BookListHandler(webapp2.RequestHandler):
    """ The base handler for all the Book list handler. """

    # the max fetching amount for one time
    FETCH_LIMIT = 30

    def get(self):
        """ Get method: Ask for data for a particular booklist. """
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        if not user:
            self.redirect('/login')
            return

        template = utils.get_jinja_env().get_template("booklist.html")
        bl = booklist.BookList.get_or_create(user, self.list_type)
        context = {
            'user': user,
            'title': self.title,
            'active_nav': self.active_nav,
            'booklist': bl
        }

        import_started = self.request.get('import_started')
        if import_started:
            # an async Task has just been added to import from douban
            context['import_started'] = True

        start_str = self.request.get('start')
        if start_str:
            try:
                start = int(start_str) - 1
                if start < 0:
                    start = 0
            except Exception:
                start = 0
        else:
            start = 0

        # there are 4 types now:
        # time, rating, voted, pages
        sort_by = self.request.get('sortby')
        if not sort_by:
            sort_by = 'time'
        context['sortby'] = sort_by

        if sort_by == 'time':
            bookbriefs = self._prepare_by_time(user, bl, start)
        elif sort_by == 'public_rating':
            bookbriefs = self._prepare_by_public_rating(user, bl, start)
        elif sort_by == 'user_rating':
            bookbriefs = self._prepare_by_user_rating(user, bl, start)
        elif sort_by == 'rated_amount':
            bookbriefs = self._prepare_by_rated_amount(user, bl, start)
        elif sort_by == 'pages':
            bookbriefs = self._prepare_by_pages(user, bl, start)
        else:
            bookbriefs = None

        if bookbriefs:
            context['bookbriefs'] = bookbriefs
            context['start'] = start + 1
            context['end'] = len(bookbriefs) + start - 1 + 1
            context['prev_url'] = self._prepare_prev_url(start, sort_by)
            context['next_url'] = self._prepare_next_url(start, bl.size(), sort_by)

        self.response.out.write(template.render(context))
        return
    # end of get()

    def _prepare_prev_url(self, start, sortby):
        """ Generate the url for the previous FETCH_LIMIT items.
            @param start: counting from 0.
        """
        # in get(), start has been limited to >= 0
        if start == 0:
            return None

        last = start - self.FETCH_LIMIT
        if last < 0:
            last = 0
        base_url = self.request.path
        params = {
            # in the url, counting from 1
            'start': last + 1,
            'sortby': sortby
        }
        return base_url + '?' + urllib.urlencode(params)

    def _prepare_next_url(self, start, length, sortby):
        """ Generate the url for the following FETCH_LIMIT items.
            @param start: counting from 0.
            @param length: the total amount of available items.
        """
        next = start + self.FETCH_LIMIT
        if next >= length:
            return None

        base_url = self.request.path
        params = {
            # in the url, counting from 1
            'start': next + 1,
            'sortby': sortby
        }
        return base_url + '?' + urllib.urlencode(params)

    def _collect_book(self, user, isbn, bl_name, updated_time):
        """ Collect a specific book related stuffs.
            @param updated_time: its updated time in the booklist.
            @return a BookRelated object.
        """
        brief = books.BookRelated.get_by_user_isbn(user, isbn,
                                                   load_booklist_related=False,
                                                   load_comment=False)
        brief.booklist_name = bl_name
        brief.updated_time = updated_time.strftime("%Y-%m-%d %H:%M:%S")
        return brief

    def _prepare_by_time(self, user, bl, start, oldest=False):
        """ Gather all necessary information for books inside this list.
            @param start: counting from 0.
            @param oldest: whether sort the older ones to be in the front.
        """
        isbn_pairs = bl.isbn_times_pair()
        # list.sort() is slightly more efficient than sorted()
        # if you don't need the original data
        isbn_pairs.sort(key=lambda p: p[1], reverse=(not oldest))

        end = start + self.FETCH_LIMIT
        to_display = isbn_pairs[start:end]

        return [self._collect_book(user, isbn, bl.name, time) for (isbn, time) in to_display]

    def _prepare_by_public_rating(self, user, bl, start):
        """ Gather all necessary information for books inside this list.
            Sorted by public rating.
            @param start: counting from 0.
        """
        helper = books.SortHelper(user)
        isbns = helper.by_public_rating(self.list_type)

        end = start + self.FETCH_LIMIT
        to_display = isbns[start:end]

        return [self._collect_book(user, isbn, bl.name, bl.get_updated_time(isbn)) for isbn in to_display]

    def _prepare_by_user_rating(self, user, bl, start):
        """ Gather all necessary information for books inside this list.
            Sorted by user's rating.
            @param start: counting from 0.
        """
        helper = books.SortHelper(user)
        isbns = helper.by_user_rating(self.list_type)

        end = start + self.FETCH_LIMIT
        to_display = isbns[start:end]

        return [self._collect_book(user, isbn, bl.name, bl.get_updated_time(isbn)) for isbn in to_display]

    def _prepare_by_pages(self, user, bl, start):
        """ Gather all necessary information for books inside this list.
            Sorted by how many people have rated.
            @param start: counting from 0.
        """
        helper = books.SortHelper(user)
        isbns = helper.by_pages(self.list_type)

        end = start + self.FETCH_LIMIT
        to_display = isbns[start:end]

        return [self._collect_book(user, isbn, bl.name, bl.get_updated_time(isbn)) for isbn in to_display]

    def _prepare_by_rated_amount(self, user, bl, start):
        """ Gather all necessary information for books inside this list.
            Sorted by how many people have rated.
            @param start: counting from 0.
        """
        helper = books.SortHelper(user)
        isbns = helper.by_rated_amount(self.list_type)

        end = start + self.FETCH_LIMIT
        to_display = isbns[start:end]

        return [self._collect_book(user, isbn, bl.name, bl.get_updated_time(isbn)) for isbn in to_display]

    def post(self):
        """ Post method is used when user wants to import from douban
            or to refresh Tongji Library info.
        """
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        if not user:
            self.redirect('/login')
            return

        if not user.is_douban_connected():
            # goto the oauth2 of douban
            self.redirect('/auth/douban')
            return

        action = self.request.get('type')
        if action == 'import':
            # import from douban
            self._import_async(user)

            params = {'import_started': True}
            self.redirect(self.request.path + '?' + urllib.urlencode(params))
        elif action == 'douban':
            # refresh each book's public information from douban
            bl = booklist.BookList.get_or_create(user, self.list_type)
            for isbn in bl.isbns():
                t = taskqueue.Task(url='/workers/douban', params={'isbn': isbn})
                t.add(queue_name="douban")

            self.redirect(self.request.path)
        elif action == 'tongji':
            # refresh each book's status in tj library
            bl = booklist.BookList.get_or_create(user, self.list_type)
            for isbn in bl.isbns():
                t = taskqueue.Task(url='/workers/tongji', params={'isbn': isbn})
                t.add(queue_name="tongji")

            self.redirect(self.request.path)
        else:
            self.redirect(self.request.path)

        return

    def _import_async(self, user):
        """ Asyncly import from douban. """
        params = {
            'user_key': user.key(),
            'list_type': self.list_type,
            'action': 'fetch_parse'
        }
        t = taskqueue.Task(url='/workers/import', params=params)
        t.add(queue_name="douban")
        return
# end of class _BookListHandler


class ReadingListHandler(_BookListHandler):
    title = "Reading List"
    active_nav = "Reading"
    list_type = booklist.LIST_READING


class InterestedListHandler(_BookListHandler):
    title = "Interested List"
    active_nav = "Interested"
    list_type = booklist.LIST_INTERESTED


class DoneListHandler(_BookListHandler):
    title = "Done List"
    active_nav = "Done"
    list_type = booklist.LIST_DONE
