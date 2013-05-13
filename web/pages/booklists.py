'''
@author: Andriy Lin
@description: Handlers for manipulating book lists
'''

import webapp2
import urllib

import utils
import auth
import api.douban as douban
from books.book import Book
import books.booklist as booklist
import books.elements as elements


class _BookListHandler(webapp2.RequestHandler):
    """ The base handler for all the Book list handler. """

    def get(self):
        """ Get method: Ask for data for a particular booklist. """
        email = auth.get_email_from_cookies(self.request.cookies)
        if email:
            user = auth.user.User.get_by_email(email)
            template = utils.get_jinja_env().get_template("booklist.html")
            context = {
                'user': user,
                'title': self.title,
                'active_nav': self.active_nav,
            }
            books = self._prepare_books(user)
            if books:
                context['books'] = books

            self.response.out.write(template.render(context))
        else:
            self.redirect('/login')

    def post(self):
        """ Post method is used when user wants to import from douban. """
        email = auth.get_email_from_cookies(self.request.cookies)
        if email:
            user = auth.user.User.get_by_email(email)
            if not user.is_douban_connected():
                # goto the oauth2 of douban
                self.redirect('/auth/douban')
            else:
                # try import, and then refresh page
                try:
                    self._import_from_douban(user)
                except utils.errors.ParseJsonError as err:
                    msg = "Error PARSING book information while importing from Douban. " + str(err)
                    url = "/error?" + urllib.urlencode({'msg': msg})
                    self.redirect(url)
                else:
                    self.redirect(self.request.path)
        else:
            self.redirect('/login')

    def _merge_into_datastore(self, book_related_json, user):
        """ Update the datastore with the latest data from douban.
            @param book_related: A json object that may contain
                'book', 'comment', 'tags', 'rating', 'updated_time', etc.
            @param user: the corresponding user
            @return: The final Book object for reference
        """
        book = book_related_json.get('book')
        comment = book_related_json.get('comment')
        tags = book_related_json.get('tags')
        rating = book_related_json.get('rating')
        # TODO updated time may not be useful currently
        # updated_time = book_related_json.get('updated')
        isbn = book.isbn

        # check if book exists, if so, update it
        book_db = Book.get_by_isbn(isbn)
        if book_db:
            book_db.update_to(book)
            result = book_db
        else:
            book.put()
            result = book

        comment_db = elements.Comment.get_by_user_isbn(user, isbn)
        if comment:
            if comment_db:
                comment_db.update_to(comment)
            else:
                comment.put()
        else:
            if comment_db:
                # no such comment, if there is in this system, delete it
                comment_db.delete()

        tags_db = elements.Tags.get_by_user_isbn(user, isbn)
        if tags:
            if tags_db:
                tags_db.update_to(tags)
            else:
                tags.put()
        else:
            if tags_db:
                # no such tags, if there is in this system, delete it
                tags_db.delete()

        rating_db = elements.Rating.get_by_user_isbn(user, isbn)
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

    def _prepare_books(self, user):
        """ For subclasses to override, specifying data source, return the books in this list. """
        raise NotImplementedError()


class ReadingListHandler(_BookListHandler):
    title = "Reading List"
    active_nav = "Reading"

    def _prepare_books(self, user):
        bl = booklist.BookList.get_by_user_name(user, booklist.LIST_READING)
        return [Book.get_by_isbn(isbn) for isbn in bl.isbns]

    def _import_from_douban(self, user):
        bl = booklist.BookList.get_or_create(user, booklist.LIST_READING)
        bl.remove_all()

        jsons = douban.get_book_list(user, booklist.LIST_READING)
        for json in jsons:
            b = self._merge_into_datastore(json, user)
            bl.add_book(b)
    # end of _import_from_douban()


class InterestedListHandler(_BookListHandler):
    title = "Interested List"
    active_nav = "Interested"

    def _prepare_books(self, user):
        bl = booklist.BookList.get_by_user_name(user, booklist.LIST_INTERESTED)
        return [Book.get_by_isbn(isbn) for isbn in bl.isbns]

    def _import_from_douban(self, user):
        bl = booklist.BookList.get_or_create(user, booklist.LIST_INTERESTED)
        bl.remove_all()

        jsons = douban.get_book_list(user, booklist.LIST_INTERESTED)
        for json in jsons:
            b = self._merge_into_datastore(json, user)
            bl.add_book(b)
    # end of _import_from_douban()


class DoneListHandler(_BookListHandler):
    title = "Done List"
    active_nav = "Done"

    def _prepare_books(self, user):
        bl = booklist.BookList.get_by_user_name(user, booklist.LIST_DONE)
        return [Book.get_by_isbn(isbn) for isbn in bl.isbns]

    def _import_from_douban(self, user):
        bl = booklist.BookList.get_or_create(user, booklist.LIST_DONE)
        bl.remove_all()

        jsons = douban.get_book_list(user, booklist.LIST_DONE)
        for json in jsons:
            b = self._merge_into_datastore(json, user)
            bl.add_book(b)
    # end of _import_from_douban()
