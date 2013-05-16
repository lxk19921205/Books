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
from books.book import Book
import books.booklist as booklist
import books.elements as elements


def _merge_into_datastore(book_related, user):
    """ Update the datastore with the latest data from douban.
        @param book_related: A json object that may contain
            'book', 'comment', 'tags', 'rating', 'updated_time', etc.
        @param user: the corresponding user
        @return: the final Book object for reference
    """
    book = book_related.book
    comment = book_related.comment
    tags = book_related.tags
    rating = book_related.rating

    # check if book exists, if so, update it
    book_db = Book.get_by_isbn(book.isbn)
    if book_db:
        book_db.update_to(book)
        result = book_db
    else:
        book.put()
        result = book

    comment_db = elements.Comment.get_by_user_isbn(user, book.isbn)
    if comment:
        if comment_db:
            comment_db.update_to(comment)
        else:
            comment.put()
    else:
        if comment_db:
            # no such comment, if there is in this system, delete it
            comment_db.delete()

    tags_db = elements.Tags.get_by_user_isbn(user, book.isbn)
    if tags:
        if tags_db:
            tags_db.update_to(tags)
        else:
            tags.put()
    else:
        if tags_db:
            # no such tags, if there is in this system, delete it
            tags_db.delete()

    rating_db = elements.Rating.get_by_user_isbn(user, book.isbn)
    if rating:
        if rating_db:
            rating_db.update_to(rating)
        else:
            rating.put()
    else:
        if rating_db:
            # no such rating, if there is in this system, delete it
            rating_db.delete()

    return result
# end of _update_datastore()

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
            b = _merge_into_datastore(related, user)
            bl.add_isbn(b.isbn, related.updated_time)
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
                                                       booklist_related=False,
                                                       comment=False)
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
