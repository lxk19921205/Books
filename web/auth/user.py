'''
@author: Xuankang
@description: defining the properties and methods of User, saved in the datastore
'''

from google.appengine.ext import db

class User(db.Model):
    '''
    The User class contains all the information for the user's identification.
    Together with some useful methods concerning with User.
    '''

    email = db.EmailProperty(required=True)
    pwd_hashed = db.StringProperty(required=True)
    # TODO more attributed will be added, such as nickname, douban id, weibo id...


    @classmethod
    def get_by_email(cls, email):
        """ Retrieve the User according to his/her email. 
        Returns None if it doesn't exist.
        """
        cursor = db.GqlQuery("select * from User where email = :val", val=email)
        return cursor.get()
        
    @classmethod
    def exists(cls, email):
        """ Check if there is already a user with such an email. """
        return cls.get_by_email(email) is not None
