# University of Illinois/NCSA Open Source License
# Copyright (c) 2017, Jakub Svoboda.

# TODO: docstring for the file
from woolnote import util
from woolnote import config
from woolnote import tests

# UI authentication helper
##########################

class WoolnoteUIAuth():
    def __init__(self):
        """
        Class providing functionality to generate and check authentication strings.
        """
        super().__init__()
        self.authenticated_cookie = util.create_random_id()
        self.one_time_pwd = util.generate_one_time_pwd()
        self.one_time_pwd_tries_left = 0
        self.ONE_TIME_PWD_TRIES = 5

    @tests.integration_method("web_ui")
    def return_cookie_authenticated(self):
        """
        Returns a string that should be used as a cookie granting access.

        Returns:
            str: The string value of the cookie value (not the cookie key/name).
        """
        return self.authenticated_cookie

    @tests.integration_method("web_ui")
    def create_new_one_time_pwd(self):
        """
        Creates a new one-time password and sets how many tries are left.

        Returns:
            str: The one-time password (e.g. to be displayed to the user over a secure channel (e.g. loopback)).
        """
        self.one_time_pwd = util.generate_one_time_pwd()
        self.one_time_pwd_tries_left = self.ONE_TIME_PWD_TRIES
        return self.one_time_pwd

    @tests.integration_method("web_ui")
    def check_one_time_pwd(self, user_supplied_pwd):
        """
        Checks whether the supplied one-time password is correct, only if tries are left.
        Password is disabled after 1st successful use.

        Args:
            user_supplied_pwd (): The potentially wrong or malicious password the user provided. Decreases the number of tries left.

        Returns:
            bool: Whether the user-supplied password is correct and allowed.

        """
        self.one_time_pwd_tries_left -= 1
        if self.one_time_pwd_tries_left > 0:
            ret = util.safe_string_compare(user_supplied_pwd, self.one_time_pwd)
            if ret is True:  # explicitly checking for boolean True
                # successful use, prohibit subsequent (e.g. attacker reading screen)
                self.one_time_pwd_tries_left = 0
                return True
            return False
        return False

    @tests.integration_method("web_ui")
    def check_permanent_pwd(self, user_supplied_pwd):
        """
        Checks whether the supplied password is correct.

        Args:
            user_supplied_pwd (str): The potentially wrong or malicious password the user provided.

        Returns:
            bool: Whether the user-supplied password is correct and allowed.
        """
        ret = util.safe_string_compare(user_supplied_pwd, config.LOGIN_PASSWORD)
        if ret is True:  # explicitly checking for boolean True
            return True
        return False


        # TODO: save the permanent password as a hash?
