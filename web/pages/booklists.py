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
import api.douban as douban
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
            related.merge_into_datastore(user)
        bl.finish_importing()
# end of _import_worker()


class _BookListHandler(webapp2.RequestHandler):
    """ The base handler for all the Book list handler. """

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

        bookbriefs = self._prepare_books(user, bl)
        if bookbriefs:
            context['bookbriefs'] = bookbriefs

        self.response.out.write(template.render(context))
    # end of get()

    def _prepare_books(self, user, bl):
        """ Gather all necessary information for books inside this list. """
        def _helper(isbn, updated_time):
            # comment is not need here
            brief = books.BookRelated.get_by_user_isbn(user, isbn,
                                                       load_booklist_related=False,
                                                       load_comment=False)
            brief.booklist_name = bl.name
            brief.updated_time = updated_time.strftime("%Y-%m-%d %H:%M:%S")
            return brief

        return [_helper(isbn, updated_time) for (isbn, updated_time) in bl.isbn_times()]

    def post(self):
        """ Post method is used when user wants to import from douban. """
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        if user:
            if not user.is_douban_connected():
                # goto the oauth2 of douban
                self.redirect('/auth/douban')
            else:
                deferred.defer(_import_worker, user.key(), self.list_type)
                params = {'import_started': True}
                self.redirect(self.request.path + '?' + urllib.urlencode(params))
        else:
            self.redirect('/login')
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
