# coding=utf-8
'''
@author: Andriy Lin
@description: Provide the definition and implementation of @class Book
'''

from google.appengine.ext import db

import utils


class Book(db.Model):
    '''
    the Book class contains everything related to the book. It will be saved in datastore.
    '''
    
    # specify the data source
    source = db.CategoryProperty(required=True)

    # use ISBN as the unique identifier
    isbn = db.StringProperty(required=True, validator=utils.validate_isbn)
    douban_id = db.StringProperty()

    title = db.StringProperty()
    subtitle = db.StringProperty()
    title_original = db.StringProperty()    # title in its original language

    authors = db.StringListProperty()
    authors_intro = db.TextProperty()
    translators = db.StringListProperty()

    summary = db.TextProperty()

    rating_avg = db.FloatProperty()     # the average rating
    rating_max = db.IntegerProperty()   # the maximum rating available
    rating_num = db.IntegerProperty()   # how many people have rated

    img_link = db.LinkProperty()
    douban_url = db.LinkProperty()

    publisher = db.StringProperty()
    published_date = db.StringProperty()
    pages = db.IntegerProperty()

    tags_others_name = db.StringListProperty()
    tags_others_count = db.ListProperty(item_type=int)

    price_amount = db.FloatProperty()
    price_unit = db.StringProperty()


    @classmethod
    def get_by_douban_id(cls, douban_id):
        cursor = db.GqlQuery("select * from Book where ancestor is :parent_key and douban_id = :val",
                     parent_key=utils.get_key_book(),
                     val=douban_id)
        return cursor.get()

# end of Book
