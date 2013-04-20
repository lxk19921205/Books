# coding=utf-8
'''
@author: Andriy Lin
@description: Provide the definition and implementation of @class Book
'''

from google.appengine.ext import db

import datasrc
import utils

from utils.errors import ParseJsonError


class Rating(object):
    """ The rating to a book from others. Including the average score and the amount of voted people.
        If the amount is to few, the score would be None (stands for meaningless).
    """

    def __init__(self, score=None, amount=0):
        self.score = score
        self.amount = amount

    def __unicode__(self):
        if self.score is None:
            return u"Too few people have voted (%s) thus the rating is meaningless." % unicode(self.amount)
        else:
            return u"%s out of %s voters." % (unicode(self.score), unicode(self.amount))


class Tag(object):
    """ The tag attached to a book. (Including the name and the corresponding count.) """

    def __init__(self, name, count=1):
        self.name = name
        self.count = count

    def __unicode__(self):
        if self.count <= 1:
            return unicode(self.name)
        else:
            return unicode(self.name) + u"-" + unicode(self.count)


class Price(object):
    """ The price of a book. """

    def __init__(self, amount, unit):
        self.amount = amount
        self.unit = unit

    def __unicode__(self):
        if self.unit is None:
            return unicode(self.amount)
        else:
            return unicode(self.amount) + u', ' + unicode(self.unit)


class Book(db.Model):
    '''
    the Book class contains everything related to the book. It will be saved in datastore.
    '''
    
    # specify the data source
    source = db.CategoryProperty(required=True)

    # use ISBN as the unique identifier
    isbn = db.StringProperty(required=True, validator=utils.validate_isbn)

    title = db.StringProperty()
    subtitle = db.StringProperty()
    title_original = db.StringProperty()    # title in its original language

    authors = db.StringListProperty()
    authors_intro = db.TextProperty()
    translators = db.StringListProperty()

    summary = db.TextProperty()

    _rating_avg = db.FloatProperty()     # the average rating
    _rating_num = db.IntegerProperty()   # how many people have rated

    img_link = db.LinkProperty()
    douban_url = db.LinkProperty()

    publisher = db.StringProperty()
    published_date = db.StringProperty()
    pages = db.IntegerProperty()

    _tags_others_name = db.StringListProperty()
    _tags_others_count = db.ListProperty(item_type=int)

    _price_amount = db.FloatProperty()
    _price_unit = db.StringProperty()

    @property
    def rating_others(self):
        """ Return a Rating object representing the rating from other users. """
        if self._rating_avg is None and self._rating_num is None:
            return None
        return Rating(score=self._rating_avg, amount=self._rating_num)

    @property
    def tags_others(self):
        """ Return a list of Tag object representing the tags set by others. """ 
        if self._tags_others_name is None or self._tags_others_count is None:
            return []
        zipped = zip(self._tags_others_name, self._tags_others_count)
        return [Tag(name=n, count=c) for n, c in zipped]

    @property
    def price(self):
        """ Return a Price object. """
        if self._price_amount is None and self._price_unit is None:
            return None
        return Price(amount=self._price_amount, unit=self._price_unit)


    @classmethod
    def parse_from_douban(cls, json, book_id=None):
        """ Construct a Book according to the provided json object.
            Raise ParseJsonError on error.
        """
        # isbn
        isbn = json.get('isbn13')
        if not isbn:
            isbn = json.get('isbn10')
        # end of isbn

        b = Book(source=datasrc.DOUBAN, isbn=isbn)

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
                _max = int(_tmp['max'])
                _avg = float(_tmp['average'])

                # convert into 5 scale
                b._rating_avg = _avg * 5 / _max
                if b._rating_avg == 0.0:
                    # 0.0 means the ratings are too few to be meaningful
                    b._rating_avg = None
                b._rating_num = int(_tmp['numRaters'])
            except Exception:
                # Notify that here is error.
                raise ParseJsonError(msg="Parsing rating failed.", res_id=book_id)
            else:
                pass
        # end of ratings

        # image url & douban url
        def _get_image_url():
            """ Parse the json to fetch the image url with highest resolution. """
            _urls = json.get('images')
            if _urls:
                if 'large' in _urls:
                    return _urls['large']
                elif 'medium' in _urls:
                    return _urls['medium']
                elif 'small' in _urls:
                    return _urls['small']
            return json.get('image')

        _tmp = _get_image_url()
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
                value_float = cls._parse_amount_unit(_tmp, unit_str, unit_order)[0]
                if value_float is None:
                    # in case the page_string is just a number-string
                    if _tmp.isdigit():
                        # some books may be a collection, the 'pages' may be u'共12册'
                        b.pages = int(_tmp)
                else:
                    b.pages = int(value_float)
            except Exception:
                raise ParseJsonError(msg="Parsing pages failed.", res_id=book_id)
        # end of publisher & published date & pages

        # tags from others
        def _get_tags_others():
            """ Parse the json to fetch the tags information of others.
                Assume there is 'tags' in the json.
            """
            counts = []
            names = []
            for dic in json.get('tags'):
                counts.append(dic['count'])
                names.append(dic['name'])
            return counts, names

        if 'tags' in json:
            try:
                b._tags_others_count, b._tags_others_name = _get_tags_others()
            except Exception:
                raise ParseJsonError(msg="Parsing tags failed.", res_id=book_id)
        # end of tags from others

        # price
        _tmp = json.get('price')
        if _tmp:
            unit_str = [u'元', '$', 'USD', 'JPY', u'円']
            unit_order = ["after", "before", "before", "before", "after"]
            try:
                b._price_amount, b._price_unit = cls._parse_amount_unit(_tmp, unit_str, unit_order)
                if not b._price_amount:
                    # in case the price_string is just a number string
                    b._price_amount = float(_tmp.strip())
            except Exception:
                raise ParseJsonError(msg="Parsing price failed.", res_id=book_id)
        # end of price

        return b

    @classmethod
    def _parse_amount_unit(cls, src, units, positions):
        """ Return the amount and unit information if they are in the src.
            @param units: a list of unit strings to check
            @param positions:    a list of strings
                                "after" => unit is after amount
                                "before" => unit is before amount.
            @return: amount (float), unit(str)
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
