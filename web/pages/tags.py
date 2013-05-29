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

    # the max fetching amount for one time
    FETCH_LIMIT = 30

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

            start_str = self.request.get('start')
            if start_str:
                try:
                    # count from 0
                    start = int(start_str) - 1
                    if start < 0:
                        start = 0
                except Exception:
                    start = 0
            else:
                start = 0

            context['tag_name'] = tag_name
            context['tag_books'], context['total'] = self._prepare_books(tag_name, start, helper, user)
            context['start'] = start + 1
            context['end'] = len(context['tag_books']) + start - 1 + 1
            context['prev_url'] = self._prepare_prev_url(tag_name, start)
            context['next_url'] = self._prepare_next_url(tag_name, start, context['total'])
        else:
            all = helper.all_by_amount()
            context['tag_names'] = all

        self.response.out.write(template.render(context))
        return

    def _prepare_books(self, tag_name, start, helper, user):
        """ Prepare data to display for a specific tag.
            @param helper: a TagHelper object.
            @returns: ([BookRelated], total), total is the amount of all books in this tag
        """
        isbns = helper.isbns(tag_name)
        end = start + self.FETCH_LIMIT
        to_display = isbns[start:end]
        bs = [books.BookRelated.get_by_user_isbn(user, isbn, load_comment=False) for isbn in to_display]
        return bs, len(isbns)

    def _prepare_prev_url(self, tag_name, start):
        """ Generate the url for the previous FETCH_LIMIT items.
            @param start: counting from 0.
        """
        # in get(), start has been limited to >= 0
        if start == 0:
            return None

        last = start - self.FETCH_LIMIT
        if last < 0:
            last = 0
        base_url = self.request.path
        params = {
            # in the url, counting from 1
            'start': last + 1,
            't': codecs.encode(tag_name, 'utf-8')
        }
        return base_url + '?' + urllib.urlencode(params)

    def _prepare_next_url(self, tag_name, start, length):
        """ Generate the url for the following FETCH_LIMIT items.
            @param start: counting from 0.
            @param length: the total amount of available items.
        """
        next = start + self.FETCH_LIMIT
        if next >= length:
            return None

        base_url = self.request.path
        params = {
            # in the url, counting from 1
            'start': next + 1,
            't': codecs.encode(tag_name, 'utf-8')
        }
        return base_url + '?' + urllib.urlencode(params)
