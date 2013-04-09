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
