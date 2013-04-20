'''
@author: Andriy Lin
@description: Dealing with douban.
'''

import webapp2
import urllib
import urllib2
import json

import auth
import utils.keys as keys

from auth.user import User
from books.book import Book
from utils.errors import FetchDataError


def _fetch_data(url, token=None):
    """ Helper method for retrieving information from douban.
        @param token: The Access_Token by OAuth2 from douban.
        Return a Json object when success.
        Raise FetchDataError when failed.
    """
    req = urllib2.Request(url=url)
    if token is not None:
        req.add_header('Authorization', 'Bearer ' + token)

    try:
        page = urllib2.urlopen(req)
    except urllib2.HTTPError as err:
        obj = json.loads(err.read())
        raise FetchDataError(msg="Error _fetch_data(), MSG: " + obj.get('msg'),
                             link=url,
                             error_code=obj.get('code'))
    except urllib2.URLError:
        raise FetchDataError(msg="Error _fetch_data()", link=url)
    else:
        return json.loads(page.read())


def get_book_by_id(book_id):
    """ Fetch a book's information by its douban id(string). """
    assert book_id

    url = "https://api.douban.com/v2/book/" + book_id
    obj = _fetch_data(url)
    b = Book.parseFromDouban(obj, book_id)
    return b


def get_book_list(uid):
    """ Fetch all book-list of the bound douban user.
        @param uid: the douban user's uid, e.g. andriylin
    """
    assert uid

    url = "https://api.douban.com/v2/book/user/" + uid + "/collections"
    obj = _fetch_data(url)
    return obj


def get_my_info(token):
    """ Retrieve the authenticated user's information. """
    assert token

    url = "https://api.douban.com/v2/user/~me"
    obj = _fetch_data(url, token)
    return obj


def refresh_access_token(user):
    """ When the previous access_token expires, get a new one try the refresh_token. """
    # TODO finish this method when appropriate
    raise NotImplementedError


class OAuth2Handler(webapp2.RequestHandler):
    """ Handling '/auth/douban' (2 cases):
        1. It comes to start douban oauth2 authenticating.
        2. It comes with the authorization code / error from douban.
    """

    # TODO while testing locally, use this URI
    REDIRECT_URI = "http://localhost:8080/auth/douban"
#    REDIRECT_URI = "https://andriybook.appspot.com/auth/douban"

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if email is None:
            # needs to be logged in first!
            self.redirect('/login')
            return

        user = User.get_by_email(email)
        auth_code = self.request.get('code')
        auth_error = self.request.get('error')

        if auth_code:
            # douban user has agreed to authenticate, authorization_code provided.
            base_url, params = self._prepare_access_token_url(auth_code)
            try:
                page = urllib2.urlopen(base_url, urllib.urlencode(params))
            except urllib2.HTTPError as err:
                self.response.out.write("HTTPError" + "<br/>")
                self.response.out.write("AUTH_CODE: " + auth_code + "<br/>")
                self.response.out.write(err.read())
            else:
                obj = json.loads(page.read())
                user.douban_access_token = obj.get('access_token')
                user.douban_refresh_token = obj.get('refresh_token')
                user.douban_id = obj.get('douban_user_id')

                obj = get_my_info(user.douban_access_token)
                user.add_info_from_douban(obj)
                user.put()

                self.redirect('/auth/douban')
        elif auth_error:
            # douban user disagreed to authenticate, error message provided.
            self.response.out.write("Please click Agree to authenticate. MSG: " + auth_error)
        else:
            # To start OAuth2 authentication or has fully finished.
            if user.is_douban_connected():
                self.response.out.write("Douban id: " + user.douban_id)
            else:
                self.redirect(self._prepare_authorization_code_url())
    # end of self.get()

    def _prepare_access_token_url(self, auth_code):
        """ Return (base_url, params) in which params can be passed into urlencode().
            Used in getting access_token in douban's oauth2 procedure.
            @param auth_code: the code returned by douban as the authorization code.
        """
        base_url = "https://www.douban.com/service/auth2/token"
        params = {
            'client_id': keys.DOUBAN_API_KEY,
            'client_secret': keys.DOUBAN_SECRET,
            'redirect_uri': self.REDIRECT_URI,
            'grant_type': 'authorization_code',
            'code': auth_code
        }
        return base_url, params

    def _prepare_authorization_code_url(self):
        """ Return the url for redirecting to douban for oauth2 authentication.
            @param email: the user in this app for identity.
        """
        base_url = "https://www.douban.com/service/auth2/auth"
        params = {
            'client_id': keys.DOUBAN_API_KEY,
            'redirect_uri': self.REDIRECT_URI,
            'response_type': "code",
            'scope': 'douban_basic_common,book_basic_r,book_basic_w'
        }
        url = base_url + '?' + urllib.urlencode(params)
        return url

# end of class OAuth2Handler
