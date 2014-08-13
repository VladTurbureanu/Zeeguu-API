# Mother of all Zeeguu testcases.
# Provides utility methods for logging in
# Makes sure that we are using the testing DB

import os
os.environ["ZEEGUU_TESTING"] = "True"
# It's important to set this up at the beginning of every test
# otherwise the tests will override the actual database!
# This is too fragile though... The moment I forget, this...

import zeeguu
import unittest
import zeeguu.populate
import zeeguu.model

class ZeeguuTestCase(unittest.TestCase):

    def login(self, email, password):
        return self.app.post('/login', data=dict(
            login=True, #/login tests for the existence of "login" in this dict
            email=email,
            password=password
        ), follow_redirects=True)

    def i_login(self):
        self.login('i@mir.lu', 'password')

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def get_session(self):
        self.i_login()
        rv = self.app.post('/session/i@mir.lu', data=dict(
            password="password"
        ))
        return rv.data

    def in_session(self, url):
        return url + "?session=" + self.session

    def setUp(self):
        # zeeguu.app.config['TESTING'] = True
        self.app = zeeguu.app.test_client()
        zeeguu.populate.create_test_db()
        self.session = self.get_session()