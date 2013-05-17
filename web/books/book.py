# coding=utf-8
'''
@author: Andriy Lin
@description: Provide the definition and implementation of @class Book
'''

from google.appengine.ext import db

import utils
from api.tongji import TongjiData


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

    # the link to its page in Tongji Library
    tongji_url = db.LinkProperty()
    # the id in TJ Library for this book
    tongji_id = db.StringProperty()
    # the following 3 fields may have several instances, that's why it needs a list
    # in which campus
    tongji_campus_list = db.StringListProperty()
    # in which room
    tongji_room_list = db.StringListProperty()
    # current status
    tongji_status_list = db.StringListProperty()

    def is_tongji_linked(self):
        """ @return: True if this book is also found in Tongji Library. """
        return self.tongji_url

    @db.transactional
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

        self.put()
    # end of update_to()

    @db.transactional
    def add_tongji_info(self, url, datas):
        """ Fill the information of a book in Tongji Library into it.
            @param url: the url of that book's page in TJ Library
            @param datas: an array of TongjiData
        """
        if not url:
            return

        self.tongji_url = url
        if datas:
            self.tongji_id = datas[0].id
            self.tongji_campus_list = []
            self.tongji_room_list = []
            self.tongji_status_list = []
            for d in datas:
                self.tongji_campus_list.append(d.campus)
                self.tongji_room_list.append(d.room)
                self.tongji_status_list.append(d.status)
        self.put()

    def _get_tj_availables(self):
        """ @return: a list of TongjiData objects that are available for borrowing. """
        """ @return: True if at least one book is available. """
        datas = self._get_tj_datas()
        available_datas = [d for d in datas if d.status == u"可借"]
        return available_datas

    def _get_tj_datas(self):
        """ @return: all the TongjiData objects as a list. """
        def _generator(tu):
            td = TongjiData()
            td.id = self.tongji_id
            td.campus = tu[0]
            td.room = tu[1]
            td.status = tu[2]
            return td

        return [_generator(t) for t in zip(self.tongji_campus_list,
                                           self.tongji_room_list,
                                           self.tongji_status_list)]
    # end of _get_tj_datas()

    def get_tongji_description(self):
        """ Return a unicode string introducing the current situation in TJ Library. """
        availables = self._get_tj_availables()
        if availables:
            dic = {}
            for td in availables:
                dic[td.room] = td.campus

            return u"Available at " + u"; ".join([k + u'(' + v + u')' for (k, v) in dic.items()])
        else:
            dic = {}
            for td in self._get_tj_datas():
                if td.status in dic:
                    dic[td.status] += 1
                else:
                    dic[td.status] = 1

            def _predicate(num):
                if num > 1:
                    return " are "
                else:
                    return " is "

            return u"Not available now. " + u"; ".join([v + _predicate(v) + k for (k, v) in dic.item()])
        # TODO not tested
    # end of get_tongji_description()


    @classmethod
    def get_by_douban_id(cls, douban_id):
        """ Query via douban_id """
        cursor = db.GqlQuery("SELECT * FROM Book WHERE ANCESTOR IS :parent_key AND douban_id = :val LIMIT 1",
                             parent_key=utils.get_key_book(),
                             val=douban_id)
        return cursor.get()

    @classmethod
    def get_by_isbn(cls, isbn):
        """ Query via douban_id """
        cursor = db.GqlQuery("SELECT * FROM Book WHERE ANCESTOR IS :parent_key AND isbn = :val LIMIT 1",
                             parent_key=utils.get_key_book(),
                             val=isbn)
        return cursor.get()

    @classmethod
    def get_by_isbns(cls, isbns):
        """ Query an array of books by isbns """
        # GQL limit: at most 30 at a time
        assert len(isbns) <= 30

        cursor = db.GqlQuery("SELECT * FROM Book WHERE ANCESTOR IS :parent_key AND isbn IN :isbn_list",
                             parent_key=utils.get_key_book(),
                             isbn_list=isbns)
        return cursor.run()

# end of Book
