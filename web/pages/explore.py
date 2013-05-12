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


class RandomOneHandler(webapp2.RequestHandler):
    """ Handling url "explore/random", randomly pick a book from douban and present it. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if email:
            self.user = auth.User.get_by_email(email)
            book_id = utils.random_book_id()
#            book_id = "3597031"
#            book_id = "4782867"
            b = books.book.Book.get_by_douban_id(book_id)
            if b is None:
                self._try_fetch_render(book_id)
            else:
                self._render_book(b)
        else:
            self.redirect('/login')

    def _try_fetch_render(self, douban_id):
        """ Try fetching a book from douban. If no exception raised, render it.  """
        try:
            b = douban.get_book_by_id(douban_id)
        except utils.errors.FetchDataError:
            # No such book, display its original link
            self._render_no_such_book(douban_id)
        except utils.errors.ParseJsonError:
            # This is something I should care about, some cases are not covered
            msg = "Error PARSING book information of douban_id: " + douban_id
            url = "/error?" + urllib.urlencode({'msg': msg})
            self.redirect(url)
        else:
            b.put()
            self._render_book(b)
    # end of self.display()

    def _render_no_such_book(self, douban_id):
        """ Render a NO SUCH BOOK msg onto web page. Including the corresponding douban_id """
        template = utils.get_jinja_env().get_template("random.html")
        context = {
            'douban_id': douban_id,
            'user': self.user
        }
        self.response.out.write(template.render(context))

    def _render_book(self, b):
        """ Render a book onto web page. """
        template = utils.get_jinja_env().get_template("random.html")
        context = {
            'book': b,
            'user': self.user
        }
        self.response.out.write(template.render(context))
    # end of self._render_book(b)

# end of RandomOneHandler
