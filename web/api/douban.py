'''
@author: Andriy Lin
@description: Dealing with Douban.
'''

import webapp2
import urllib
import urllib2
import json

import auth
import utils.keys as keys
from books.book import Book
from utils.errors import FetchDataError

# the 1st step of the oauth2 procedure
STATE_AUTHORIZATION_CODE = "_STATE_GETTING_AUTHORIZATION_CODE_"
# the 2nd step of the oauth2 procedure
STATE_ACCESS_TOKEN = "_STATE_ACCESS_TOKEN_"


def get_book_by_id(book_id):
    """ Fetch a book's information by its douban id(string). """
    url = "https://api.douban.com/v2/book/" + book_id
    try:
        page = urllib2.urlopen(url)
    except urllib2.HTTPError as err:
        dic = json.loads(err.read())
        raise FetchDataError(msg=dic['msg'], link=url, error_code=dic['code'])
    except urllib2.URLError:
        raise FetchDataError(msg="Url opening failed.", link=url)
    else:
        content = page.read()
        values = json.loads(content)
        b = Book.parseFromDouban(values, book_id)
        return b


def request_authorization_code():
    """ The 1st step of oauth2 procedure for douban. """
    base_url = "https://www.douban.com/service/auth2/auth?"
    params = {
        'client_id': keys.DOUBAN_API_KEY,
        'redirect_uri': "https://andriybook.appspot.com/auth/douban",
        'response_type': "code",
        'scope': 'douban_basic_common,book_basic_r,book_basic_w',
        'state': STATE_AUTHORIZATION_CODE
    }
    url = base_url + urllib.urlencode(params)
    try:
        urllib2.urlopen(url)
    except urllib2.URLError:
        pass
    else:
        pass

def request_access_token(auth_code):
    """ The 2nd step of oauth2 procedure of douban.
        @param auth_code: the authorization_code returned by step 1.
    """
    assert auth_code is not None

    base_url = "https://www.douban.com/service/auth2/token"
    params = {
        'client_id': keys.DOUBAN_API_KEY,
        'client_secret': keys.DOUBAN_SECRET,
        'redirect_uri': "https://andriybook.appspot.com/auth/douban",
        'grant_type': 'authorization_code',
        'code': auth_code
    }
    try:
        urllib2.urlopen(base_url, urllib.urlencode(params))
    except urllib2.URLError:
        pass


class OAuth2Handler(webapp2.RequestHandler):
    """ Handling the redirect_uri when authenticating from Douban. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if email is None:
            self.redirect('/login')
            return

        user = auth.user.User.get_by_email(email)
        state = self.request.get('state')
        if state == STATE_AUTHORIZATION_CODE:
            # the result for getting authorization code
            code = self.request.get('code')
            error = self.request.get('error')
            if code is not None:
                user.douban_authorization_code = code
                user.put()
            elif error is not None:
                self.response.out.write(error)
            else:
                # TODO new a OAuth2Error -> OAuth2DoubanError?
                raise ValueError("Bad response while getting authorization code.")
        elif state == STATE_ACCESS_TOKEN:
            # the result for getting access token
            token = self.request.get('access_token')
            expires = self.request.get('expires_in')
            refresh = self.request.get('refresh_token')
            user_id = self.request.get('douban_user_id')
            user.douban_access_token = token
            user.douban_refresh_token = refresh
            user.douban_user_id = user_id
            user.douban_expires_in = expires
            user.put()
            pass

        pass
