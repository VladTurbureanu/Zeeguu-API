# coding=utf-8
__author__ = 'mircea'

# We need this even before the zeeguu_testcase import
# so we are sure to setup the right db for pefromance testing
import os
os.environ["ZEEGUU_PERFORMANCE_TESTING"] = "True"

import zeeguu_testcase
# Always must be imported first
# it sets the test DB

from zeeguu.model import User
import zeeguu

class Performance_Tests(zeeguu_testcase.ZeeguuTestCase):

    # We must override the super implementation, which
    # repopulates the DB
    def setUp(self):
        self.app = zeeguu.app.test_client()
        zeeguu.app.test_request_context().push()
        self.session = self.get_session()

    def test_user_bookmarks(self):
        user = User.find("i@mir.lu")
        assert user.all_bookmarks() > 100

