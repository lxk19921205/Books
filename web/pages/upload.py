'''
@author: Andriy Lin
@description: Handling "/upload", importing data from local files
'''

import urllib
import codecs
import json
import webapp2
from google.appengine.ext import deferred

import utils
import auth
from api import local
from api import douban


def _upload_worker(user_key, id_tags):
    """ Called in Task Queue, for adding books to douban's Wish List.
        @param user_key: DO NOT pass the user, otherwise it would raise exceptions (due to cache??)
        @param id_tags: a list of (douban, tag_string)
    """
    user = auth.user.User.get(user_key)
    count = 0
    for (douban_id, tag_string) in id_tags:
        response = douban.upload_book(user, douban_id, tag_string)
        obj = json.loads(response.content)
        if obj.get('code') == '111' or obj.get('code') == 111:
            # it may fail, due to rate limit or something, no need to try any further
            return
            raise ValueError("Wait longer, uploaded: " + count)
        else:
            count += 1
    return


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
        if not user:
            self.redirect('/login')
            return

        if not user.is_douban_connected():
            self.redirect('/auth/douban')
            return

        data = codecs.decode(self.request.get('file'), 'utf-8')
        # get a list of (douban_id, tags)
        id_tags = local.parse(data)
        deferred.defer(_upload_worker, user.key(), id_tags)

        params = {
            'msg': 'Upload finished, parsing & syncing now.'
        }
        self.redirect('/upload?' + urllib.urlencode(params))
        return
