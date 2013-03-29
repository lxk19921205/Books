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
import cgi

form = """
<h1> Enter some text to ROT13: </h1>
<form method="post">
    <textarea name="text">%(text)s</textarea>
    <br />
    <input type="submit">
</form>
"""

class MainHandler(webapp2.RequestHandler):
    def output(self, text=""):
        self.response.write(form % {'text': text})

    def get(self):
    	self.response.headers['Content-Type'] = "text/html"
        self.output()

    def rot13(self, s):
        lower = "abcdefghijklmnopqrstuvwxyz"
        upper = lower.upper()
        result = ""
        for c in s:
            if c in lower:
                index = lower.find(c)
                result = result + lower[(index + 13) % 26]
            elif c in upper:
                index = upper.find(c)
                result = result + upper[(index + 13) % 26]
            else:
                result = result + c
                
        return result

    def post(self):
        t = self.request.get('text')
        temp = self.rot13(t)
        self.output(cgi.escape(temp))

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
