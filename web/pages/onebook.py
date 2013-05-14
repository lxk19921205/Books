'''
@author: Andriy Lin
@description: Displaying a particular book.
'''

import urllib
import webapp2

import utils
import auth
from books.book import Book


class OneBookHandler(webapp2.RequestHandler):
    """ Handling requests for a particular book. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        if not user:
            self.redirect('/login')
            return

        isbn = self.request.path.split('/book/')[1]
        if not utils.validate_isbn(isbn):
            msg = "Invalid ISBN: " + isbn
            params = {'msg': msg}
            self.redirect('/error?' + urllib.urlencode(params))
            return

        template = utils.get_jinja_env().get_template('onebook.html')
        context = {
            'user': user
        }
        b = Book.get_by_isbn(isbn)
        if b:
            context['title'] = b.title
        else:
            context['title'] = "Book Not Found"
        self.response.out.write(template.render(context))
