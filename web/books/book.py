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


    def update_to(self, another):
        """ Update to another book's information """
        if self.isbn != another.isbn:
            raise ValueError("The books are different, cannot update to that book.")

        if another.source:
            self.source = another.source
        if another.douban_id:
            self.douban_id = another.douban_id
        if another.title:
            self.title = another.title
        if another.subtitle:
            self.subtitle = another.subtitle
        if another.title_original:
            self.title_original = another.title_original
        if another.authors:
            self.authors = another.authors
        if another.authors_intro:
            self.authors_intro = another.authors_intro
        if another.translators:
            self.translators = another.translators
        if another.summary:
            self.summary = another.summary
        if another.rating_avg:
            self.rating_avg = another.rating_avg
        if another.rating_max:
            self.rating_max = another.rating_max
        if another.rating_num:
            self.rating_num = another.rating_num
        if another.img_link:
            self.img_link = another.img_link
        if another.douban_url:
            self.douban_url = another.douban_url
        if another.publisher:
            self.publisher = another.publisher
        if another.published_date:
            self.published_date = another.published_date
        if another.pages:
            self.pages = another.pages
        if another.tags_others_name:
            self.tags_others_name = another.tags_others_name
        if another.tags_others_count:
            self.tags_others_count = another.tags_others_count
        if another.price_amount:
            self.price_amount = another.price_amount
        if another.price_unit:
            self.price_unit = another.price_unit
    # end of update_to()

    @classmethod
    def get_by_douban_id(cls, douban_id):
        """ Query via douban_id """
        cursor = db.GqlQuery("select * from Book where ancestor is :parent_key and douban_id = :val",
                             parent_key=utils.get_key_book(),
                             val=douban_id)
        return cursor.get()

# end of Book
