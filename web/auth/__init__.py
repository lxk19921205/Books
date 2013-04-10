'''
@summary: responsible for all stuffs related to authentication
@author: Andriy Lin

@class:
    SignUpHandler: handling "/signup"
    LogInHandler: handling "/login"
'''

import os

import webapp2
import jinja2


jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(os.path.realpath("./static/html/")),
                               autoescape = True)


class SignUpHandler(webapp2.RequestHandler):
    """ Handler for url "/signup", directs user to register. """
    
    def get(self):
        """ Display the sign-up page. """
        template = jinja_env.get_template("signup.html")
        values = {}
        self.response.out.write(template.render(values))

    def post(self):
        """ Handle the sign-up request. """
        email = self.request.get("email")
        pwd = self.request.get("password")
        verify = self.request.get("verify")
        
        self.response.out.write(email + " " + pwd + " " + verify)
        # TODO when registration success, redirect to fill personal information
        pass


class LogInHandler(webapp2.RequestHandler):
    """ Handler for url "/login", directs user to log in. """
    
    def get(self):
        pass
