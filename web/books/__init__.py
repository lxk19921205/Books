"""
@author: Andriy Lin
@description:
    Contains all classes and functions related to books which are the major topic of this project.
"""

import operator

from google.appengine.ext import db
from google.appengine.api import memcache

import utils
import book
import booklist
import elements


class BookRelated(object):
    """ A congregate class gathering all information related to one book. """

    # the book's shared info, book.Book
    book = None

    # the name of the list the book is in, booklist.LIST_XXX or None
    booklist_name = None

    # the time this book was last updated, datetime.datetime
    updated_time = None

    # the user's rating to the book, elements.Rating
    rating = None

    # the user's tags to the book, elements.Tags
    tags = None

    # the user's comment to the book, elements.Comment
    comment = None

    def is_empty(self):
        """ @return: whether it is empty in this object. """
        return self.book is None

    def merge_into_datastore(self, user, update_book=True):
        """ Update the datastore with the latest data from douban.
            @param user: the corresponding user
            @param update: whether to update datastore when there is sth. there.
            @return: the final Book object for reference
        """
        # book
        if update_book:
            book_db = book.Book.get_by_isbn(self.book.isbn)
            if book_db:
                book_db.update_to(self.book)
                result = book_db
            else:
                self.book.put()
                result = self.book
        else:
            if not book.Book.exist(self.book.isbn):
                # no such book, save it
                self.book.put()
                result = self.book
            else:
                result = None
        # end of book

        # booklist
        bls = booklist.BookList.get_all_booklists(user)
        if self.booklist_name:
            from_lists = [bl for bl in bls if self.book.isbn in bl.isbns]
            target_list = booklist.BookList.get_or_create(user, self.booklist_name)

            if from_lists:
                for bl in from_lists:
                    # in case that the book is in many booklists..
                    bl.remove_isbn(self.book.isbn)

            target_list.add_isbn(self.book.isbn, self.updated_time)
        else:
            # remove from any current list
            for bl in bls:
                if self.book.isbn in bl.isbns:
                    bl.remove_isbn(self.book.isbn)
        # end of booklist

        # comment
        comment_db = elements.Comment.get_by_user_isbn(user, self.book.isbn)
        if self.comment:
            if comment_db:
                comment_db.update_to(self.comment)
            else:
                self.comment.put()
        else:
            if comment_db:
                # no such comment, if there is in this system, delete it
                comment_db.delete()
        # end of comment

        # tags
        tag_helper = TagHelper(user)
        tags_db = elements.Tags.get_by_user_isbn(user, self.book.isbn)
        if self.tags:
            # maybe no need to remove duplication, the data here are mostly from douban
            if tags_db:
                for name in tags_db.names:
                    tag_helper.remove(name, tags_db.isbn)
                for name in self.tags.names:
                    tag_helper.add(name, self.tags.isbn)
                tags_db.update_to(self.tags)
            else:
                for name in self.tags.names:
                    tag_helper.add(name, self.tags.isbn)
                self.tags.put()
        else:
            if tags_db:
                # no such tags, if there is in this system, delete it
                for name in tags_db.names:
                    tag_helper.remove(name, tags_db.isbn)
                tags_db.delete()
        # end of tags

        # rating
        rating_db = elements.Rating.get_by_user_isbn(user, self.book.isbn)
        if self.rating:
            if rating_db:
                rating_db.update_to(self.rating)
            else:
                self.rating.put()
        else:
            if rating_db:
                # no such rating, if there is in this system, delete it
                rating_db.delete()
        # end of rating

        # save syncing in memcache
        memcache_data = _SortData()
        memcache_data.isbn = self.book.isbn
        memcache_data.updated_time = self.updated_time
        memcache_data.public_rating = self.book.rating_avg
        memcache_data.rated_amount = self.book.rating_num
        memcache_data.pages = self.book.pages
        if self.rating:
            memcache_data.user_rating = self.rating.score

        helper = SortHelper(user)
        if self.booklist_name:
            # in a list, set it
            helper.set(self.booklist_name, memcache_data)
        else:
            # not in a list, delete any from memcache
            helper.delete(memcache_data.isbn)

        return result
    # end of merge_into_datastore()

    @classmethod
    def get_by_user_isbn(cls, user, isbn,
                         load_book=True, load_booklist_related=True,
                         load_rating=True, load_tags=True, load_comment=True):
        """ Auto-fetching the related objects for a specific book.
            @note: booklist_name & updated_time will not be filled.
            @param rating: whether to load rating, default is True
            @param tags: whether to load tags, default is True
            @param comment: whether to load comment, default is True
        """
        related = BookRelated()
        if load_book:
            related.book = book.Book.get_by_isbn(isbn)

        if load_booklist_related:
            for bl in booklist.BookList.get_all_booklists(user):
                time = bl.get_updated_time(isbn)
                if time is not None:
                    related.booklist_name = bl.name
                    related.updated_time = time
                    break

        if load_rating:
            related.rating = elements.Rating.get_by_user_isbn(user, isbn)

        if load_tags:
            related.tags = elements.Tags.get_by_user_isbn(user, isbn)

        if load_comment:
            related.comment = elements.Comment.get_by_user_isbn(user, isbn)

        return related


class TagHelper(object):
    """ Help manipulating tags using memcache.
        In memcache: 'TagHelper' + user.key(): {tag: isbns ...}
    """

    def __init__(self, user):
        self._user = user
        self._key = 'TagHelper' + str(self._user.key())
        self._client = memcache.Client()

        if self._get() is None:
            self._init_memcache()
        return

    def _get(self):
        return self._client.gets(self._key)

    def _init_memcache(self):
        """ Add data into memcache. """
        cursor = db.GqlQuery("SELECT * FROM Tags WHERE ANCESTOR IS :parent_key AND user = :u",
                             parent_key=utils.get_key_book(),
                             u=self._user)
        results = {}
        for tag in cursor.run():
            for name in tag.names:
                if name in results:
                    results[name].append(tag.isbn)
                else:
                    results[name] = [tag.isbn]

        # set all tags' names, in a cas way
        while True:
            if self._get() is None:
                if self._client.add(self._key, results):
                    break
            else:
                if self._client.cas(self._key, results):
                    break
        return

    def add(self, tag_name, isbn):
        """ Add a record to the Helper. """
        while True:
            obj = self._get()
            if tag_name in obj:
                if isbn in obj[tag_name]:
                    break
                else:
                    obj[tag_name].append(isbn)
            else:
                obj[tag_name] = [isbn]

            if self._client.cas(self._key, obj):
                break
        return

    def remove(self, tag_name, isbn):
        """ Remove a record from the Helper. """
        while True:
            obj = self._get()
            if tag_name not in obj:
                # the tag is not there
                break
            if isbn not in obj[tag_name]:
                # the isbn is not there
                break

            obj[tag_name].remove(isbn)
            if len(obj[tag_name]) == 0:
                del obj[tag_name]

            if self._client.cas(self._key, obj):
                break
        return

    def isbns(self, tag):
        """ @returns: the linked isbn of @param tag. """
        obj = self._client.gets(self._key)
        if tag in obj:
            return obj[tag]
        else:
            return None

    def all(self):
        """ Retrieve all the tags used by a particular user.
            @returns: a list of (tag_name, isbns)
        """
        obj = self._get()
        return obj.items()

    def all_by_amount(self):
        """ Retrieve all the tags used by a particular user.
            Sorted by how many books are linked to that tag, descending.
            @returns: a list of (tag_name, isbns)
        """
        return sorted(self.all(), key=lambda p: len(p[1]), reverse=True)
# end of class TagHelper


class _SortData(object):
    """ Containing data for sorting. """

    def __init__(self):
        # string
        self.isbn = None
        # datetime
        self.updated_time = None
        # float
        self.public_rating = None
        # integer
        self.rated_amount = None
        # integer
        self.user_rating = None
        # integer
        self.pages = None


class SortHelper(object):
    """ Saving useful data for sorting in memcache.
        In memcache: 'SortHelper' + user.key() + booklist_name: [_SortData]
    """

    def __init__(self, user):
        self._user = user
        self._base_key = 'SortHelper' + str(user.key())
        self._client = memcache.Client()

        for name in booklist.LIST_NAMES:
            if self._client.gets(self._key(name)) is None:
                self._init_memcache(name)
        return

    def _key(self, list_name):
        return self._base_key + list_name

    def _collect(self, isbn, time):
        """ Collect relevant data of a book.
            @param u: user.
            @param isbn
            @param time: updated time
            @returns: a _SortData object
        """
        result = _SortData()
        result.isbn = isbn
        result.updated_time = time
        cursor = db.GqlQuery("SELECT rating_avg, rating_num, pages FROM Book " +
                             "WHERE ANCESTOR IS :parent_key AND isbn = :val",
                             parent_key=utils.get_key_book(),
                             val=isbn)
        b = cursor.get()
        result.public_rating = b.rating_avg
        result.rated_amount = b.rating_num
        result.pages = b.pages

        rating = elements.Rating.get_by_user_isbn(self._user, isbn)
        if rating:
            result.user_rating = rating.score
        return result

    def _init_memcache(self, list_name):
        """ Add relevant data into memcache, if no data, just add []. """
        bl = booklist.BookList.get_or_create(self._user, list_name)
        results = [self._collect(isbn, time) for (isbn, time) in bl.isbn_times()]

        # set all data into memcache
        key = self._key(list_name)
        while True:
            if self._client.gets(key) is None:
                if self._client.add(key, results):
                    break
            else:
                if self._client.cas(key, results):
                    break
        return

    def by_public_rating(self, list_name):
        """ Return the isbns of a list sorted by online rating. """
        arr = self._client.gets(self._key(list_name))
        result = sorted(arr,
                        key=operator.attrgetter('public_rating', 'rated_amount', 'updated_time'),
                        reverse=True)
        return [obj.isbn for obj in result]

    def by_user_rating(self, list_name):
        """ Return the isbns of a list sorted by user's rating. """
        arr = self._client.gets(self._key(list_name))
        result = sorted(arr,
                        key=operator.attrgetter('user_rating', 'updated_time'),
                        reverse=True)
        return [obj.isbn for obj in result]

    def by_rated_amount(self, list_name):
        """ Return the isbns of a list sorted by rated amount online. """
        arr = self._client.gets(self._key(list_name))
        result = sorted(arr,
                        key=operator.attrgetter('rated_amount', 'public_rating', 'updated_time'),
                        reverse=True)
        return [obj.isbn for obj in result]

    def by_pages(self, list_name):
        """ Return the isbns of a list sorted by pages length. """
        arr = self._client.gets(self._key(list_name))
        result = sorted(arr,
                        key=operator.attrgetter('pages', 'public_rating', 'rated_amount', 'updated_time'),
                        reverse=True)
        return [obj.isbn for obj in result]

    def clear(self, list_name):
        """ Clear all the data of particular list. """
        key = self._key(list_name)
        while True:
            if self._client.cas(key, []):
                break
        return

    def _find(self, isbn):
        """ @returns: the list_name of a specific book with @param isbn.
            @returns None if not found.
        """
        for list_name in booklist.LIST_NAMES:
            datas = self._client.gets(self._key(list_name))
            target = [d for d in datas if d.isbn == isbn]
            if target:
                return list_name
        return None

    def set(self, list_name, data):
        """ Add or update a data in memcache.
            @param list_name: the target list.
            @param data: a _SortData object.
        """
        from_list = self._find(data.isbn)
        if from_list:
            if from_list == list_name:
                # update it
                key = self._key(list_name)
                while True:
                    arr = self._client.gets(key)
                    for idx in xrange(len(arr)):
                        if arr[idx].isbn == data.isbn:
                            arr[idx] = data
                            break
                    if self._client.cas(key, arr):
                        break
            else:
                # remove & add it
                self._remove(from_list, data.isbn)
                self._add(list_name, data)
        else:
            # just add it
            self._add(list_name, data)
        return

    def set_by_isbn(self, list_name, isbn):
        """ Add or update a data in memcache.
            @param list_name: the target list.
            @param isbn: the ISBN used to collect data
        """
        bl = booklist.BookList.get_or_create(self._user, list_name)
        time = bl.get_updated_time(isbn)
        data = self._collect(isbn, time)
        self.set(list_name, data)
        return

    def _add(self, list_name, data):
        """ Add a data into memcache.
            @param list_name: the list to put into.
            @param data: a _SortData object.
        """
        key = self._key(list_name)
        while True:
            arr = self._client.gets(key)
            for obj in arr:
                if obj.isbn == data.isbn:
                    return
            arr.append(data)
            if self._client.cas(key, arr):
                break
        return

    def _remove(self, list_name, isbn):
        """ Remove a data in a particular list. """
        key = self._key(list_name)
        while True:
            changed = False
            arr = self._client.gets(key)
            for idx in xrange(len(arr)):
                if arr[idx].isbn == isbn:
                    arr.pop(idx)
                    changed = True
                    break
            if not changed:
                break
            if self._client.cas(key, arr):
                break
        return

    def delete(self, isbn):
        """ Delete relevant data in memcache.
            @param isbn: the isbn of the book. ISBN is enough, no need to pass a ful _SortData.
        """
        from_list = self._find(isbn)
        if from_list:
            self._remove(from_list, isbn)
        return
# end of class SortHelper
