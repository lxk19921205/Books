'''
@author: Andriy Lin
@description: Handlers for manipulating book lists
'''

import webapp2

import utils
import auth
import api.douban as douban
import books
import books.elements as elements


class _BookListHandler(webapp2.RequestHandler):
    """ The base handler for all the Book list handler. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if email:
            user = auth.user.User.get_by_email(email)
            template = utils.get_jinja_env().get_template("booklist.html")
            context = {
                'user': user,
                'title': self.title,
                'active_nav': self.active_nav,
                'books': self._prepare_books(user)
            }
            self.response.out.write(template.render(context))
        else:
            self.redirect('/login')

    def _update_datastore(self, book_related_json, user):
        """ Update the datastore with the latest data from douban.
            @param book_related: A json object that may contain
                'book', 'comment', 'tags', 'rating', 'updated_time', etc.
            @param user: the corresponding user
        """
        book = book_related_json.get('book')
        comment = book_related_json.get('comment')
        tags = book_related_json.get('tags')
        rating = book_related_json.get('rating')
        # TODO updated time may not be useful currently
        # updated_time = book_related_json.get('updated')
        isbn = book.isbn

        # check if book exists, if so, update it
        book_db = books.book.Book.get_by_isbn(isbn)
        if book_db:
            book_db.update_to(book)
            book_db.put()
        else:
            book.put()

        comment_db = elements.Comment.get_by_user_isbn(user, isbn)
        if comment:
            if comment_db:
                comment_db.update_to(comment)
                comment_db.put()
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
                tags_db.put()
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
                rating_db.put()
            else:
                rating.put()
        else:
            if rating_db:
                # no such rating, if there is in this system, delete it
                rating_db.delete()
    # end of _update_datastore()

    def _prepare_books(self, user):
        """ For subclasses to override, specifying data source, return the books in this list. """
        raise NotImplementedError()


class ReadingListHandler(_BookListHandler):
    title = "Reading List"
    active_nav = "Reading"

    def _prepare_books(self, user):
        return None


class InterestedListHandler(_BookListHandler):
    title = "Interested List"
    active_nav = "Interested"

    def _prepare_books(self, user):
        if not user.is_douban_connected():
            # display a message to tell to connect douban
            self.redirect('/auth/douban')
            return
        else:
            # TODO still need to save into a local list
            jsons = douban.get_book_list(user, books.booklist.LIST_INTERESTED)
            for json in jsons:
                self._update_datastore(json, user)
            return jsons


class DoneListHandler(_BookListHandler):
    title = "Done List"
    active_nav = "Done"

    def _prepare_books(self, user):
        return None
