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


class MainHandler(webapp2.RequestHandler):
    """ The handler for the root path "/" of the website. """
    
    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if email is None:
            self.redirect('/login')
        else:
            self.render_book()

    def render_book(self):

        book_id = "6895949"
        url = "https://api.douban.com/v2/book/" + book_id
        
        content = urllib2.urlopen(url).read()
        values = json.loads(content)
        b = Book.parseFromDouban(values)
        b.put()
        def _output(msg):
            self.response.out.write(msg)
            self.response.out.write('<br/>')

        _output("Data Src: " + b.source)
        _output("ISBN: " + b.isbn)
        _output("Title: " + b.title)
        _output("Subtitle: " + b.subtitle)
        _output("Original Title: " + b.title_original)
        _output("Authors: " + ','.join(b.authors))
        _output("Authors Intro: " + b.authors_intro)
        _output("Translators: " + ','.join(b.translators))
        _output("Summary: " + b.summary)
        _output("Rating: " + str(b.rating_avg) + " out of " + str(b.rating_num))
        _output("User Rating: " + str(b.rating_user))
        _output("Image Link: " + b.img_link)
        _output("Douban Url: " + b.douban_url)
        _output("Published by " + b.publisher + " in " + b.published_date)
        _output("Total Pages: " + str(b.pages))
        
        tags_others = zip(b.tags_others_name, b.tags_others_count)
        _output("Tags by others: " + '; '.join(p[0] + '-' + str(p[1]) for p in tags_others))

        _output("User's tags: " + ', '.join(b.tags_user))
        _output("Price: " + str(b.price_amount) + " " + b.price_unit)
        return


app = webapp2.WSGIApplication([
    # the root page
    ('/?', MainHandler),
    
    # sign-up & log-in & log-out & other operations that needs 
    ('/signup/?', auth.SignUpHandler),
    ('/login/?', auth.LogInHandler),
    ('/logout/?', auth.LogOutHandler)
], debug=True)
