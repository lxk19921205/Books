'''
@author: Xuankang
@description: Handling the search requests
'''

import urllib
import webapp2

import utils
import auth
from books import TagHelper


class SearchHandler(webapp2.RequestHandler):
    """ Handling the search request from nav bar. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        if not user:
            self.redirect('/login')
            return

        keywords = self.request.get('q')
        if self._is_isbn(keywords):
            # show that book
            self.redirect('/book/' + keywords)
            return

        if self._is_tag(keywords, user):
            # show the books of that tag
            self.redirect('/tags?t=' + keywords)
            return

        msg = "Invalid search words: " + keywords
        params = {'msg': msg}
        self.redirect('/error?' + urllib.urlencode(params))
        return

    def _is_isbn(self, text):
        """ Determine whether the user's input is a valid isbn number. """
        try:
            utils.validate_isbn(text)
        except Exception:
            # not a isbn
            return False
        else:
            return True

    def _is_tag(self, text, user):
        """ Determine whether the user's input is a valid isbn number. """
        if not text:
            # there must be something
            return False

        if ' ' in text:
            # can not be multiple tags
            return False

        helper = TagHelper(user)
        if helper.isbns(text):
            return True
        else:
            return False
