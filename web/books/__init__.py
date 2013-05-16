"""
@author: Andriy Lin
@description: 
    Contains all classes and functions related to books which are the major topic of this project.
"""

import book
import booklist
import datasrc
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


    def merge_into_datastore(self, user):
        """ Update the datastore with the latest data from douban.
            @param user: the corresponding user
            @return: the final Book object for reference
        """
        # book
        book_db = book.Book.get_by_isbn(self.book.isbn)
        if book_db:
            book_db.update_to(self.book)
            result = book_db
        else:
            self.book.put()
            result = self.book
        # end of book

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
        tags_db = elements.Tags.get_by_user_isbn(user, self.book.isbn)
        if self.tags:
            if tags_db:
                tags_db.update_to(self.tags)
            else:
                self.tags.put()
        else:
            if tags_db:
                # no such tags, if there is in this system, delete it
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

        return result
    # end of merge_into_datastore()


    @classmethod
    def get_by_user_isbn(cls, user, isbn, booklist_related=True, rating=True, tags=True, comment=True):
        """ Auto-fetching the related objects for a specific book.
            @note: booklist_name & updated_time will not be filled.
            @param rating: whether to load rating, default is True
            @param tags: whether to load tags, default is True
            @param comment: whether to load comment, default is True
        """
        related = BookRelated()
        related.book = book.Book.get_by_isbn(isbn)

        if booklist_related:
            for bl in booklist.BookList.get_all_booklists(user):
                time = bl.get_updated_time(isbn)
                if time is not None:
                    related.booklist_name = bl.name
                    related.updated_time = time
                    break

        if rating:
            related.rating = elements.Rating.get_by_user_isbn(user, isbn)

        if tags:
            related.tags = elements.Tags.get_by_user_isbn(user, isbn)

        if comment:
            related.comment = elements.Comment.get_by_user_isbn(user, isbn)

        return related
