import unittest
import requests
import json
import zeeguu

USER=zeeguu.app.config.get("TEST_USER")
PASS=zeeguu.app.config.get("TEST_PASS")
ZSRV="https://zeeguu.unibe.ch/"


class Live_API_Tests(unittest.TestCase):

    def test_login(self):
        url = 'https://zeeguu.unibe.ch/login'
        data=dict(
            login=True, #/login tests for the existence of "login" in this dict
            email=USER,
            password=PASS)
        response = requests.get(url, data=data)
        assert response

    def test_get_session(self):
        self.test_login()

        rv = requests.post('https://zeeguu.unibe.ch/session/'+USER, data=dict(
            password=PASS
        ))
        assert rv.text > 0
        return rv.text


    def in_session(self, session, url, other_args=None):
        if other_args is None:
            other_args = []
        print session
        print url
        url_with_session = url + "?session=" + session

        for each in other_args:
            url_with_session += "&" + each
        print url_with_session
        return url_with_session

    def zurl(self, url):
        return self.in_session(self.test_get_session(), ZSRV+url)

    def test_content_from_url(self):
        manual_check = False

        data = dict(urls=[
                    dict(url="http://www.derbund.ch/wirtschaft/unternehmen-und-konjunktur/die-bankenriesen-in-den-bergkantonen/story/26984250",
                         id=1),
                    dict(url="http://www.computerbase.de/2015-11/bundestag-parlament-beschliesst-das-ende-vom-routerzwang-erneut/",
                         id=2)])

        r = requests.post(self.zurl('get_content_from_url'), json=data)

        urls = r.json()['contents']
        for url in urls:
            assert url['content'] is not None
            assert url['image'] is not None
            if manual_check:
                print url['content']
                print url['image']

        print urls
        return urls

    def test_get_learnability(self):
        r = requests.post(self.zurl('/get_learnability_for_text/de'), json=dict(texts=self.test_content_from_url()))
        print r.text




