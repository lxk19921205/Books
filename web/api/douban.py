'''
@author: Andriy Lin
@description: Dealing with Douban.
'''

import urllib2
import json

from books.book import Book
from utils.errors import FetchDataError


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
