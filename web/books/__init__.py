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
