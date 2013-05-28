'''
@author: Andriy Lin
@description: Displaying all tags or the books in one particular tag.
'''

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

        tag_name = self.request.get('t')
        if tag_name:
            # a specific tag to display
            context['msg'] = tag_name
        else:
            helper = books.TagHelper(user)
            tags = helper.all_by_amount()
            context['tags'] = tags

        self.response.out.write(template.render(context))
        return
