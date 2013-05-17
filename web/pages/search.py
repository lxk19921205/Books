'''
@author: Xuankang
@description: Handling the search requests
'''

import urllib
import webapp2

import utils


class SearchHandler(webapp2.RequestHandler):
    """ Handling the search request from nav bar. """

    def get(self):
        keywords = self.request.get('q')
        try:
            utils.validate_isbn(keywords)
        except Exception:
            # not a isbn
            msg = "Invalid ISBN: " + keywords
            params = {'msg': msg}
            self.redirect('/error?' + urllib.urlencode(params))
        else:
            self.redirect('/book/' + keywords)
