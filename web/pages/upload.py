'''
@author: Andriy Lin
@description: Handling "/upload", importing data from local files
'''

import webapp2
import urllib
import codecs

import utils
import auth
from api import local


class UploadHandler(webapp2.RequestHandler):
    """ Handling the requests for '/upload'. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)

        if not user:
            self.redirect('/login')
            return

        template = utils.get_jinja_env().get_template('upload.html')
        context = {
            'user': user
        }
        context['msg'] = self.request.get('msg')

        self.response.out.write(template.render(context))
        return

    def post(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)

        template = utils.get_jinja_env().get_template('upload.html')
        context = {
            'user': user
        }

        data = codecs.decode(self.request.get('file'), 'utf-8')
        # get a list of (douban_id, tags)
        id_tags = local.parse(data)
        context['msg'] = id_tags

        self.response.out.write(template.render(context))
        return

        params = {
            'msg': 'Upload finished, parsing & syncing now.'
        }
        self.redirect('/upload?' + urllib.urlencode(params))
        return
