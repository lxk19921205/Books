'''
@author: Andriy Lin
@description: The handler for 404-Not-Found page
'''

import webapp2

import utils
import auth


class NotFoundHandler(webapp2.RequestHandler):
    """ 404 Not Found. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if email:
            user = auth.user.User.get_by_email(email)
        else:
            user = None

        template = utils.get_jinja_env().get_template('404.html')
        context = {
            'user': user
        }
        self.response.out.write(template.render(context))
