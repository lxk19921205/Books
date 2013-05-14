'''
@author: Andriy Lin
@description: Displaying a particular book.
'''

import urllib
import webapp2

import utils
import auth


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

        # TODO
        self.response.out.write("ONE BOOK: " + self.request.path + "<br/>" + isbn)
