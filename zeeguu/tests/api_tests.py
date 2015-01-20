import zeeguu_testcase
# Always must be imported first
# it sets the test DB

import unittest
import zeeguu.populate
import zeeguu.model
from zeeguu.model import User
from zeeguu import util
import json

class API_Tests(zeeguu_testcase.ZeeguuTestCase):

    def test_login(self):
        rv = self.login('i@mir.lu', 'password')
        assert 'words you are currently learning' in rv.data

    def test_logout(self):
        self.logout()
        rv = self.app.get('/recognize')
        assert 'Redirecting' in rv.data

    def test_contribute(self):
        formData = dict(
            url='http://mir.lu',
            context='Somewhere over the Rainbow',
            title='Songs by Iz')
        rv = self.app.post(self.in_session('/contribute_with_context/de/sondern/en/but'), data=formData)
        assert rv.data == "OK"
        t = zeeguu.model.Url.find("http://mir.lu","Songs by Iz")

        assert t != None

        rv = self.app.get('/contributions')
        assert 'hauen' in rv.data
        assert 'Songs by Iz' in rv.data
        # This test guarantees that the capitalizatin of the contribution is
        # saved as sent.
        assert 'Somewhere over the Rainbow' in rv.data

    def test_contribute_without_title_should_fail(self):
        formData = dict(
            url='http://mir.lu',
            context='somewhere over the rainbowwwwwwwww')
        rv = self.app.post(self.in_session('/contribute_with_context/de/sondern/en/but'), data=formData)
        assert rv.data == "OK"


    def test_get_contribs(self):
        rv = self.app.get(self.in_session('/contribs'))
        assert "Wald" in rv.data

    def test_get_contribs_by_day(self):
        rv = self.app.get(self.in_session('/contribs_by_day'))

        json_data = json.loads(rv.data)
        assert json_data

        some_date = json_data[0]
        assert some_date ["date"]

        some_contrib = some_date ["contribs"][0]
        assert some_contrib["to"]
        assert some_contrib["from"]
        assert some_contrib["id"]



    def test_password_hash(self):
        p1 = "test"
        p2 = "password"
        user = User.find("i@mir.lu")

        hash1 = util.password_hash(p1,user.password_salt)
        hash2 = util.password_hash(p2, user.password_salt)
        assert hash1 != hash2

        assert user.authorize("i@mir.lu", "password") != None


if __name__ == '__main__':
    unittest.main()
