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
from google.appengine.api import taskqueue

import utils
import auth
from pages import booklists
from pages import error
from pages import four_o_four
from pages import me
from pages import onebook
from pages import recommendation
from pages import search
from pages import tags
from pages import upload
from pages import workers
from api import douban


class MainHandler(webapp2.RequestHandler):
    """ The handler for the root path "/" of the website. """

    def get(self):
        self.redirect('/me')
        return


class TestHandler(webapp2.RequestHandler):
    """ For testing only. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        if not user:
            self.redirect('/login')
            return

        action = self.request.get('action')
        if action == 'clear':
            # clear all data in db
            msg = self._clear(user)
        else:
            # default case
            msg = self._test(user)

        template = utils.get_jinja_env().get_template('test.html')
        context = {
            'user': user,
            'msg': msg
        }
        self.response.out.write(template.render(context))
        return

    def _clear(self, user):
        """ Clear all data in datastore. For debugging. """
        classes = ['Book', 'BookList', 'Comment', 'Rating', 'Tags']
        for cls in classes:
            t = taskqueue.Task(params={'cls': cls}, url='/workers/clear')
            t.add(queue_name="debug")

        return "Please also flush the memcache and purge the task queue."

    def _test(self, user):
        """ Default case. """
        return "HELLO WORLD"


# All mappings
app = webapp2.WSGIApplication([
    # the home page
    ('/?', MainHandler),

    # all authentication operations
    ('/signup/?', auth.SignUpHandler),
    ('/login/?', auth.LogInHandler),
    ('/logout/?', auth.LogOutHandler),

    # 3rd party APIs
    ('/auth/douban/?', douban.OAuth2Handler),

    # a particular book
    ('/book/.*', onebook.OneBookHandler),

    # manipulating book lists
    ('/booklists/?', booklists.ReadingListHandler),
    ('/booklists/reading/?', booklists.ReadingListHandler),
    ('/booklists/interested/?', booklists.InterestedListHandler),
    ('/booklists/done/?', booklists.DoneListHandler),

    # manipulating tags
    ('/tags/?', tags.TagsHandler),

    # recommendation section
    ('/recommendation/?', recommendation.RecommendationHandler),
    ('/recommendation/random/?', recommendation.RandomHandler),
    ('/recommendation/whatsnext/?', recommendation.WhatsNextHandler),

    # user's information
    ('/me/?', me.MeHandler),

    # book searches
    ('/search/?', search.SearchHandler),

    # when error occurs, report it to this page
    ('/error/?', error.ErrorHandler),

    # importing from local files
    ('/upload/?', upload.UploadHandler),

    # only for debugging
    ('/test/?', TestHandler),

    # workers for task queue
    ('/workers/clear/?', workers.ClearWorker),
    ('/workers/tongji/?', workers.TongjiWorker),
    ('/workers/import/?', workers.ImportWorker),
    ('/workers/douban/?', workers.DoubanWorker),

    # all possibilities failed, go to 404 Not Found page
    ('/.*', four_o_four.NotFoundHandler)
], debug=True)
