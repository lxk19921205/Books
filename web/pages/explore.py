'''
@author: Andriy Lin
@description: Containing handlers for pages in Explore section
    1. Random!
'''

import webapp2

import auth
import utils
import api.douban as douban

from utils.errors import FetchDataError, ParseJsonError


class RandomOneHandler(webapp2.RequestHandler):
    """ Handling url "explore/random", randomly pick a book and present it. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if email:
            self.display_one_book();
        else:
            self.redirect('/login')

    def display_one_book(self):
        """ Randomly pick a book from douban to display. """
        book_id = utils.random_book_id()
        # for debugging, set a exact book id
        # book_id = "3597031"

        try:
            # TODO to check from local store first?
            b = douban.get_book_by_id(book_id)
        except FetchDataError as e:
            # TODO to change
            self._output("Error FETCHING contents from " + book_id)
            self._output("Reason: " + e.msg + "; Error_code: " + str(e.error_code))
            self._output("""<a href=""" + e.link + """>Have a try</a>""")
        except ParseJsonError:
            # TODO to change
            self._output(" Error PARSING contents from " + book_id)
            html = '<a href="http://book.douban.com/subject/%s">Have a try</a>' % book_id
            self._output(html)
        else:
            b.put()
            self._output("Douban id: " + book_id)
            self._render_book(b)
    # end of self.display()

    def _output(self, msg):
        """ Write a line of msg to response. """
        self.response.out.write(msg)
        self.response.out.write('<br/>')

    def _output_item(self, name, value):
        self.response.out.write(name + ': ')
        self.response.out.write(value)
        self.response.out.write('<br/>')

    def _render_book(self, b):
        self._output_item('Data src', b.source)
        self._output_item('ISBN', b.isbn)
        self._output_item('Title', b.title)
        self._output_item('Subtitle', b.subtitle)
        self._output_item("Original Title", b.title_original)
        self._output_item("Authors", ', '.join(b.authors))
        self._output_item("Authors Intro", b.authors_intro)
        self._output_item("Translators", ','.join(b.translators))
        self._output_item("Summary", b.summary)
        self._output_item("Rating", b.rating_others)

        if b.img_link:
            html = '<img src="%s"/>' % b.img_link
            self._output(html)
        else:
            self._output("Image Url: ")
        if b.douban_url:
            self._output("""<a href=" """ + b.douban_url + """ ">Douban Url</a> """)
        else:
            self._output("Douban Url: ")

        self._output_item("Published by", b.publisher)
        self._output_item('Published in', b.published_date)
        self._output_item("Total Pages", b.pages)

        tags_others = b.tags_others
        self._output_item("Tags by others", '; '.join(unicode(p) for p in tags_others))

        price = b.price
        self._output_item("Price", price)
    # end of self._render_book(b)
