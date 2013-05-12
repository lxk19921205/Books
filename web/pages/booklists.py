'''
@author: Andriy Lin
@description: Handlers for manipulating book lists
'''

import webapp2

import utils
import auth
import api.douban as douban
import books.book as book
import books.booklist as booklist


class _BookListHandler(webapp2.RequestHandler):
    """ The base handler for all the Book list handler. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if email:
            user = auth.user.User.get_by_email(email)
            
            import jinja2
            import os
            jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.realpath("./static/html/")))
            template = jinja_env.get_template("booklist.html")

#             template = utils.get_jinja_env().get_template("booklist.html")
            context = {
                'user': user,
                'title': self.title,
                'active_nav': self.active_nav,
                'books': self._prepare_books(user)
            }
            self.response.out.write(template.render(context))
        else:
            self.redirect('/login')

    def _prepare_books(self, user):
        """ For subclasses to override, specifying data source, return the books in this list. """
        raise NotImplementedError()


class ReadingListHandler(_BookListHandler):
    title = "Reading List"
    active_nav = "Reading"

    def _prepare_books(self, user):
        if not user.is_douban_connected():
            self.redirect('/auth/douban')
            return
        else:
            uid = user.douban_uid
            # TODO just get the Interested list for debugging
            books = douban.get_book_list(uid, booklist.LIST_INTERESTED)
            for book in books:
                # each one is a Book
                pass

            books = books['collections']
            self.html = ""
            for book_obj in books:
                # keys(): 'status', 'comment', 'updated', 'user_id', 'rating', 'book', 'book_id', 'id'
                self._output('')
                self._output('')

                self._output_item('Status', book_obj['status'])
                self._output_item('Rating', book_obj['rating'])
                self._output_item('Updated time', book_obj['updated'])
                self._output_item('Saved by', book_obj['user_id'])
                self._output_item('id (what is that?)', book_obj['id'])
                b = book.Book.parse_from_douban(book_obj['book'], book_obj['book_id'])
                self._render_book(b)

                self._output('')
                self._output('')

            return self.html
            # end of for loop

    def _output(self, msg):
        """ Write a line of msg to response. """
        self.html += msg
        self.html += '<br/>'

    def _output_item(self, name, value):
        self.html += (name + ': ')
        self.html += unicode(value)
        self.html += '<br/>'

    def _render_book(self, b):
        self._output_item('Data src', b.source)
        self._output_item('ISBN', b.isbn)
        self._output_item('Title', b.title)
        self._output_item('Subtitle', b.subtitle)
        self._output_item("Original Title", b.title_original)
        self._output_item("Authors", ', '.join(b.authors))
        self._output_item("Authors Intro", b.authors_intro)
        self._output_item("Translators", ','.join(b.translators))
        self._output_item("Summary", b.summary)
#        self._output_item("Rating", b.rating_others)

        if b.img_link:
            html = '<img src="%s"/>' % b.img_link
            self._output(html)
        else:
            self._output("Image Url: ")
        if b.douban_url:
            self._output("""<a href=" """ + b.douban_url + """ ">Douban Url</a> """)
        else:
            self._output("Douban Url: ")

        self._output_item("Published by", b.publisher)
        self._output_item('Published in', b.published_date)
        self._output_item("Total Pages", b.pages)

#         tags_others = b.tags_others
#        self._output_item("Tags by others", '; '.join(unicode(p) for p in tags_others))

#         price = b.price
#         self._output_item("Price", price)
    # end of self._render_book(b)



class InterestedListHandler(_BookListHandler):
    title = "Interested List"
    active_nav = "Interested"

    def _prepare_books(self, user):
        return None


class DoneListHandler(_BookListHandler):
    title = "Done List"
    active_nav = "Done"

    def _prepare_books(self, user):
        return None
