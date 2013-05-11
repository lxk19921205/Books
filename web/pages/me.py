'''
@author: Andriy Lin
@description: The handler for the page of displaying user's information & settings
'''

import webapp2

import auth
import utils


class MeHandler(webapp2.RequestHandler):
    """ Handling '/me' or '/me/' """

    def _output(self, name, value):
        self.html += unicode(name + ": ")
        self.html += unicode(value)
        self.html += u'<br/>'

    def _output_link(self, name, link):
        self.html += u"<a href='%s'>%s</a>" % (link, name)
        self.html += u'<br/>'

    def _output_image(self, link):
        self.html += "<img src='%s'/>" % link
        self.html += '<br/>'

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if not email:
            self.redirect('/login')
            return

        user = auth.user.User.get_by_email(email)
        self.html = ""

        self._output('Email', user.email)
        self._output('Douban id', user.douban_id)
        self._output('Douban uid', user.douban_uid)
        self._output('Douban name', user.douban_name)
        self._output_image(user.douban_image)
        self._output_link('URL', user.douban_url)
        self._output('Signature', user.douban_signature)
        self._output('Description', user.douban_description)
        self._output('Created at', user.douban_created_time)

#         jinja_env = utils.get_jinja_env()
        import os
        import jinja2
        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.realpath("./static/html/")),
                               autoescape=False)
        template = jinja_env.get_template("me.html")
        context = {
            'user': user,
            'html': self.html
        }
        self.response.out.write(template.render(context))
