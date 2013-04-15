'''
@author: Andriy Lin
@description: The hierarchy of all *errors* that may occur while running the application.
'''

class ABError(Exception):
    """ The basic exception for this project. Stands for *AndriyBooksException*. """
    pass


class FetchDataError(ABError):
    """ Error fetching data from a source online. """

    def __init__(self, link, error_code=None):
        """ @param link: the url to fetch data.
            @param error_code: the error code provided by the resource url.
        """
        self.link = link
        self.error_code = error_code


class ParseJsonError(ABError):
    """ Error parsing the provided json into a valid data structure. """

    def __init__(self, res_id):
        """ @param res_id: may be the book_id of douban. """
        self.res_id = res_id