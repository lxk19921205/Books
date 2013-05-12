'''
@author: Andriy Lin
@description: Handlers for manipulating book lists
'''

import webapp2

class _BookListHandler(webapp2.RequestHandler):
    """ The base handler for all the Book list handler. """

    def get(self):
        self.response.out.write("Booklist: " + self.id)


class ReadingListHandler(_BookListHandler):
    id = "Reading"
    pass

class InterestedListHandler(_BookListHandler):
    id = "Interested"
    pass

class DoneListHandler(_BookListHandler):
    id = "Done"
    pass
