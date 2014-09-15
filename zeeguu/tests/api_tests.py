import zeeguu_testcase
# Always must be imported first
# it sets the test DB

import unittest
import zeeguu.populate
import zeeguu.model

class API_Tests(zeeguu_testcase.ZeeguuTestCase):

    def test_login(self):
        rv = self.login('i@mir.lu', 'password')
        assert 'This is a list of the words you are learning' in rv.data

    def test_logout(self):
        self.logout()
        rv = self.app.get('/identify_the_word')
        assert 'Redirecting' in rv.data

    def test_contribute(self):
        formData = dict(
            url='http://mir.lu',
            context='Somewhere over the rainbow',
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
        assert 'Somewhere over the rainbow' in rv.data

    def test_contribute_without_title_should_fail(self):
        formData = dict(
            url='http://mir.lu',
            context='somewhere over the rainbowwwwwwwww')
        rv = self.app.post(self.in_session('/contribute_with_context/de/sondern/en/but'), data=formData)
        assert rv.data == "OK"

    def test_get_contribs(self):
        rv = self.app.get(self.in_session('/contribs'))
        assert "Wald" in rv.data


if __name__ == '__main__':
    unittest.main()
