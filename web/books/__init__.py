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
