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
from datetime import datetime

from google.appengine.ext import db
from google.appengine.ext.db import Key
from google.appengine.api import memcache

from unit3 import Blog

jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                               autoescape=True)


class MainHandler(webapp2.RequestHandler):
    last_queried = None
    
    def get(self):
        blogs = self.retrieveBlogs()
        now = datetime.now()
        duration = now - self.last_queried
        values = {
            'blogs': blogs,
            'ago': "Queried " + str(duration.seconds) + " seconds ago"
        }
        template = jinja_env.get_template("mainpage.html")
        self.response.out.write(template.render(values))
        
    def retrieveBlogs(self, fromDB = False):
        client = memcache.Client()
        data = client.get("mainpage")
        self.last_queried = client.get("last_queried")

        if fromDB or data == None:
            self.last_queried = datetime.now()
            data = self.retrieveBlogsFromDB()
            client.set("mainpage", data)
            client.set("last_queried", self.last_queried)
        
        return data
    
    def retrieveBlogsFromDB(self):
        blogs = Blog.all().order("-time")
        self.last_queried = datetime.now()
        return list(blogs)


class DetailHandler(webapp2.RequestHandler):
    def get(self):
        i = self.pick_id(self.request.url)
        if len(i) > 0:
            blog, queried_time = self.retrieve(i)
        else:
            blog, queried_time = None, None

        if blog:
            now = datetime.now()
            duration = now - queried_time

            values = {
                'title': blog.title,
                'text': blog.text,
                # formatting: blog.time.strftime("%b %d, %Y")
                'time': blog.time,
                'ago': "Queried " + str(duration.seconds) + " seconds ago"
            }
            template = jinja_env.get_template("detail.html")
            self.response.out.write(template.render(values))
        else:
            # if not found, can just: self.error(404)
            self.redirect("/unit6")

    def pick_id(self, url):
        pos = url.index('/unit6/')
        return url[(pos+7):]

    def retrieve(self, k, fromDB = False):
        client = memcache.Client()
        data = client.get(k)
        last_queried = client.get("last_queried_" + k)

        if fromDB or data == None or last_queried == None:
            last_queried = datetime.now()
            data = db.get(Key(k))
            client.set(k, data)
            client.set("last_queried_" + k, last_queried)
        
        return data, last_queried

class FlushHandler(webapp2.RequestHandler):
    def get(self):
        client = memcache.Client()
        client.flush_all()
        self.redirect("/unit6")
