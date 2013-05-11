'''
@author: Andriy Lin
@description: Containing handlers for pages in Explore section
    1. Random!
'''

import webapp2
import urllib

import auth
import utils
import api.douban as douban


class RandomOneHandler(webapp2.RequestHandler):
    """ Handling url "explore/random", randomly pick a book from douban and present it. """

    def get(self):
        email = auth.get_email_from_cookies(self.request.cookies)
        if email:
            self.user = auth.User.get_by_email(email)
            # TODO let the first digit to be non-zero
            book_id = utils.random_book_id()
            # for debugging, set a exact book id
#            book_id = "3597031"
            # TODO to check from local store first?
            self._try_fetch_render(book_id)
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
        self.html = u""

        self._output_item('ID', b.douban_id)
        self._output_item('Data src', b.source)
        self._output_item('ISBN', b.isbn)
        self._output_item('Title', b.title)
        self._output_item('Subtitle', b.subtitle)
        self._output_item("Original Title", b.title_original)
        self._output_item("Authors", ', '.join(b.authors))
        self._output_item("Authors Intro", b.authors_intro)
        self._output_item("Translators", ','.join(b.translators))
        self._output_item("Summary", b.summary)
        self._output_item("Rating", b.rating_others)

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

        tags_others = b.tags_others
        self._output_item("Tags by others", '; '.join(unicode(p) for p in tags_others))

        price = b.price
        self._output_item("Price", price)


        import os
        import jinja2
        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.realpath("./static/html/")))
        template = jinja_env.get_template("random.html")
        context = {
            'book': self.html,
            'user': self.user
        }
        self.response.out.write(template.render(context))
    # end of self._render_book(b)

    def _output(self, msg):
        """ Write a line of msg to response. """
        self.html += msg
        self.html += u'<br/>'

    def _output_item(self, name, value):
        self.html += unicode(name + ': ')
        self.html += unicode(value)
        self.html += u'<br/>'
