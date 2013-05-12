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

import utils
import auth
import pages
import api.douban as douban

from books.book import Book


class MainHandler(webapp2.RequestHandler):
    # TODO move this to a handler handling book list
    """ The handler for the root path "/" of the website. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if email:
            self.display_book_list(auth.user.User.get_by_email(email))
        else:
            self.redirect('/login')

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



class TestHandler(webapp2.RequestHandler):
    """ For testing only. """

    def get(self):
        template = utils.get_jinja_env().get_template('test.html')
        self.response.out.write(template.render({}))


# All mappings
app = webapp2.WSGIApplication([
    # the root page
    ('/?', MainHandler),

    # all authentication operations
    ('/signup/?', auth.SignUpHandler),
    ('/login/?', auth.LogInHandler),
    ('/logout/?', auth.LogOutHandler),

    # 3rd party APIs
    ('/auth/douban/?', douban.OAuth2Handler),

    # manipulating book lists
    ('/booklists/?', pages.booklists.ReadingListHandler),
    ('/booklists/reading/?', pages.booklists.ReadingListHandler),
    ('/booklists/interested/?', pages.booklists.InterestedListHandler),
    ('/booklists/done/?', pages.booklists.DoneListHandler),

    # Explore section
    ('/explore/?', pages.explore.RandomOneHandler),
    ('/explore/random/?', pages.explore.RandomOneHandler),

    # user's information
    ('/me/?', pages.me.MeHandler),

    # when error occurs, report it to this page
    ('/error/?', pages.error.ErrorHandler),

    # only for debugging
    ('/test/?', TestHandler),

    # all possibilities failed, go to 404 Not Found page
    ('/.*', pages.four_o_four.NotFoundHandler)
], debug=True)
