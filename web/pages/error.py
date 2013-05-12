'''
@author: Andriy Lin
@description: When error occurs, it should come to this page
'''

import webapp2

import utils
import auth


class ErrorHandler(webapp2.RequestHandler):
    """ Handler for "/error?msg=xxx" """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if email:
            user = auth.user.User.get_by_email(email)
        else:
            user = None

        msg = self.request.get("msg")
        template = utils.get_jinja_env().get_template("error.html")
        context = {
            'msg': msg,
            'user': user
        }
        self.response.out.write(template.render(context))
