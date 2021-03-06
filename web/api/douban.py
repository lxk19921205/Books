# coding=utf-8
'''
@author: Andriy Lin
@description: Dealing with douban.
'''

import webapp2
import urllib
import urllib2
import json
import datetime
import codecs

from google.appengine.ext import db
from google.appengine.api import urlfetch

import utils
from utils import errors
from utils import keys
import auth
import books
from books import booklist
from books import datasrc
from books import elements

from auth.user import User


###############################################################################
# for parsing the data fetched
###############################################################################
def _parse_book_img_url(json):
    """ Parse the provided json to fetch the image url with highest resolution.
        Used in parse_book_shared_info()
    """
    _urls = json.get('images')
    if _urls:
        if 'large' in _urls:
            return _urls['large']
        elif 'medium' in _urls:
            return _urls['medium']
        elif 'small' in _urls:
            return _urls['small']
    return json.get('image')


def _parse_book_amount_unit(src, units, positions):
    """ Return the amount and unit information if they are in the src.
        @param units: a list of unit strings to check
        @param positions:    a list of strings
                            "after" => unit is after amount
                            "before" => unit is before amount.
        @return: amount (float), unit(str)
        Used in parse_book_shared_info()
    """
    assert len(units) == len(positions)

    def _split(unit_2_test, relative_pos):
        """ Try different units to fetch the price information out.
            @param unit_2_test is the unit to try.
            @param relative_pos specify whether the unit is "before" or "after" the amount.
        """
        if unit_2_test in src:
            results = src.split(unit_2_test)
            if relative_pos == "after":
                string = results[0]
            elif relative_pos == "before":
                string = results[1]
            else:
                raise ValueError("Only 'before' or 'after' is allowed in @param relative_pos")
            string = string.replace(',', '')
            return float(string.strip()), unit_2_test
        return None, None

    _idx = 0
    amount = None
    unit = None
    while amount is None and _idx < len(units):
        amount, unit = _split(units[_idx], positions[_idx])
        _idx += 1
    return amount, unit


def _parse_book_tags_others(json):
    """ Parse the provided @param json to fetch the tags information of others.
        Assume there is 'tags' in the json.
        Used in _parse_book_shared_info()
    """
    counts = []
    names = []
    for dic in json.get('tags'):
        counts.append(dic['count'])
        names.append(dic['name'])
    return counts, names


def parse_book_shared_info(json, douban_id=None):
    """ Construct a books.book.Book object (contains only shared information)
        @param json: provided json object to parse.
        @raise ParseJsonError
    """
    # isbn
    isbn = json.get('isbn13')
    if not isbn:
        isbn = json.get('isbn10')
    # end of isbn

    b = books.book.Book(source=datasrc.DOUBAN,
                        isbn=isbn,
                        parent=utils.get_key_public('Book'))
    b.douban_id = json.get('id')

    # title & subtitle
    b.title = json.get('title')
    b.subtitle = json.get('subtitle')
    b.title_original = json.get('origin_title')

    # author & their introduction & translators
    b.authors = json.get('author')
    b.authors_intro = json.get('author_intro')
    b.translators = json.get('translator')

    # summary
    b.summary = json.get('summary')

    # ratings
    _tmp = json.get('rating')
    if _tmp:
        try:
            b.rating_max = int(_tmp['max'])
            b.rating_avg = float(_tmp['average'])
            if b.rating_avg == 0.0:
                # 0.0 means the ratings are too few to be meaningful
                b.rating_avg = None
            b.rating_num = int(_tmp['numRaters'])
        except Exception:
            # Notify that here is error.
            raise errors.ParseJsonError(msg="Parsing rating failed.",
                                        res_id=douban_id)
    # end of ratings

    # image url & douban url
    _tmp = _parse_book_img_url(json)
    if _tmp and 'book-default' not in _tmp:
        # the default image link is useless
        b.img_link = db.Link(_tmp)

    _tmp = json.get('alt')
    if _tmp:
        b.douban_url = db.Link(_tmp)
    # end of image url & douban url

    # publisher & published date & pages
    _tmp = json.get('publisher')
    if _tmp:
        # some data from Douban may contain '\n', unreasonable!
        b.publisher = _tmp.replace('\n', ' ')

    b.published_date = json.get('pubdate')
    _tmp = json.get('pages')
    if _tmp:
        unit_str = [u'页']
        unit_order = ['after']
        try:
            value_float = _parse_book_amount_unit(_tmp, unit_str, unit_order)[0]
            if value_float is None:
                # in case the page_string is just a number-string
                if _tmp.isdigit():
                    # some books may be a collection, the 'pages' may be u'共12册'
                    b.pages = int(_tmp)
            else:
                b.pages = int(value_float)
        except Exception:
            raise errors.ParseJsonError(msg="Parsing pages failed.",
                                        res_id=douban_id)
    # end of publisher & published date & pages

    # tags from others
    if 'tags' in json:
        try:
            b.tags_others_count, b.tags_others_name = _parse_book_tags_others(json)
        except Exception:
            raise errors.ParseJsonError(msg="Parsing tags failed.",
                                        res_id=douban_id)
    # end of tags from others

    # price
    _tmp = json.get('price')
    if _tmp:
        unit_str = [u"美元", u'元', '$', 'USD', 'JPY', u'円', 'NTD', 'TWD', 'EUR']
        unit_order = ["after", "after", "before", "before", "before", "after", "before", "before", "before"]
        try:
            b.price_amount, b.price_unit = _parse_book_amount_unit(_tmp, unit_str, unit_order)
            if b.price_amount is None:
                # in case the price_string is just a number string
                b.price_amount = float(_tmp.strip())
        except Exception:
            raise errors.ParseJsonError(msg="Parsing price failed.",
                                        res_id=douban_id)
    # end of price
    return b


def parse_book_related_info(json, user):
    """ Parsing not only the shared book information, but also user's ratings, tags etc.
        @param json: the provided json to parse
        @param user: the corresponding user
        @return: a books.BookRelated object
        Used in get_book_list()
    """
    results = books.BookRelated()
    results.book = parse_book_shared_info(json.get('book'),
                                          json.get('book_id'))
    isbn = results.book.isbn

    # comment
    comment_string = json.get('comment')
    if comment_string:
        c = elements.Comment(user=user,
                             isbn=isbn,
                             parent=utils.get_key_private('Comment', user))
        c.comment = comment_string
        results.comment = c
    # end of comment

    # booklist name
    status = json.get('status')
    if status:
        # specify which list the book is in, if any
        results.booklist_name = {
            'reading': books.booklist.LIST_READING,
            'read': books.booklist.LIST_DONE,
            'wish': books.booklist.LIST_INTERESTED
        }.get(status)
    # end of booklist name

    # updated time
    time_string = json.get('updated')
    if time_string:
        try:
            time = datetime.datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
        else:
            results.updated_time = time
    # end of updated time

    # tags
    tags_array = json.get('tags')
    if tags_array:
        t = elements.Tags(user=user,
                          isbn=isbn,
                          parent=utils.get_key_private('Tags', user))
        t.names = tags_array
        results.tags = t
    # end of tags

    # rating
    rating_obj = json.get('rating')
    if rating_obj:
        r = elements.Rating(user=user,
                            isbn=isbn,
                            parent=utils.get_key_private('Rating', user))
        r.score = int(rating_obj.get('value'))
        r.max_score = int(rating_obj.get('max'))
        r.min_score = int(rating_obj.get('min'))
        results.rating = r
    # end of rating

    return results

###############################################################################
# end of parsing data from fetched data
###############################################################################


###############################################################################
# for fetching data from douban
###############################################################################
def _fetch_data(url, token=None):
    """ Helper method for retrieving information from douban.
        @param token: The Access_Token by OAuth2 from douban.
        @return: a Json object when success.
        @raise TokenExpiredError: when token has expired.
        @raise FetchDataError: when failed for other reasons.
    """
    req = urllib2.Request(url=url)
    if token is not None:
        req.add_header('Authorization', 'Bearer ' + token)

    try:
        # set timeout to be 10 minutes, GAE allow a maximum of 10s for web requests
        # and a 10min for task queues
        page = urllib2.urlopen(req, timeout=600)
    except urllib2.HTTPError as err:
        obj = json.loads(err.read())
        if obj.get('code') == 106 or obj.get('code') == '106':
            # access_token_has_expired
            raise errors.TokenExpiredError()
        else:
            raise errors.FetchDataError(msg="Error _fetch_data(), MSG: " + obj.get('msg'),
                                        link=url,
                                        error_code=obj.get('code'))
    except urllib2.URLError:
        raise errors.FetchDataError(msg="Error _fetch_data()",
                                    link=url)
    else:
        return json.loads(page.read())


def get_book_by_id(book_id):
    """ Fetch a book's information by its douban id(string).
        @return: a Book object
        @raise TokenExpiredError: when token has expired
    """
    url = "https://api.douban.com/v2/book/" + book_id
    obj = _fetch_data(url)
    return parse_book_shared_info(obj, book_id)


def get_book_by_isbn(isbn):
    """ Fetch a book's information by its isbn.
        @return: a Book object
        @raise TokenExpiredError: when token has expired
    """
    url = "https://api.douban.com/v2/book/isbn/%s" % isbn
    obj = _fetch_data(url)
    return parse_book_shared_info(obj, isbn)


def get_book_all_by_id(book_id, user):
    """ Fetch all the info concerned with the book by its douban_id
        Including comments, tags, ratings, etc. If there is any.
        @return: a books.BookRelated object
    """
    url = "https://api.douban.com/v2/book/%s/collection" % book_id
    try:
        obj = _fetch_data(url, user.douban_access_token)
    except errors.TokenExpiredError:
        # expired, refresh, try again
        refresh_access_token(user)
        return get_book_all_by_id(book_id, user)
    except errors.FetchDataError as err:
        if err.error_code == 1001 or err.error_code == "1001":
            # means user hasn't collected this book
            result = books.BookRelated()
            result.book = get_book_by_id(book_id)
            return result
        else:
            raise
    else:
        return parse_book_related_info(obj, user)


def get_book_list_raw(user, list_type=None, start=0, max_count=100):
    """ Fetch all book-list of the bound douban user.
        @param user: current user
        @param type: the identifier of 3 predefined lists, None => All books
        @param start: the start index of importing.
        @param max_count: how many to load this time.
        @return: an array of json objects that can be parsed into books.BookRelated objects.
        @return: an array of string and how many are there in total.
    """
    base_url = "https://api.douban.com/v2/book/user/" + user.douban_uid + "/collections"
    params = {
        'count': max_count,
        'start': start
    }
    if list_type is not None:
        params['status'] = {
            books.booklist.LIST_READING: 'reading',
            books.booklist.LIST_INTERESTED: 'wish',
            books.booklist.LIST_DONE: 'read'
        }[list_type]

    url = base_url + '?' + urllib.urlencode(params)
    try:
        result_json = _fetch_data(url)
    except errors.TokenExpiredError:
        refresh_access_token(user)
        # just stop...
        return [], None

    return result_json['collections'], result_json['total']


def get_book_list(user, list_type=None, start=0):
    """ Fetch all book-list of the bound douban user.
        @param user: current user
        @param type: the identifier of 3 predefined lists, None => All books
        @return: an array of books.BookRelated objects.
    """
    start = 0
    each_time = 100
    results = []
    while True:
        raws, total = get_book_list_raw(user, list_type, start, each_time)
        results += raws
        if start + len(raws) >= total:
            break
        start += each_time

    return [parse_book_related_info(json, user) for json in results]


def get_my_info(token):
    """ Retrieve the authenticated user's information. """
    url = "https://api.douban.com/v2/user/~me"
    return _fetch_data(url, token)


def edit_book(book_id, user, related, method):
    """ Edit the user's rating, comment, tag, or booklist to this book.
        @param book_id: the book's douban_id
        @param user: the corresponding user
        @param related: a BookRelated object that contains relavant data
        @param method: one of "POST", "PUT", or "DELETE"
        @return: the response object returned by urlfetch.fetch()
    """
    url = "https://api.douban.com/v2/book/%s/collection" % book_id
    params = {
        "status": {
            booklist.LIST_INTERESTED: 'wish',
            booklist.LIST_READING: 'reading',
            booklist.LIST_DONE: 'read'
        }.get(related.booklist_name)
    }
    if related.tags:
        params['tags'] = codecs.encode(' '.join(related.tags.names), 'utf-8')
    else:
        params['tags'] = ""

    if related.comment:
        params['comment'] = codecs.encode(related.comment.comment, 'utf-8')
    else:
        params['comment'] = ""

    if related.rating:
        params['rating'] = related.rating.score
    else:
        params['rating'] = 0

    header = {
        'Authorization': 'Bearer ' + user.douban_access_token,
        # without the following header, PUT won't work!
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    if method == "POST":
        result = urlfetch.fetch(url=url,
                                payload=urllib.urlencode(params),
                                method=urlfetch.POST,
                                headers=header)
    elif method == "PUT":
        result = urlfetch.fetch(url=url,
                                payload=urllib.urlencode(params),
                                method=urlfetch.PUT,
                                headers=header)
    elif method == "DELETE":
        result = urlfetch.fetch(url=url,
                                method=urlfetch.DELETE,
                                headers=header)
    return result


def upload_book(user, book_id, tag_string):
    """ Save a book into douban's wish list. """
    url = "https://api.douban.com/v2/book/%s/collection" % book_id
    params = {
        'status': 'wish',
        'tags': codecs.encode(tag_string, 'utf-8')
    }

    header = {
        'Authorization': 'Bearer ' + user.douban_access_token,
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    result = urlfetch.fetch(url=url,
                            payload=urllib.urlencode(params),
                            method=urlfetch.POST,
                            headers=header)
    return result


def refresh_access_token(user):
    """ When the previous access_token expires, get a new one try the refresh_token. """
    url = "https://www.douban.com/service/auth2/token"
    params = {
        'client_id': keys.DOUBAN_API_KEY,
        'client_secret': keys.DOUBAN_SECRET,
        'redirect_uri': OAuth2Handler.REDIRECT_URI,
        'grant_type': 'refresh_token',
        'code': user.douban_refresh_token
    }

    result = urlfetch.fetch(url=url,
                            payload=urllib.urlencode(params),
                            method=urlfetch.POST)
    obj = json.loads(result.content)

    user.douban_access_token = obj.get('access_token')
    user.douban_refresh_token = obj.get('refresh_token')
    user.put()
    return

###############################################################################
# end of fetching data from douban
###############################################################################


###############################################################################
# for the OAuth2 procedures of douban
###############################################################################
class OAuth2Handler(webapp2.RequestHandler):
    """ Handling '/auth/douban' (2 cases):
        1. It comes to start douban oauth2 authenticating.
        2. It comes with the authorization code / error from douban.
    """

    # while testing locally, use this URI
    REDIRECT_URI = "http://localhost:8080/auth/douban"
#    REDIRECT_URI = "https://andriybook.appspot.com/auth/douban"

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = User.get_by_email(email)
        if not user:
            # needs to be logged in first!
            self.redirect('/login')
            return

        auth_code = self.request.get('code')
        auth_error = self.request.get('error')

        if auth_code:
            # douban user has agreed to authenticate, authorization_code provided.
            base_url, params = self._prepare_access_token_url(auth_code)
            try:
                page = urllib2.urlopen(base_url, urllib.urlencode(params))
            except urllib2.HTTPError:
                msg = "HTTP error when trying to get the access token from douban, auth_code: %s" % auth_code
                self.redirect('/error?' + urllib.urlencode({'msg': msg}))
            else:
                obj = json.loads(page.read())
                user.douban_access_token = obj.get('access_token')
                user.douban_refresh_token = obj.get('refresh_token')
                user.douban_id = obj.get('douban_user_id')

                obj = get_my_info(user.douban_access_token)
                user.add_info_from_douban(obj)
                user.put()

                self.redirect('/me')
        elif auth_error:
            # douban user disagreed to authenticate, error message provided.
            msg = "Please click Agree to bind your Douban account! Auth error: %s" % auth_error
            self.redirect('/error?' + urllib.urlencode({'msg': msg}))
        else:
            # To start OAuth2 authentication or has fully finished.
            if user.is_douban_connected():
                self.redirect('/me')
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
