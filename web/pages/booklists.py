'''
@author: Andriy Lin
@description: Handlers for manipulating book lists
'''

import webapp2

import utils
import auth


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
                'books': self._prepare_books()
            }
            self.response.out.write(template.render(context))
        else:
            self.redirect('/login')

    def _prepare_books(self):
        """ For subclasses to override, specifying data source, return the books in this list. """
        raise NotImplementedError()


class ReadingListHandler(_BookListHandler):
    title = "Reading List"
    active_nav = "Reading"

    def _prepare_books(self):
        return None


class InterestedListHandler(_BookListHandler):
    title = "Interested List"
    active_nav = "Interested"

    def _prepare_books(self):
        return None


class DoneListHandler(_BookListHandler):
    title = "Done List"
    active_nav = "Done"

    def _prepare_books(self):
        return None
