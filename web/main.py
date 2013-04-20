#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import webapp2

import auth
import api.douban as douban
import utils

from books.book import Book
from utils.errors import FetchDataError, ParseJsonError


class MainHandler(webapp2.RequestHandler):
    """ The handler for the root path "/" of the website. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if email:
#            self.display_one_book()
            self.display_book_list(auth.user.User.get_by_email(email))
        else:
            self.redirect('/login')

    def _output(self, msg):
        """ Write a line of msg to response. """
        self.response.out.write(msg)
        self.response.out.write('<br/>')

    def _output_item(self, name, value):
        self.response.out.write(name + ': ')
        self.response.out.write(value)
        self.response.out.write('<br/>')

    def display_book_list(self, user):
        """ Display the booklist of the binded douban user. """
        if not user.is_douban_connected():
            self.redirect('/auth/douban')
        else:
            uid = user.douban_uid
            books = douban.get_book_list(uid)
            books = books['collections']
            for book_obj in books:
                # keys(): 'status', 'comment', 'updated', 'user_id', 'rating', 'book', 'book_id', 'id'
                self._output('')
                self._output('')

                self._output_item('Status', book_obj['status'])
                self._output_item('Rating', book_obj['rating'])
                self._output_item('Updated time', book_obj['updated'])
                self._output_item('Saved by', book_obj['user_id'])
                self._output_item('id (what is that?)', book_obj['id'])
                b = Book.parse_from_douban(book_obj['book'], book_obj['book_id'])
                self._render_book(b)

                self._output('')
                self._output('')
            # end of for loop

    def display_one_book(self):
        """ Randomly pick a book from douban to display. """
        book_id = utils.random_book_id()
        book_id = "3597031"

        try:
            b = douban.get_book_by_id(book_id)
        except FetchDataError as e:
            self._output("Error FETCHING contents from " + book_id)
            self._output("Reason: " + e.msg + "; Error_code: " + str(e.error_code))
            self._output("""<a href=""" + e.link + """>Have a try</a>""")
        except ParseJsonError:
            self._output(" Error PARSING contents from " + book_id)
            html = '<a href="http://book.douban.com/subject/%s">Have a try</a>' % book_id
            self._output(html)
        else:
            b.put()
            self._output("Douban id: " + book_id)
            self._render_book(b)
    # end of self.display()

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


class MeHandler(webapp2.RequestHandler):
    """ Handling '/me' or '/me/' """

    def _output(self, name, value):
        self.response.out.write(name + ": ")
        self.response.out.write(value)
        self.response.out.write('<br/>')

    def _output_link(self, name, link):
        html = "<a href='%s'>%s</a>" % (link, name)
        self.response.out.write(html)
        self.response.out.write('<br/>')

    def _output_image(self, link):
        html = "<img src='%s'/>" % link
        self.response.out.write(html)
        self.response.out.write('<br/>')

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if not email:
            self.redirect('/login')
            return

        user = auth.user.User.get_by_email(email)
        self._output('Email', user.email)
        self._output('Douban id', user.douban_id)
        self._output('Douban uid', user.douban_uid)
        self._output('Douban name', user.douban_name)
        self._output_image(user.douban_image)
        self._output_link('URL', user.douban_url)
        self._output('Signature', user.douban_signature)
        self._output('Description', user.douban_description)
        self._output('Created at', user.douban_created_time)


app = webapp2.WSGIApplication([
    # the root page
    ('/?', MainHandler),

    # all authentication operations
    ('/signup/?', auth.SignUpHandler),
    ('/login/?', auth.LogInHandler),
    ('/logout/?', auth.LogOutHandler),

    # 3rd party APIs
    ('/auth/douban/?', douban.OAuth2Handler),

    # user's information
    ('/me/?', MeHandler)
], debug=True)
