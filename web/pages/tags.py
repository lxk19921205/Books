'''
@author: Andriy Lin
@description: Handling "/tags"
'''

import webapp2

import utils
import auth


class TagsHandler(webapp2.RequestHandler):
    """ Handling the requests for '/tags'. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        
        template = utils.get_jinja_env().get_template('base_nav.html')
        context = {'user': user}
        self.response.out.write(template.render(context))
