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
import unit1
import unit2
import unit3
import unit4
import unit5
import unit6

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Hello World, Andriy is learning GAE")
        return

# /unitX/? this can match both /unitX & /unitX/
app = webapp2.WSGIApplication([
    ('/', MainHandler),
    # in unit 1
    ('/unit1', unit1.MainHandler),
    # in unit 2
    ('/unit2', unit2.MainHandler),
    ('/unit2/welcome', unit2.WelcomeHandler),
    # in unit 3
    ('/unit3', unit3.MainHandler),
    ('/unit3/newpost', unit3.NewPostHandler),
    ('/unit3/.*', unit3.DetailHandler),
    # in unit 4
    ('/unit4', unit4.SignupHandler),
    ('/signup', unit4.SignupHandler),
    ('/unit4/welcome', unit4.WelcomeHandler),
    ('/login', unit4.LoginHandler),
    ('/logout', unit4.LogoutHandler),
    # in unit 5
    ('/unit5/.json', unit5.AllJsonHandler),
    ('/unit5/.*.json', unit5.DetailJsonHandler),
    ('/unit5/newpost', unit5.NewPostHandler),
    # in unit 6
    ('/unit6/?', unit6.MainHandler),
    ('/unit6/flush', unit6.FlushHandler),
    ('/unit6/.*', unit6.DetailHandler)
], debug=True)
