'''
@summary: responsible for all stuffs related to authentication
@author: Andriy Lin

@content:
    @function: get_email_from_cookies(), retrieve the user_id -- email
    @class: SignUpHandler: handling "/signup"
    @class: LogInHandler: handling "/login"
'''

import os
import re
import datetime

import webapp2
import jinja2
import logging

import encrypt

from google.appengine.ext.db import TransactionFailedError
from user import User


jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.realpath("./static/html/")),
                               autoescape=True)


def get_email_from_cookies(cookies):
    """ Try to retrieve the user_id (that is, the email) from cookies.
    If it is not present, return None.
    If the cookies is broken (say, being modified by someone), it is no longer valid.
    """
    src = cookies.get('user_id')
    if src is not None:
        email = src.split('|')[0]
        if encrypt.check_encoded(email, src):
            return email

    return None


class _AuthHandler(webapp2.RequestHandler):
    """ The base class for SignUpHandler & LogInHandler. """

    def _set_id_cookie(self, email=None, remember_me=False):
        """ Set the user_id information to cookies.
        If @param remember, the cookie will be stored even after browser is closed.
        """
        body = "user_id="
        if email is not None:
            body += encrypt.encode(email)
            if remember_me:
                now = datetime.datetime.utcnow()
                # default, let the cookie live for a week
                delta = datetime.timedelta(days=7)
                expire = now + delta
                body += ("; Expires=" + expire.strftime("%a, %d-%b-%Y %H:%M:%S GMT;"))

        self.response.headers.add_header("Set-Cookie", str(body))


class SignUpHandler(_AuthHandler):
    """ Handler for url "/signup", directs user to register procedures. """

    def get(self):
        """ Display the sign-up page. """
        self._render()

    def post(self):
        """ Handle the sign-up request. """
        email = self.request.get("email")
        pwd = self.request.get("password")
        verify = self.request.get("verify")
        
        # there is verification on browser by JS, but validating again won't hurt
        if not SignUpHandler._validate(email, pwd, verify):
            logging.error("How could the invalid input pass the JS test? @auth.SignUpHandler.post()")
            self.redirect("/signup")
            return
        
        if User.exists(email):
            # telling user that the email has been taken
            self._error("Sorry, but the email has been registered by somebody else.")
        else:
            hashed = encrypt.hash_pwd(email, pwd)
            u = User(email=email, pwd_hashed=hashed)
            try:
                u.put()
            except TransactionFailedError, e:
                # unable to register, display messages to user
                self._error("Sorry, registration failed unexpectedly. Please try again later.", e)
                return

            self._set_id_cookie(email)
            # TODO register new user, redirects to welcome page, or redirects to fill personal information
            self.redirect('/')

    def _render(self, dic={}):
        """ Render the sign-up page with @param dic. """
        template = jinja_env.get_template("signup.html")
        self.response.out.write(template.render(dic))

    def _error(self, msg, error=None):
        """ On error, display some message back to user && log it. """
        if error is not None:
            logging.error(error)

        self._render({'email_info': msg})

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


class LogInHandler(_AuthHandler):
    """ Handler for url "/login", directs user to log in. """
    
    def get(self):
        """ Display the log-in page. """
        self._render()

    def post(self):
        """ Handle the log-in request. """
        email = self.request.get('email')
        pwd = self.request.get('password')
        keep_logged_in = self.request.get('keep_logged_in')
        remember_me = (keep_logged_in == 'on')

        u = User.get_by_email(email)
        if u is None:
            # the input email is invalid, no such user
            self._render({'login_error': "No such user."})
        elif encrypt.check_pwd(email, pwd, u.pwd_hashed):
            # log-in success
            self._set_id_cookie(email, remember_me)
            self.redirect('/')
        else:
            # log-in failed
            values = {
                'login_error': "Incorrect password.",
                'email': email,
            }
            if remember_me:
                values['keep_logged_in'] = 'checked'
            self._render(values)

    def _render(self, dic={}):
        """ Render the log-in page with @param dic. """
        template = jinja_env.get_template('login.html')
        self.response.out.write(template.render(dic))


class LogOutHandler(_AuthHandler):
    """ Handler for url '/logout', log out. """

    def get(self):
        """ Handle the log out request """
        self._set_id_cookie()
        self.redirect('/')


app_https = webapp2.WSGIApplication([
    ('/signup/?', SignUpHandler),
    ('/login/?', LogInHandler),
    ('/logout/?', LogOutHandler)
], debug=True)