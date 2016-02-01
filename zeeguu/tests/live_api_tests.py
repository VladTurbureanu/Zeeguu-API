import unittest
import requests
import zeeguu

USER=zeeguu.app.config.get("TEST_USER")
PASS=zeeguu.app.config.get("TEST_PASS")

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


