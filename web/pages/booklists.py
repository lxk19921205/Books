'''
@author: Andriy Lin
@description: Handlers for manipulating book lists
'''

import webapp2
import urllib
import logging
from google.appengine.ext import deferred

import utils
import auth
from api import douban
from api import tongji
import books
import books.booklist as booklist


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
        bl = booklist.BookList.get_or_create(user, list_type)
        bl.start_importing(len(all_book_related))
        for related in all_book_related:
            b = related.merge_into_datastore(user)
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
    for isbn in bl.isbns:
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

        bookbriefs = self._prepare_by_time(user, bl, start)
        if bookbriefs:
            context['bookbriefs'] = bookbriefs
            context['start'] = start + 1
            context['end'] = len(bookbriefs) + start - 1 + 1
            context['prev_url'] = self._prepare_prev_url(start)
            context['next_url'] = self._prepare_next_url(start, len(bl.isbns))

        self.response.out.write(template.render(context))
        return
    # end of get()

    def _prepare_prev_url(self, start):
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
            'start': last + 1
        }
        return base_url + '?' + urllib.urlencode(params)

    def _prepare_next_url(self, start, length):
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
            'start': next + 1
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
        isbn_pairs = bl.isbn_times()
        # list.sort() is slightly more efficient than sorted()
        # if you don't need the original data
        isbn_pairs.sort(key=lambda p: p[1], reverse=(not oldest))

        end = start + self.FETCH_LIMIT
        to_display = isbn_pairs[start:end]

        return [self._collect_book(user, isbn, bl.name, time) for (isbn, time) in to_display]

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
            booklist.BookList.get_or_create(user, self.list_type).remove_all()
            deferred.defer(_import_worker, user.key(), self.list_type)
            params = {'import_started': True}
            self.redirect(self.request.path + '?' + urllib.urlencode(params))
        elif action == 'tongji':
            # refresh data in tj library
            deferred.defer(_refresh_tj_worker, user.key(), self.list_type)
            self.redirect(self.request.path)

        return
    # end of post()


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
