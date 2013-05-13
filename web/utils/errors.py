'''
@author: Andriy Lin
@description: The hierarchy of all *errors* that may occur while running the application.
'''

class ABError(Exception):
    """ The basic exception for this project. Stands for *AndriyBooksException*. """

    def __init__(self, msg):
        """ Just a msg describing what happened. """
        self.msg = msg

    def __str__(self):
        return self.msg


class FetchDataError(ABError):
    """ Error fetching data from a source online. """

    def __init__(self, msg, link, error_code=None):
        """ @param link: the url to fetch data.
            @param error_code: the error code provided by the resource url.
        """
        super(FetchDataError, self).__init__(msg)
        self.link = link
        self.error_code = error_code

    def __str__(self):
        return self.msg + "; Link: " + str(self.link) + "; Err: " + self.error_code


class ParseJsonError(ABError):
    """ Error parsing the provided json into a valid data structure. """

    def __init__(self, msg, res_id):
        """ @param res_id: may be the book_id of douban. """
        super(ParseJsonError, self).__init__(msg)
        self.res_id = res_id

    def __str__(self):
        return self.msg + "; Res_id: " + self.res_id
