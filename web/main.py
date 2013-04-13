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


class MainHandler(webapp2.RequestHandler):
    """ The handler for the root path "/" of the website. """
    
    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if email is None:
            self.redirect('/login')
        else:
            self.render_book()

    def render_book(self):
        book_id = "1220562"
        url = "https://api.douban.com/v2/book/" + book_id
        
        import urllib2
        import json
        content = urllib2.urlopen(url).read()
        values = json.loads(content)
        self.response.out.write(str(values))
        pass


app = webapp2.WSGIApplication([
    # the root page
    ('/?', MainHandler),
    
    # sign-up & log-in & log-out & other operations that needs 
    ('/signup/?', auth.SignUpHandler),
    ('/login/?', auth.LogInHandler),
    ('/logout/?', auth.LogOutHandler)
], debug=True)


app_https = webapp2.WSGIApplication([
], debug=True)
