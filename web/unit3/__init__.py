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

from google.appengine.ext import db
from google.appengine.ext.db import Key


jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                               autoescape=True)

class Blog(db.Model):
    title = db.StringProperty(required=True)
    text = db.TextProperty(required=True)
    time = db.DateTimeProperty(auto_now_add=True)


class MainHandler(webapp2.RequestHandler):
    def get(self):
        blogs = db.GqlQuery("select * from Blog order by time desc")
        values = {'blogs': blogs}
        template = jinja_env.get_template("template.html")
        self.response.out.write(template.render(values))


class NewPostHandler(webapp2.RequestHandler):
    def get(self):
        values = {}
        template = jinja_env.get_template("newpost.html")
        self.response.out.write(template.render(values))
        return
    
    def post(self):
        subject = self.request.get('subject')
        blog = self.request.get('blog')
        if subject and blog:
            # TODO save into db
            b = Blog(title=subject, text=blog)
            key = b.put()
            url = "/unit3/" + str(key)
            self.redirect(url)
        else:
            values = {
                'subject': subject,
                'blog': blog,
                'error': "Neither fields shall be empty!"
            }
            template = jinja_env.get_template("newpost.html")
            self.response.out.write(template.render(values))
        return


class DetailHandler(webapp2.RequestHandler):
    def get(self):
        i = self.pick_id(self.request.url)
        if len(i) > 0:
            blogCursor = db.GqlQuery("select * from Blog where __key__ = :id", id=Key(i))
            blog = blogCursor.get()
        else:
            blog = None

        if blog:
            values = {
                'title': blog.title,
                'text': blog.text,
                'time': blog.time
            }
            template = jinja_env.get_template("detail.html")
            self.response.out.write(template.render(values))
        else:
            self.redirect("/unit3")

    def pick_id(self, url):
        pos = url.index('/unit3/')
        return url[(pos+7):]
