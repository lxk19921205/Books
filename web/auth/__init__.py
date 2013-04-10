'''
@summary: responsible for all stuffs related to authentication
@author: Andriy Lin
'''

import os
import webapp2
import jinja2


jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(os.path.realpath("./static/html/")),
                               autoescape = True)

class SignUpHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_env.get_template("signup.html")
        values = {}
        self.response.out.write(template.render(values))
