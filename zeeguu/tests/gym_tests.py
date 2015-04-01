import zeeguu_testcase
import unittest

class Gym_Tests(zeeguu_testcase.ZeeguuTestCase):

    def test_homepage_is_rendered_correctly(self):
        rv = self.app.get('/')
        assert 'redirected' in rv.data

    def test_bookmarks_page(self):
        rv = self.app.get('/bookmarks')
        assert 'hauen' in rv.data

if __name__ == '__main__':
    unittest.main()
