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

import re


jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                               autoescape=True)


class MainHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        template = jinja_env.get_template('template.html')
        self.response.out.write(template.render(template_values))
        return

    def post(self):
        fields = ['username', 'password', 'verify', 'email']
        errors = {
            'username': "That's not a valid username",
            'password': "That wasn't a valid password",
            'verify': "Your passwords didn't match",
            'email': "That's not a valid email"
        }

        values = {}
        for field in fields:
            values[field] = self.request.get(field)

        all_valid = True
        for field in fields:
            if field == 'verify':
                valid = self.check_valid(field, values['password'], values[field])
            else:
                valid = self.check_valid(field, values[field])

            if not valid:
                all_valid = False
                values[field + "_error"] = errors[field]
            # end of for loop

        if all_valid:
            # all valid, go to welcome page
            self.response.headers.add_header("Set-Cookie", str("username=" + values['username']))
            self.redirect('/unit4/welcome')
        else:
            # at least one is invalid, go back and print out it again
            template = jinja_env.get_template('template.html')
            self.response.out.write(template.render(values))

        return


    def check_valid(self, field, arg1, arg2=""):
        if field == 'username':
            pattern = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
            return pattern.match(arg1)

        elif field == 'password':
            pattern = re.compile(r"^.{3,20}$")
            return pattern.match(arg1)

        elif field == 'verify':
            return arg1 == arg2

        elif field == 'email':
            pattern = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
            return arg1 == "" or pattern.match(arg1)

        return False;


class WelcomeHandler(webapp2.RequestHandler):
    def get(self):
        username = self.request.cookies.get("username")
        values = {}
        if username:
            values['username'] = username
        
        template = jinja_env.get_template('welcome.html')
        self.response.out.write(template.render(values))

