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
import books
from api import douban
from api import tongji


class MainHandler(webapp2.RequestHandler):
    """ The handler for the root path "/" of the website. """

    def get(self):
        self.redirect('/me')


class TestHandler(webapp2.RequestHandler):
    """ For testing only. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        if user:
            msg = self.testing(user)
        else:
            msg = None

        self.response.out.write(len(msg))
        self.response.out.write("<br/>")
        for d in msg:
            self.response.out.write(d.id)
            self.response.out.write("<br/>")
            self.response.out.write(d.campus)
            self.response.out.write("<br/>")
            self.response.out.write(d.room)
            self.response.out.write("<br/>")
            self.response.out.write(d.status)
            self.response.out.write("<br/>")
            self.response.out.write("<br/>")
        return

        template = utils.get_jinja_env().get_template('test.html')
        context = {
            'user': user,
            'msg': msg
        }
        self.response.out.write(template.render(context))

    def testing(self, user):
        """ Doing testing & debugging & trying stuffs here. """
#        url, datas = tongji.get_by_isbn("9787544702065") # book found
        url, datas = tongji.get_by_isbn("978-7-115-28158-6")
        return datas
#        return tongji.get_book_by_isbn("9787510704390") # no such book


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

    # a particular book
    ('/book/.*', pages.onebook.OneBookHandler),

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

    # book searches
    ('/search/?', pages.search.SearchHandler),

    # when error occurs, report it to this page
    ('/error/?', pages.error.ErrorHandler),

    # only for debugging
    ('/test/?', TestHandler),

    # all possibilities failed, go to 404 Not Found page
    ('/.*', pages.four_o_four.NotFoundHandler)
], debug=True)
