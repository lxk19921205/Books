'''
@summary: responsible for all stuffs related to authentication
@author: Andriy Lin

@class:
    SignUpHandler: handling "/signup"
    LogInHandler: handling "/login"
'''

import os
import re

import webapp2
import jinja2

from user import User


jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(os.path.realpath("./static/html/")),
                               autoescape = True)


class SignUpHandler(webapp2.RequestHandler):
    """ Handler for url "/signup", directs user to register procedures. """

    def get(self):
        """ Display the sign-up page. """
        values = {}
        self._render(values)

    def post(self):
        """ Handle the sign-up request. """
        email = self.request.get("email")
        pwd = self.request.get("password")
        verify = self.request.get("verify")
        
        # there is verification on browser by JS, but validating again won't hurt
        if not SignUpHandler._validate(email, pwd, verify):
            self.redirect("/signup")
            return
        
        if User.exists(email):
            # telling user that the email has been taken
            values = {}
            values['email_info'] = "Sorry, but the email has been registered by somebody else."
            self._render(values)
        else:
            u = User(email=email, pwd_hashed=pwd)
            u.put()
            # TODO register new user, redirects to welcome page, or redirects to fill personal information
            self.response.out.write(email + ", Welcome!")

    @classmethod
    def _validate(cls, email, pwd, verify):
        """ Validate the registration input again in the server. """
        # email
        pattern = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
        if not pattern.match(email):
            return False
        # pwd
        pattern = re.compile(r"^.{6,30}$")
        if not pattern.match(pwd):
            return False
        # verify
        return pwd == verify

    def _render(self, dic):
        """ Render the sign-up page with @param dic. """
        template = jinja_env.get_template("signup.html")
        self.response.out.write(template.render(dic))


class LogInHandler(webapp2.RequestHandler):
    """ Handler for url "/login", directs user to log in. """
    
    def get(self):
        pass
