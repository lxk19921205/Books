'''
@author: Andriy Lin
@description: Containing handlers for pages in Explore section
    1. Random!
'''

import webapp2
import urllib

import utils
import auth
import books
import api.douban as douban


class RandomHandler(webapp2.RequestHandler):
    """ Handling url "recommendation/random", randomly pick a book from douban and present it. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        self.user = auth.User.get_by_email(email)
        if not self.user:
            self.redirect('/login')
            return

        book_id = utils.random_book_id()
        book_id = "2535044"
        b = books.book.Book.get_by_douban_id(book_id)
        if b:
            self.redirect('/book/%s' % b.isbn)
            return

        if self.user.is_douban_connected():
            self._try_fetch_render(book_id)
        else:
            self.redirect('/auth/douban')

    def _try_fetch_render(self, douban_id):
        """ Try fetching a book from douban.
            If no exception raised, render it.
        """
        try:
            b = douban.get_book_all_by_id(douban_id, self.user)
            b.merge_into_datastore(self.user)
        except utils.errors.FetchDataError:
            # No such book, display its original link
            self._render_no_such_book(douban_id)
        except utils.errors.ParseJsonError:
            # This is something I should care about, some cases are not covered
            msg = "Error PARSING book information of douban_id: " + douban_id
            url = "/error?" + urllib.urlencode({'msg': msg})
            self.redirect(url)
        else:
            self.redirect('/book/%s' % b.book.isbn)
    # end of self.display()

    def _render_no_such_book(self, douban_id):
        """ Render a NO SUCH BOOK msg onto web page. Including the corresponding douban_id """
        template = utils.get_jinja_env().get_template("random.html")
        context = {
            'douban_id': douban_id,
            'user': self.user
        }
        self.response.out.write(template.render(context))

# end of RandomHandler


class RecommendationHandler(webapp2.RequestHandler):
    """ Handling the real recommendation request. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)

        template = utils.get_jinja_env().get_template('base_nav.html')
        context = {'user': user}
        self.response.out.write(template.render(context))


class WhatsNextHandler(webapp2.RequestHandler):
    """ Handling the real request to recommend in Interested list. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)

        template = utils.get_jinja_env().get_template('base_nav.html')
        context = {'user': user}
        self.response.out.write(template.render(context))
