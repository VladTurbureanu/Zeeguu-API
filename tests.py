import os
import zeeguu
import unittest
import tempfile
import zeeguu.populate
import urllib

class FlaskrTestCase(unittest.TestCase):

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


    #
    #
    #


    def setUp(self):
        zeeguu.app.config['TESTING'] = True
        self.app = zeeguu.app.test_client()
        zeeguu.populate.create_test_db()
        self.session = self.get_session()


    def test_not_logged_in(self):
        self.logout()
        rv = self.app.get('/identify_the_word')
        assert 'Redirecting' in rv.data


    def test_homepage_is_rendered_correctly(self):
        rv = self.app.get('/')
        assert 'The Language Gym' in rv.data


    def test_login_logout(self):
        rv = self.login('i@mir.lu', 'password')
        assert 'These are the words and examples' in rv.data


    def test_example_read_from_url(self):
        handle = urllib.urlopen("http://scg.unibe.ch/staff/mircea")
        assert "Mircea F. Lungu" in handle.read()
        handle.close()

    def test_get_url_for_dicts_taht_do_nasty_urls(self):
        dictionaries = [
            'http://pda.leo.org/#/search=fantastisch',
        ]

        for d in dictionaries:
            formData = dict(url=d)
            rv = self.app.post(self.in_session('/get_page'), data=formData)
            if 'fantastic' in rv.data:
                print "OK for " + d
            else:
                print "Fail for " + d
                print rv.data



    def test_get_url(self):
        dictionaries = [
            'http://www.dict.cc/?s=fantastic',
            'http://www.wordreference.com/deen/fantastisch',
            'http://dictionary.sensagent.com/fantastisch/de-en/'
        ]

        for d in dictionaries:
            formData = dict(url=d)
            rv = self.app.post(self.in_session('/get_page'), data=formData)
            if 'fantastic' in rv.data:
                print "OK for " + d
            else:
                print "Fail for " + d
                print rv.data
                assert False

    def test_contribute(self):
        formData = dict(
            url='http://mir.lu',
            context='somewhere over the rainboww',
            title='Songs by Iz')
        rv = self.app.post(self.in_session('/contribute_with_context/de/sondern/en/but'), data=formData)
        assert rv.data == "OK"

    def test_contribute_without_title_should_fail(self):
        formData = dict(
            url='http://mir.lu',
            context='somewhere over the rainbowwwwwwwww')
        rv = self.app.post(self.in_session('/contribute_with_context/de/sondern/en/but'), data=formData)
        assert rv.data == "OK"





if __name__ == '__main__':
    unittest.main()
