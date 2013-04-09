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
import jinja2
import os
import json

from google.appengine.ext import db
from google.appengine.ext.db import Key

from unit3 import Blog
from time import strftime

jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                               autoescape=True)

def blog2dict(blog):
    output = {}
    output['subject'] = blog.title
    output['content'] = blog.text
    output['time'] = blog.time.strftime("%a %b %d %H:%M:%S %Y")
    return output


class AllJsonHandler(webapp2.RequestHandler):
    def get(self):
        blogs = Blog.all().order("-time")
        blogs = list(blogs)
        output = [blog2dict(b) for b in blogs]
        self.response.headers['Content-Type'] = "application/json; charset=UTF-8"
        self.response.out.write(json.dumps(output))


class DetailJsonHandler(webapp2.RequestHandler):
    def get(self):
        blog = None

        i = self.pick_id(self.request.url)
        if len(i) > 0:
            blog = db.get(Key(i))

        if blog:
            self.response.headers['Content-Type'] = "application/json; charset=UTF-8"
            self.response.out.write(json.dumps(blog2dict(blog)))
        else:
            # if not found, can just: self.error(404)
            self.redirect("/unit5/.json")

    def pick_id(self, url):
        url = url.split('/unit5/')[1]
        return url.split('.json')[0]


class NewPostHandler(webapp2.RequestHandler):
    def get(self):
        values = {}
        template = jinja_env.get_template("newpost.html")
        self.response.out.write(template.render(values))
    
    def post(self):
        subject = self.request.get('subject')
        blog = self.request.get('blog')
        if subject and blog:
            b = Blog(title=subject, text=blog)
            key = b.put()
            # can also: b.key().id(), then converts to a number id
            url = "/unit5/" + str(key) + '.json'
            self.redirect(url)
        else:
            values = {
                'subject': subject,
                'blog': blog,
                'error': "Neither fields shall be empty!"
            }
            template = jinja_env.get_template("newpost.html")
            self.response.out.write(template.render(values))
