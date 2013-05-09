'''
@author: Andriy Lin
@description: The handler for 404-Not-Found page
'''

import webapp2

import utils


class NotFoundHandler(webapp2.RequestHandler):
    """ 404 Not Found. """

    def get(self):
        jinja_env = utils.get_jinja_env()
        template = jinja_env.get_template('404.html')
        self.response.out.write(template.render({}))
