'''
@author: Andriy Lin
@description: The handler for the page of displaying user's information & settings
'''

import webapp2

import auth
import utils


class MeHandler(webapp2.RequestHandler):
    """ Handling '/me' or '/me/' """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if not email:
            self.redirect('/login')
            return

        template = utils.get_jinja_env().get_template("me.html")
        context = {
            'user': auth.user.User.get_by_email(email)
        }
        self.response.out.write(template.render(context))
