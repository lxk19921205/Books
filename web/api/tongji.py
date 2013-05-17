# coding=utf-8
'''
@author: Andriy Lin
@description: Dealing with retrieving information from Tongji Library
'''

import re
import codecs
from HTMLParser import HTMLParser
import urllib
from google.appengine.api import urlfetch


class TongjiData(object):
    """ Container class for all necessary fields. """
    id = None
    campus = None
    room = None
    status = None

class _TongjiParser(HTMLParser):
    """ Parsing the table html containing book information. """
    data_parsed = []
    data_parsing = None
    tag_stack = []
    td_count = 0

    def _tag_push(self, tag):
        self.tag_stack.append(tag)

    def _tag_pop(self):
        self.tag_stack.pop()

    def _tag_top(self):
        if len(self.tag_stack) > 0:
            return self.tag_stack[-1]
        else:
            return None

    def handle_starttag(self, tag, attrs):
        self._tag_push(tag)
        if tag == 'tr':
            # start a new row
            self.data_parsing = TongjiData()
            self.td_count = 0
        elif tag == 'td':
            # encounter a new data
            self.td_count += 1

    def handle_endtag(self, tag):
        self._tag_pop()
        if tag == 'tr':
            # ends the current row
            self.data_parsed.append(self.data_parsing)
            self.data_parsing = None
            self.td_count = 0
        elif tag == 'td':
            # ends the current data
            pass

    def handle_data(self, data):
        if self._tag_top() == 'td':
            # only now the data is meaningful
            if self.td_count == 1:
                self.data_parsing.id = data
            elif self.td_count == 4:
                self.data_parsing.campus = data
            elif self.td_count == 5:
                self.data_parsing.room = data
        elif self._tag_top() == 'font':
            # an extra case is that src file added some css into html!
            if self.td_count == 6:
                self.data_parsing.status = data


def get_by_isbn(isbn):
    """ Add the important information from Tongji Library.
        @param book: The books.book.Book object, assuming that it has field isbn
        @return: (the url of this book in TJ library, and an array of parsed data)
    """
    # try get the search results first
    base_url = "http://webpac.lib.tongji.edu.cn/opac/openlink.php"
    params = {
        'strSearchType': 'isbn',
        'historyCount': 1,
        'strText': isbn,
        'doctype': 'ALL',
        'match_flag': 'forward',
        'displaypg': 20,
        'sort': 'CATA_DATE',
        'orderby': 'desc',
        'showmode': 'list',
        'dept': 'ALL',
    }

    search_results = urlfetch.fetch(base_url + '?' + urllib.urlencode(params))
    decoded = codecs.decode(search_results.content, 'utf-8')
    match = re.search(u"本馆没有您检索的馆藏书目", decoded)
    if match:
        # No such book in Tongji Library
        return None, None

    pat = r'<a href="item.php\?marc_no=(\d+)">'
    match = re.search(pat, decoded)
    if not match:
        return None, None

    item_num = match.group(1)
    base_url = "http://webpac.lib.tongji.edu.cn/opac/item.php"
    params = {
        'marc_no': item_num
    }
    # also save this url
    tongji_url = base_url + '?' + urllib.urlencode(params)
    try:
        # have to set deadline explicitly, because it responds very slowly!!!
        detail_page = urlfetch.fetch(url=tongji_url, deadline=15)
    except Exception:
        # the time on this may exceed the limit
        return tongji_url, None
    else:
        decoded = codecs.decode(detail_page.content, 'utf-8')

    pat = r'<table width="670" border="0" align="center" cellpadding="2" cellspacing="1" bgcolor="#d2d2d2">([\s\S]*)</table>'
    rows = re.search(pat, decoded)
    if not rows:
        return tongji_url, None

    parser = _TongjiParser()
    parser.feed(rows.group(1))

    # the first one is the title
    return tongji_url, parser.data_parsed[1:]
