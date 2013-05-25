# coding=utf-8
'''
@author: Xuankang
@description: defining the properties and methods of User, saved in the datastore
'''

import datetime
from google.appengine.ext import db

import utils


class User(db.Model):
    '''
    The User class contains all the information for the user's identification.
    Together with some useful methods concerning with User.
    '''

    # used as the user's id
    email = db.EmailProperty(required=True)
    pwd_hashed = db.StringProperty(required=True)

    # for douban
    douban_access_token = db.StringProperty()
    douban_refresh_token = db.StringProperty()
    douban_id = db.StringProperty()                 # user_id, all numbers. e.g. 1234567

    douban_uid = db.StringProperty()                # user_uid, e.g. andriylin
    douban_name = db.StringProperty()               # user_name, e.g. 康康Andriy
    douban_url = db.LinkProperty()                  # user's homepage, e.g. www.douban.com/people/andriylin/
    douban_signature = db.StringProperty()          # user's one line 'mood', e.g. Today is a good day.
    douban_image = db.LinkProperty()                # user's icon
    douban_description = db.TextProperty()          # long paragraph of introduction..
    douban_created_time = db.DateTimeProperty()     # e.g. 2010-03-21 18:16:05
    # end of douban

    def add_info_from_douban(self, obj):
        """ Add additional information when OAuth2 has been approved.
            @param obj: The JSON object returned by douban containing user info.
            Raise ParseJsonError when errors occur.
        """
        assert obj is not None

        # uid
        _tmp = obj.get('uid')
        if _tmp:
            self.douban_uid = _tmp
        # end of uid

        # username
        _tmp = obj.get('name')
        if _tmp:
            self.douban_name = _tmp
        # end of username

        # url
        _tmp = obj.get('alt')
        if _tmp:
            self.douban_url = db.Link(_tmp)
        # end of url

        # signature
        _tmp = obj.get('signature')
        if _tmp:
            self.douban_signature = _tmp
        # end of signature

        # image
        _tmp = obj.get('large_avatar')
        if _tmp:
            self.douban_image = db.Link(_tmp)
        _tmp = obj.get('avatar')
        if self.douban_image is None and _tmp:
            self.douban_image = db.Link(_tmp)
        # end of image

        # description
        _tmp = obj.get('desc')
        if _tmp:
            self.douban_description = _tmp
        # end of description

        # created time
        _tmp = obj.get('created')
        if _tmp:
            try:
                self.douban_created_time = datetime.datetime.strptime(_tmp, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        # end of created time
    # end of self.add_info_from_douban(obj)

    def is_douban_connected(self):
        """ Return True if the user has been connected to douban. """
        # if douban_access_token is not None and it is not empty, True
        return self.douban_access_token

    @db.transactional
    def disconnect_from_douban(self):
        self.douban_access_token = None
        self.douban_refresh_token = None
        self.put()

    @classmethod
    def get_by_email(cls, email, key_only=False):
        """ Retrieve the User according to his/her email.
            Returns None if it doesn't exist.
        """
        if email is None:
            return None

        cursor = db.GqlQuery("SELECT * FROM User WHERE ANCESTOR IS :parent_key AND email = :val LIMIT 1",
                             parent_key=utils.get_key_auth(),
                             val=email)
        return cursor.get(keys_only=key_only)

    @classmethod
    def exists(cls, email):
        """ Check if there is already a user with such an email. """
        return cls.get_by_email(email, key_only=True) is not None
