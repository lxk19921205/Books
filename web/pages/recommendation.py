'''
@author: Andriy Lin
@description: Containing handlers for pages in Explore section
    1. Random!
'''

import random
import webapp2
import urllib

import utils
import auth
import books
from books import booklist
from books import BookRelated
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
        b = books.book.Book.get_by_douban_id(book_id)
        if b:
            self.redirect('/book/%s' % b.isbn)
            return

        if self.user.is_douban_connected():
            self._try_fetch_render(book_id)
        else:
            self.redirect('/auth/douban')
        return

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
        return
    # end of self.display()

    def _render_no_such_book(self, douban_id):
        """ Render a NO SUCH BOOK msg onto web page. Including the corresponding douban_id """
        template = utils.get_jinja_env().get_template("random.html")
        context = {
            'douban_id': douban_id,
            'user': self.user
        }
        self.response.out.write(template.render(context))
        return
# end of RandomHandler


class WhatsNextHandler(webapp2.RequestHandler):
    """ Handling the real request to recommend in Interested list. """

    # at most pick 3 books for recommendation at one time
    NEXT_LIMIT = 3

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        if not user:
            self.redirect('/login')
            return

        template = utils.get_jinja_env().get_template('whatsnext.html')
        ctx = {'user': user}

        bl = booklist.BookList.get_or_create(user, booklist.LIST_INTERESTED)
        if bl.size() == 0:
            # no books in interested list
            ctx['no_books'] = True
        else:
            # recommend next
            ctx['no_books'] = False
            self._prepare_next(ctx, user, bl)

        self.response.out.write(template.render(ctx))
        return

    def _prepare_next(self, ctx, user, bl):
        """ Generate the recommendation results (at most 3) for reading next.
            @param ctx: the {} object to fill and render onto page.
            @param user: the corresponding user.
            @param bl: the Interested list (not empty).
        """
        r = random.random()
        if r <= 0.1:
            # 10% chances to randomly pick three...
            ctx['reason'] = "randomly picked"
            isbns = bl.isbns()
            max_amount = min(self.NEXT_LIMIT, len(isbns))
            result_isbns = random.sample(isbns, max_amount)
        else:
            # TODO: default case is most recently added?
            # TODO: also, it doesn't sort by updated time here
            ctx['reason'] = "recently added"
            result_isbns = bl.isbns()[:self.NEXT_LIMIT]

        ctx['next_books'] = [BookRelated.get_by_user_isbn(user, isbn, load_comment=False) for isbn in result_isbns]
        ctx['list_amount'] = bl.size()
        ctx['picked_amount'] = len(ctx['next_books'])
        return
# end of class WhatsNextHandler


class RecommendationHandler(webapp2.RequestHandler):
    """ Handling the real recommendation request. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)

        template = utils.get_jinja_env().get_template('base_nav.html')
        context = {'user': user}
        self.response.out.write(template.render(context))
        return
# end of class RecommendationHandler
