'''
@author: Andriy Lin
@description: When error occurs, it should come to this page
'''

import webapp2
import utils

class ErrorHandler(webapp2.RequestHandler):
    """ Handler for "/error?msg=xxx" """

    def get(self):
        msg = self.request.get("msg")
        template = utils.get_jinja_env().get_template("error.html")
        context = {'msg': msg}
        self.response.out.write(template.render(context))
