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

from utils.errors import FetchDataError, ParseJsonError


class MainHandler(webapp2.RequestHandler):
    """ The handler for the root path "/" of the website. """
    
    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if email is None:
            self.redirect('/login')
        else:
            self.display()

    def _output(self, msg):
        self.response.out.write(msg)
        self.response.out.write('<br/>')

    def display(self):
        book_id = utils.random_book_id()
#        book_id = "1409016"

        try:
            b = douban.get_book_by_id(book_id)
        except FetchDataError as e:
            self._output("Error FETCHING contents from " + book_id)
            self._output("Reason: " + e.msg + "; Error_code: " + str(e.error_code))
            self._output("""<a href=""" + e.link + """>Have a try</a>""")
        except ParseJsonError:
            self._output(" Error PARSING contents from " + book_id)
            self._output("""<a href="http://book.douban.com/subject/""" + book_id + """">Have a try</a> """)
        else:
            b.put()
            self._output("Douban id: " + book_id)
            self._render_book(b)

        return

    def _render_book(self, b):
        self._output("Data Src: " + b.source)
        self._output("ISBN: " + b.isbn)
        self._output("Title: " + b.title)
        self._output("Subtitle: " + b.subtitle)
        self._output("Original Title: " + b.title_original)
        self._output("Authors: " + ', '.join(b.authors))
        self._output("Authors Intro: " + b.authors_intro)
        self._output("Translators: " + ','.join(b.translators))
        self._output("Summary: " + b.summary)
        self._output("Rating: " + unicode(b.rating_others))
        self._output("User Rating: " + unicode(b.rating_user))

        if b.img_link is None:
            self._output("Image Url: ")
        else:
            self._output("""<a href=" """ + b.img_link + """ ">Image Link</a> """)
        if b.douban_url is None:
            self._output("Douban Url: ")
        else:
            self._output("""<a href=" """ + str(b.douban_url) + """ ">Douban Url</a> """)

        self._output("Published by " + b.publisher + " in " + b.published_date)
        self._output("Total Pages: " + str(b.pages))

        tags_others = b.tags_others
        self._output("Tags by others: " + '; '.join(unicode(p) for p in tags_others))

        tags_user = b.tags_user
        self._output("User's tags: " + ', '.join(unicode(p) for p in tags_user))

        price = b.price
        self._output("Price: " + unicode(price))
        return


app = webapp2.WSGIApplication([
    # the root page
    ('/?', MainHandler),
    
    # all authentication operations
    ('/signup/?', auth.SignUpHandler),
    ('/login/?', auth.LogInHandler),
    ('/logout/?', auth.LogOutHandler),

    # 3rd party APIs
    ('/auth/douban/?', douban.OAuth2Handler)
], debug=True)
