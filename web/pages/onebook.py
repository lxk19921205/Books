'''
@author: Andriy Lin
@description: Displaying a particular book.
'''

import urllib
import webapp2
import logging

import utils
import auth
import books
from api import douban
from api import tongji
from books.book import Book
from books.booklist import BookList
from books import elements
from books import TagHelper


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

        reload = self.request.get('reload') == 'True'
        if reload:
            # force to reload from douban..
            try:
                full = self._load(user, isbn, reload=True, tjlib=True)
            except Exception as err:
                params = {'msg': err}
                self.redirect('/error?%s' % urllib.urlencode(params))
                return
        else:
            full = self._load(user, isbn, reload=False)
            if full.is_empty():
                # no such data in local datastore, try fetch
                try:
                    full = self._load(user, isbn, reload=True, tjlib=True)
                except Exception as err:
                    params = {'msg': err}
                    self.redirect('/error?%s' % urllib.urlencode(params))
                    return

        context['title'] = full.book.title
        context['book'] = full.book
        context['booklist_name'] = full.booklist_name
        context['rating'] = full.rating
        context['tags'] = full.tags
        context['comment'] = full.comment

        self.response.out.write(template.render(context))
        return

    def _load(self, user, isbn, reload, tjlib=False):
        """ Load a book from datastore or from douban.
            @param reload: directly load from douban, no matter whether there is in datastore.
            @param tjlib: whether to also load Tongji Library status when reloading.
            @return: a BookRelated object
        """
        if not reload:
            # everything here
            return books.BookRelated.get_by_user_isbn(user, isbn)

        basic_book = douban.get_book_by_isbn(isbn)
        full = douban.get_book_all_by_id(basic_book.douban_id, user)
        # douban API may have a bug: not providing summary somehow
        full.book.summary = basic_book.summary
        full.merge_into_datastore(user)

        if tjlib:
            url, datas = tongji.get_by_isbn(isbn)
            full.book.set_tongji_info(url, datas)

        return full

    def post(self):
        """ Handling requests for editing data. """
        email = auth.get_email_from_cookies(self.request.cookies)
        self.user = auth.user.User.get_by_email(email)
        if not self.user:
            self.redirect('/login')
            return

        self.isbn = self.request.path.split('/book/')[1]
        try:
            utils.validate_isbn(self.isbn)
        except Exception:
            msg = "Invalid ISBN: " + self.isbn
            params = {'msg': msg}
            self.redirect('/error?' + urllib.urlencode(params))
            return

        if not self.user.is_douban_connected():
            self.redirect('/auth/douban')
            return

        edit_type = self.request.get('type')

        # the booklists this book was previously in
        from_lists = [bl for bl in BookList.get_all_booklists(self.user) if self.isbn in bl.isbns()]

        if edit_type == 'booklist':
            self._edit_booklist(from_lists)
            self._finish_editing()
            return

        self.edited = False
        if edit_type == 'rating':
            self._edit_rating()
        elif edit_type == 'comment':
            self._edit_comment()
        elif edit_type == 'tags':
            self._edit_tags()
        elif edit_type == 'tongji':
            self._edit_tongji()

        if self.edited:
            if from_lists:
                # already in some lists, now edited, sync to douban, edit
                self._sync_edit("PUT")
            else:
                # previously not in any list, now edited, add it to Done List
                done_list = BookList.get_or_create(self.user, books.booklist.LIST_DONE)
                done_list.add_isbn(self.isbn, front=True)
                # sync to douban, add
                self._sync_edit("POST")

        self._finish_editing()
    # end of post()

    def _edit_booklist(self, from_lists):
        """ Change or delete belonging booklist.
            @param from_lists: The booklists this book was previously in.
        """
        target_list_name = self.request.get('booklist')
        if target_list_name:
            if target_list_name == "remove":
                # remove from any booklists
                for bl in from_lists:
                    bl.remove_isbn(self.isbn)

                # also remove any Rating, Tags, Comment
                r = elements.Rating.get_by_user_isbn(self.user, self.isbn)
                if r:
                    r.delete()
                t = elements.Tags.get_by_user_isbn(self.user, self.isbn)
                if t:
                    t.delete()
                c = elements.Comment.get_by_user_isbn(self.user, self.isbn)
                if c:
                    c.delete()

                # sync memcache
                helper = books.SortHelper(self.user)
                helper.delete(self.isbn)

                # sync to douban, delete all related
                self._sync_edit("DELETE")
            else:
                # change to one booklist
                target_list = BookList.get_or_create(self.user, target_list_name)
                if from_lists:
                    for bl in from_lists:
                        bl.remove_isbn(self.isbn)
                    target_list.add_isbn(self.isbn, front=True)
                    # sync to douban, modify
                    self._sync_edit("PUT")
                else:
                    target_list.add_isbn(self.isbn, front=True)
                    # sync to douban, add
                    self._sync_edit("POST")

                # sync memcache
                helper = books.SortHelper(self.user)
                helper.set_by_isbn(target_list_name, self.isbn)
        return

    def _edit_rating(self):
        rating_str = self.request.get('rating')
        if rating_str:
            self.edited = True
            r = elements.Rating.get_by_user_isbn(self.user, self.isbn)
            try:
                rating_num = int(rating_str)
            except Exception:
                logging.error("Error parsing the str for Rating: " + rating_str)
                return

            helper = books.SortHelper(self.user)
            if rating_num == 0:
                # 0 means clear
                r.delete()
                helper.delete_user_rating(self.isbn)
            else:
                if r:
                    r.score = rating_num
                    r.max_score = 5
                    r.min_score = 0
                else:
                    r = elements.Rating(user=self.user, isbn=self.isbn,
                                        parent=utils.get_key_private("Rating", self.user),
                                        score=rating_num, max_score=5, min_score=0)
                r.put()
                helper.set_user_rating(self.isbn, r.score)
        return

    def _edit_comment(self):
        comment_str = self.request.get('comment')
        self.edited = True
        if comment_str:
            c = elements.Comment.get_by_user_isbn(self.user, self.isbn)
            if c:
                c.comment = comment_str
            else:
                c = elements.Comment(user=self.user, isbn=self.isbn,
                                     parent=utils.get_key_private('Comment', self.user),
                                     comment=comment_str)
            c.put()
        else:
            # to delete any comment
            c = elements.Comment.get_by_user_isbn(self.user, self.isbn)
            if c:
                c.delete()
        return

    def _edit_tags(self):
        tags_str = self.request.get('tags')
        self.edited = True
        helper = TagHelper(self.user)
        if tags_str:
            # remove duplication
            src = tags_str.split(' ')
            tags_arr = []
            for t in src:
                if t and t not in tags_arr:
                    tags_arr.append(t)

            tags = elements.Tags.get_by_user_isbn(self.user, self.isbn)
            if tags:
                for name in tags.names:
                    helper.remove(name, tags.isbn)
                for name in tags_arr:
                    helper.add(name, tags.isbn)
                tags.names = tags_arr
            else:
                tags = elements.Tags(user=self.user, isbn=self.isbn,
                                     parent=utils.get_key_private('Tags', self.user),
                                     names=tags_arr)
                for name in tags_arr:
                    helper.add(name, self.isbn)
            tags.put()
        else:
            # to delete any tags
            t = elements.Tags.get_by_user_isbn(self.user, self.isbn)
            if t:
                t.delete()
                for name in t.names:
                    helper.remove(name, t.isbn)
        # end of tags

    def _edit_tongji(self):
        # no need to set self.edited to True, because this doesn't need sync to douban
        try:
            url, datas = tongji.get_by_isbn(self.isbn)
            b = Book.get_by_isbn(self.isbn)
            b.set_tongji_info(url, datas)
        except Exception:
            # there may be errors, like this book 9787544717731, it also has e-version in TJ Lib..
            pass

    def _finish_editing(self):
        """ When finish editing, refresh the current page. """
        self.redirect(self.request.path)

    def _sync_edit(self, method):
        """ Sync the edit done to this book to douban.
            @param method: "POST" for add, "PUT" for edit, "DELETE" for delete
        """
        if method != "POST" and method != "PUT" and method != "DELETE":
            raise ValueError("@param method shall be among 'POST', 'PUT', or 'DELETE'.")

        book_id = books.book.Book.get_by_isbn(self.isbn).douban_id
        if method == "POST":
            r = books.BookRelated.get_by_user_isbn(self.user, self.isbn, load_book=False)
        elif method == "PUT":
            r = books.BookRelated.get_by_user_isbn(self.user, self.isbn, load_book=False)
        elif method == "DELETE":
            r = books.BookRelated()

        douban.edit_book(book_id, self.user, r, method)
    # end of _sync_edit()
