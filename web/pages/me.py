'''
@author: Andriy Lin
@description: The handler for the page of displaying user's information & settings
'''

import datetime
import webapp2

import auth
import utils
from books import booklist


class MeHandler(webapp2.RequestHandler):
    """ Handling '/me' or '/me/' """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        if not user:
            self.redirect('/login')
            return

        template = utils.get_jinja_env().get_template("me.html")
        context = {
            'user': user
        }

        self._collect(context, user)
        self.response.out.write(template.render(context))
        return

    def _collect(self, ctx, user):
        """ Collect user statistics.
            @param ctx: fill the figures into this dictionary.
            @param user: the corresponding user.
        """
        interested_list = booklist.BookList.get_or_create(user, booklist.LIST_INTERESTED)
        ctx['interested_amount'] = interested_list.size()

        reading_list = booklist.BookList.get_or_create(user, booklist.LIST_READING)
        ctx['reading_amount'] = reading_list.size()

        done_list = booklist.BookList.get_or_create(user, booklist.LIST_DONE)
        ctx['done_amount'] = done_list.size()

        (current, one_week_ago, one_month_ago, one_year_ago) = self._generate_past_time()
        month_list = done_list.isbns_after(one_month_ago)
        ctx['week_amount'] = len(done_list.isbns_after(one_week_ago))
        ctx['month_amount'] = len(month_list)
        ctx['year_amount'] = len(done_list.isbns_after(one_year_ago))
        ctx['current_time'] = current.strftime("%Y-%m-%d %H:%M:%S")

        return

    def _generate_past_time(self):
        """ @returns: (now, a_week_ago, a_month_ago, a_year_ago)
            Each one is a datetime object.
        """
        current = datetime.datetime.now()

        week_delta = datetime.timedelta(days=7)
        month_delta = datetime.timedelta(days=30)
        year_delta = datetime.timedelta(days=365)
        return (current, current - week_delta, current - month_delta, current - year_delta)

    def post(self):
        """ Currently, only disconnecting from douban. """
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        if not user:
            self.redirect('/login')
            return

        if user.is_douban_connected():
            user.disconnect_from_douban()

        self.redirect('/me')
        return
