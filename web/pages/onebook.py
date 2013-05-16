'''
@author: Andriy Lin
@description: Displaying a particular book.
'''

import urllib
import webapp2

import utils
import auth
import books
from api import douban
from books.booklist import BookList
from books import elements


class OneBookHandler(webapp2.RequestHandler):
    """ Handling requests for a particular book. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        if not user:
            self.redirect('/login')
            return

        isbn = self.request.path.split('/book/')[1]
        try:
            utils.validate_isbn(isbn)
        except Exception:
            msg = "Invalid ISBN: " + isbn
            params = {'msg': msg}
            self.redirect('/error?' + urllib.urlencode(params))
            return

        template = utils.get_jinja_env().get_template('onebook.html')
        context = {
            'user': user
        }

        full = books.BookRelated.get_by_user_isbn(user, isbn)
        if full.book:
            context['title'] = full.book.title
            context['book'] = full.book
        else:
            try:
                full.book = douban.get_book_by_isbn(isbn)
                full.book.put()
            except utils.errors.FetchDataError as err:
                params = {'msg': err}
                self.redirect('/error?%s' % urllib.urlencode(params))
                return
            except utils.errors.ParseJsonError as err:
                params = {'msg': err}
                self.redirect('/error?%s' % urllib.urlencode(params))
                return
            else:
                context['title'] = full.book.title
                context['book'] = full.book

        context['booklist_name'] = full.booklist_name
        context['rating'] = full.rating
        context['tags'] = full.tags
        context['comment'] = full.comment

        self.response.out.write(template.render(context))

    def post(self):
        """ Handling requests for editing data. """
        email = auth.get_email_from_cookies(self.request.cookies)
        user = auth.user.User.get_by_email(email)
        if not user:
            self.redirect('/login')
            return

        isbn = self.request.path.split('/book/')[1]
        try:
            utils.validate_isbn(isbn)
        except Exception:
            msg = "Invalid ISBN: " + isbn
            params = {'msg': msg}
            self.redirect('/error?' + urllib.urlencode(params))
            return

        edit_type = self.request.get('type')
        if edit_type == 'booklist':
            target_list_name = self.request.get('booklist')
            if target_list_name:
                bls = BookList.get_all_booklists(user)
                if target_list_name == "remove":
                    # remove from any booklists
                    for bl in bls:
                        if isbn in bl.isbns:
                            bl.remove_isbn(isbn)
                else:
                    # change to one booklist
                    from_lists = [bl for bl in bls if isbn in bl.isbns]
                    target_list = BookList.get_or_create(user, target_list_name)

                    if from_lists:
                        for bl in from_lists:
                            # in case that the book is in many booklists..
                            bl.remove_isbn(isbn)

                    target_list.add_isbn(isbn, front=True)
            # end of booklist


        if edit_type == 'rating':
            rating_str = self.request.get('rating')
            if rating_str:
                r = elements.Rating.get_by_user_isbn(user, isbn)
                if rating_str == "clear":
                    if r:
                        r.delete()
                else:
                    try:
                        rating_num = int(rating_str)
                    except Exception:
                        pass
                    else:
                        if r:
                            r.score = rating_num
                            r.max_score = 5
                            r.min_score = 0
                        else:
                            r = elements.Rating(user=user, isbn=isbn,
                                                parent=utils.get_key_book(),
                                                score=rating_num, max_score=5, min_score=0)
                        r.put()
            # end of rating
        elif edit_type == 'comment':
            comment_str = self.request.get('comment')
            if comment_str:
                c = elements.Comment.get_by_user_isbn(user, isbn)
                if c:
                    c.comment = comment_str
                else:
                    c = elements.Comment(user=user, isbn=isbn,
                                         parent=utils.get_key_book(),
                                         comment=comment_str)
                c.put()
            else:
                # to delete any comment
                c = elements.Comment.get_by_user_isbn(user, isbn)
                if c:
                    c.delete()
            # end of comment
        elif edit_type == 'tags':
            tags_str = self.request.get('tags')
            if tags_str:
                tags_arr = tags_str.split(' ')
                tags = elements.Tags.get_by_user_isbn(user, isbn)
                if tags:
                    tags.names = tags_arr
                else:
                    tags = elements.Tags(user=user, isbn=isbn,
                                         parent=utils.get_key_book(),
                                         names=tags_arr)
                tags.put()
            else:
                # to delete any tags
                t = elements.Tags.get_by_user_isbn(user, isbn)
                if t:
                    t.delete()
            # end of tags

        self.redirect(self.request.path)
    # end of post()
