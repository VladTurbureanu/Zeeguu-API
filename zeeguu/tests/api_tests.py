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

    def test_logout(self):
        self.logout()
        rv = self.app.get('/recognize')
        assert 'Redirecting' in rv.data

    def test_contribute_from_android(self):
        formData = dict(
            url='android:app',
            context='User uploaded sentence / user uploaded picture / pre-existing Context (e.g. Harry Potter Book)!',
            title='Zeeguu for Android')
        rv = self.app.post(self.in_session('/contribute_with_context/de/befurchten/en/fear'), data=formData)
        assert rv.data == "OK"
        t = zeeguu.model.Url.find("android:app","Songs by Iz")

        assert t != None

        rv = self.app.get(self.in_session('/contributions'))
        assert 'befurchten' in rv.data
        assert 'Zeeguu for Android' in rv.data


    def test_contribute_without_title_should_fail(self):
        formData = dict(
            url='http://mir.lu',
            context='somewhere over the rainbowwwwwwwww')
        rv = self.app.post(self.in_session('/contribute_with_context/de/sondern/en/but'), data=formData)
        assert rv.data == "OK"


    def test_get_contribs(self):
        rv = self.app.get(self.in_session('/contribs'))
        assert "Wald" in rv.data


    def test_set_language(self):
        rv = self.app.post(self.in_session('/learned_language/it'))
        rv = self.app.post(self.in_session('/native_language/fr'))
        assert "OK" in rv.data
        rv = self.app.get(self.in_session('/learned_language'))
        assert rv.data== "it"
        rv = self.app.get(self.in_session('/native_language'))
        assert rv.data== "fr"


    def test_available_languages(self):
        rv = self.app.get(self.in_session('/available_languages'))
        print rv.data

    def test_get_language(self):
        rv = self.app.get(self.in_session('/learned_language'))
        print rv.data

    def test_get_contributions_by_date(self):
        rv = self.app.get(self.in_session('/contribs_by_day/with_context'))

        elements = json.loads(rv.data)
        some_date = elements[0]
        assert some_date ["date"]

        some_contrib = some_date ["contribs"][0]
        for key in ["from", "to", "id", "context"]:
            assert key in some_contrib

        # if we don't pass the context argument, we don't get
        # the context
        rv = self.app.get(self.in_session('/contribs_by_day/no_context'))
        elements = json.loads(rv.data)
        some_date = elements[0]
        some_contrib = some_date ["contribs"][0]
        assert not "context" in some_contrib





    def test_password_hash(self):
        p1 = "test"
        p2 = "pass"
        user = User.find("i@mir.lu")

        hash1 = util.password_hash(p1,user.password_salt)
        hash2 = util.password_hash(p2, user.password_salt)
        assert hash1 != hash2

        assert user.authorize("i@mir.lu", "pass") != None


if __name__ == '__main__':
    unittest.main()
