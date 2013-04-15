# coding=utf-8
'''
@author: Andriy Lin
@description: Provide the definition and implementation of @class Book
'''

from google.appengine.ext import db

import datasrc
import utils

class Tag(object):
    """ The tag attached to a book. """
    
    def __init__(self, name, count=1):
        self.name = name
        self.count = count


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

    # TODO rating_avg == 0.0  ==>  too few ratings, useless
    rating_avg = db.FloatProperty()     # the average rating
    rating_num = db.IntegerProperty()   # how many people have rated
    rating_user = db.IntegerProperty()  # the rating from user

    img_link = db.LinkProperty()
    douban_url = db.LinkProperty()

    publisher = db.StringProperty()
    published_date = db.StringProperty()
    pages = db.IntegerProperty()

    tags_others_count = db.ListProperty(item_type=int)
    tags_others_name = db.StringListProperty()
    tags_user = db.StringListProperty()

    price_amount = db.FloatProperty()
    price_unit = db.StringProperty()


    @classmethod
    def parseFromDouban(cls, json):
        """ Construct a Book according to the provided json object. """
        # isbn
        isbn = json.get('isbn13')
        if isbn is None:
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
        if _tmp is not None:
            _max = int(_tmp['max'])
            _avg = float(_tmp['average'])
            
            # convert into 5 scale
            b.rating_avg = _avg * 5 / _max
            b.rating_num = int(_tmp['numRaters'])
        # end of ratings

        # image url & douban url
        def _get_image_url():
            """ Parse the json to fetch the image url with highest resolution. """
            _urls = json.get('images')
            if _urls is not None:
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
        if _tmp is not None:
            b.douban_url = db.Link(_tmp)
        # end of image url & douban url

        # publisher & published date & pages
        b.publisher = json.get('publisher')
        b.published_date = json.get('pubdate')
        _tmp = json.get('pages')
        if _tmp:
            b.pages = int(_tmp)
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
            b.tags_others_count, b.tags_others_name = _get_tags_others()
        # end of tags from others

        # price
        def _get_price(unit, unitIsAfter):
            """ Try different units to fetch the price information out.
                @param unit is the unit to try.
                @param unitIsAfter specify whether the unit is before or after the amount. 
            """
            price_str = json.get('price')
            if unit in price_str:
                results = price_str.split(unit)
                if unitIsAfter:
                    return float(results[0].strip()), unit
                else:
                    return float(results[1].strip()), unit
            return None, None

        _tmp = json.get('price')
        if _tmp:
            unit_str = [u'元', '$', 'USD']
            before = False
            after = True
            unit_order = [after, before, before]
            _idx = 0
            while b.price_amount is None and _idx < len(unit_str):
                b.price_amount, b.price_unit = _get_price(unit_str[_idx], unit_order[_idx])
                _idx += 1

            if b.price_amount is None:
                # in case the price_string is just a number string
                try:
                    b.price_amount = float(_tmp.strip())
                except:
                    b.price_amount = None
                    b.price_unit = None
        # end of price

        return b
