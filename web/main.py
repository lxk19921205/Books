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

import urllib2
import json
from books.book import Book

import utils


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
#        book_id = "6895949"
        book_id = utils.random_book_id()
#        book_id = "3625110"
#        book_id = "3684095" # book not found
        url = "https://api.douban.com/v2/book/" + book_id

        values = None
        try:
            content = urllib2.urlopen(url).read()
            values = json.loads(content)
        except:
            self._output(" Error FETCHING contents from " + book_id)
            self._output("""<a href="http://book.douban.com/subject/""" + book_id + """">Have a try</a> """)
            return

        # TODO testing
#         b = Book.parseFromDouban(values, book_id)
#         self._render_book(b)
#         return

        try:
            b = Book.parseFromDouban(values, book_id)
            b.put()
            self._output("Douban id: " + book_id)
            self._render_book(b)
        except:
            self._output(" Error PARSING contents from " + book_id)
            self._output("""<a href="http://book.douban.com/subject/""" + book_id + """">Have a try</a> """)
            self._output("""<a href=""" + '"' + url + '"' + """>Json url</a> """)

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
        
        if b.rating_avg is None:
            self._output("Rating: " + str(b.rating_num) + " have voted, too few to be meaningful.")
        else:
            self._output("Rating: " + str(b.rating_avg) + " out of " + str(b.rating_num))
        self._output("User Rating: " + str(b.rating_user))

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
        
        tags_others = zip(b.tags_others_name, b.tags_others_count)
        self._output("Tags by others: " + '; '.join(p[0] + '-' + str(p[1]) for p in tags_others))
    
        self._output("User's tags: " + ', '.join(b.tags_user))
        if b.price_unit is None:
            self._output("Price: " + str(b.price_amount) + ", " + str(b.price_unit))
        else:
            self._output("Price: " + str(b.price_amount) + ", " + b.price_unit)            



app = webapp2.WSGIApplication([
    # the root page
    ('/?', MainHandler),
    
    # sign-up & log-in & log-out & other operations that needs 
    ('/signup/?', auth.SignUpHandler),
    ('/login/?', auth.LogInHandler),
    ('/logout/?', auth.LogOutHandler)
], debug=True)
