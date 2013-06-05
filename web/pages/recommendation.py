'''
@author: Andriy Lin
@description: Containing handlers for pages in Explore section
    1. Random!
'''

from math import log10
import datetime
import random
import webapp2
import urllib

import utils
import auth
import books
from books import booklist
from books import BookRelated
from books import SortHelper
from books import TagHelper
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

    # when read books exceeding this limit for the past month,
    # it will take pages amount into consideration in recommendation procedures.
    # make it an integer here >.< ..
    PAGE_THRESHHOLD = 512

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
        if r <= 0.15:
            # 15% chances to randomly pick three...
            ctx['reason'] = "randomly picked"
            result_isbns = self._all_random(bl)
        elif r > 0.15 and r <= 0.3:
            # 15% chances to recommend books recently added as interested
            ctx['reason'] = "recently added"
            result_isbns = self._recently_added(bl, user)
        else:
            # 70% chances to calculate each book's score and recommend the highest ones
            ctx['reason'] = "praised by others"
            result_isbns = self._being_praised(user)

        raw_src = [BookRelated.get_by_user_isbn(user, isbn, load_comment=False) for isbn in result_isbns]
        # put those in TJ library first
        in_tj = []
        not_in_tj = []
        for src in raw_src:
            if src.book.is_tongji_linked():
                in_tj.append(src)
            else:
                not_in_tj.append(src)
        ctx['next_books'] = in_tj + not_in_tj

        ctx['list_amount'] = bl.size()
        ctx['picked_amount'] = len(ctx['next_books'])
        return

    def _all_random(self, bl):
        """ @returns: a list of all randomly picked isbns. """
        isbns = bl.isbns()
        max_amount = min(self.NEXT_LIMIT, len(isbns))
        return random.sample(isbns, max_amount)

    def _recently_added(self, bl, user):
        """ Filtering key point: recently added.
            If more than self.NEXT_LIMIT books available, randomly pick some
            Otherwise, pick enough ones by the updated time
            @returns: a list of isbns
        """
        now = datetime.datetime.now()
        dt = datetime.timedelta(days=30)
        one_month_ago = now - dt
        month_list = bl.isbns_after(one_month_ago)

        if len(month_list) >= self.NEXT_LIMIT:
            # enough books for random
            return random.sample(month_list, self.NEXT_LIMIT)

        # otherwise, pick enough ones by the updated time
        helper = SortHelper(user)
        sorted_isbns = helper.by_updated_time(booklist.LIST_INTERESTED)
        return sorted_isbns[:self.NEXT_LIMIT]

    def _being_praised(self, user):
        """ Filtering by calculating scores of each book. """
        def _rating_weight(rating_score):
            """ Return the relative weight of a rating score.
                @param rating_score: In 10 points scale.
            """
            if rating_score < 6.0:
                base = -2
            elif rating_score < 7.0:
                base = -1
            elif rating_score < 7.5:
                base = 0
            elif rating_score < 7.8:
                base = 0.3
            elif rating_score < 8.0:
                base = 0.6
            elif rating_score < 8.3:
                base = 0.9
            elif rating_score < 8.5:
                base = 1.2
            elif rating_score < 8.8:
                base = 1.5
            elif rating_score < 9.0:
                base = 1.8
            else:
                base = 2
            return base + random.random()

        def _voted_weight(amount):
            """ @returns: the relative weight of rated_amount.
                Generally, the larger it is, the more it's rating can present.
            """
            if amount <= 0:
                base = -2
            elif amount < 64:
                base = -1
            else:
                # too many is also useless
                amount = max(amount, 10000)
                base = log10(amount)
            return base + random.random()

        def _pages_weight(pages):
            """ @returns: the relative weight of pages of a book.
                Generally, if pages is larger than a threshhold, it become bad.
            """
            if pages > self.PAGE_THRESHHOLD:
                return -1
            else:
                return 1

        helper = SortHelper(user)
        now = datetime.datetime.now()
        dt = datetime.timedelta(days=30)
        one_month_ago = now - dt

        datas = helper.all(booklist.LIST_DONE)
        consider_pages = False
        for d in sorted(datas, key=lambda sd: sd.updated_time, reverse=True):
            if d.updated_time < one_month_ago:
                break
            if d.pages > self.PAGE_THRESHHOLD:
                consider_pages = True
                break

        tag_helper = TagHelper(user)
        week_goals = tag_helper.isbns('thisweek')
        month_goals = tag_helper.isbns('thismonth')

        def _calculate(data):
            """ Calculate the score of that data.
                @param consider_pages: whether to take pages into account. Default is False.
            """
            r = _rating_weight(data.public_rating)
            v = _voted_weight(data.rated_amount)
            score = r * v
            if consider_pages:
                score += _pages_weight(data.pages)
            if data.isbn in week_goals or data.isbn in month_goals:
                score += 16 * random.random()
            return score

        datas = helper.all(booklist.LIST_INTERESTED)
        sorted_datas = sorted(datas, key=_calculate, reverse=True)
        return [d.isbn for d in sorted_datas[:self.NEXT_LIMIT]]
# end of class WhatsNextHandler


class RecommendationHandler(webapp2.RequestHandler):
    """ Handling the real recommendation request. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        if not user:
            self.redirect('/login')
            return

        template = utils.get_jinja_env().get_template('guess.html')
        context = {'user': user}

        self._fill(context, user)
        self.response.out.write(template.render(context))
        return

    def _fill(self, ctx, user):
        """ Fill the context for rendering. """
        def _load(isbn):
            """ Loading from datastore. """
            return BookRelated.get_by_user_isbn(user, isbn,
                                                load_booklist_related=False,
                                                load_rating=False,
                                                load_tags=False,
                                                load_comment=False)

        # hardcoded here... only for defense
        isbns = ["9787229058883", "9787115276117", "9780130305527"]
        ctx['recommendation_results'] = [_load(isbn) for isbn in isbns]
        return

# end of class RecommendationHandler
