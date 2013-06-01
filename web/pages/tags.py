'''
@author: Andriy Lin
@description: Displaying all tags or the books in one particular tag.
'''

import datetime
import urllib
import codecs
import webapp2

import utils
import auth
import books
from books import booklist
from books.elements import Tags


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

            self._render_tag_books(user, tag_name, helper, context)
        else:
            self._render_tags_info(user, helper, context)

        self.response.out.write(template.render(context))
        return

    def _render_tags_info(self, user, helper, ctx):
        """ Prepare to display the all tags, top tags, and the tags recently being used.
            @param user: the relevant user.
            @param helper: a TagHelper object utilizing memcache.
            @param ctx: a {} to fill, putting data that needs to be rendered.
        """
        # all tags
        all = helper.all_by_amount()
        ctx['tag_names'] = all

        # top tags
        tags = helper.all_by_amount()
        ctx['top_tags'] = [(p[0], len(p[1])) for p in tags[:10]]

        # tags recently being used
        current = datetime.datetime.now()
        month_delta = datetime.timedelta(days=30)
        one_month_ago = current - month_delta

        done_list = booklist.BookList.get_or_create(user, booklist.LIST_DONE)
        month_list = done_list.isbns_after(one_month_ago)
        tags = Tags.get_by_isbns(user, month_list)
        names_dict = {}
        for t in tags:
            for name in t.names:
                if name in names_dict:
                    names_dict[name] += 1
                else:
                    names_dict[name] = 1
        pairs = sorted(names_dict.items(),
                       key=lambda p: p[1],
                       reverse=True)
        ctx['recent_tags'] = pairs
        return

    def _render_tag_books(self, user, tag_name, helper, ctx):
        """ Given a specific tag, render its relevant books.
            @param user: the relevant user.
            @param tag_name: the given tag name.
            @param helper: a TagHelper object that utilizes memcache.
            @param ctx: a {} to fill, putting data that needs to be rendered.
        """
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

        ctx['tag_name'] = tag_name
        ctx['tag_books'], ctx['total'] = self._prepare_books(tag_name, start, helper, user)
        ctx['start'] = start + 1
        ctx['end'] = len(ctx['tag_books']) + start - 1 + 1
        ctx['prev_url'] = self._prepare_prev_url(tag_name, start)
        ctx['next_url'] = self._prepare_next_url(tag_name, start, ctx['total'])
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
