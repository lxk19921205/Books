'''
@author: Andriy Lin
@description: Displaying all tags or the books in one particular tag.
'''

import urllib
import codecs
import webapp2

import utils
import auth
import books


class TagsHandler(webapp2.RequestHandler):
    """ Handling the requests for '/tags'. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        if not user:
            self.redirect('/login')
            return

        template = utils.get_jinja_env().get_template('tags.html')
        context = {'user': user}
        helper = books.TagHelper(user)

        tag_name = self.request.get('t')
        if tag_name:
            # a specific tag to display
            isbns = helper.isbns(tag_name)
            if isbns is None:
                params = {
                    'msg': 'Invalid tag name: "' + codecs.encode(tag_name, 'utf-8') + '"'
                }
                self.redirect('/error?' + urllib.urlencode(params))
                return

            context['tag_name'] = tag_name
            context['tag_books'] = self._prepare_books(tag_name, helper, user)
        else:
            all = helper.all_by_amount()
            context['tag_names'] = all

        self.response.out.write(template.render(context))
        return

    def _prepare_books(self, tag_name, helper, user):
        """ Prepare data to display for a specific tag.
            @param helper: a TagHelper object.
        """
        isbns = helper.isbns(tag_name)
        return [books.BookRelated.get_by_user_isbn(user, isbn, load_comment=False) for isbn in isbns]
