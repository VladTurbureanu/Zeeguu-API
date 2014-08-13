import zeeguu_testcase
import unittest

class Gym_Tests(zeeguu_testcase.ZeeguuTestCase):

    def test_homepage_is_rendered_correctly(self):
        rv = self.app.get('/')
        assert 'Language Gym' in rv.data

    def test_contributions_page(self):
        rv = self.app.get('/contributions')
        assert 'hauen' in rv.data

if __name__ == '__main__':
    unittest.main()
