import zeeguu_testcase
import unittest

class Gym_Tests(zeeguu_testcase.ZeeguuTestCase):

    def test_homepage_is_rendered_correctly(self):
        rv = self.app.get('/')
        assert 'redirected' in rv.data

    def test_bookmarks_page(self):
        rv = self.app.get('/bookmarks')
        assert 'hauen' in rv.data

    def test_next_question_is_not_the_same_as_current(self):
        r1 = self.app.get('/gym/question/de/en')
        r2 = self.app.get('/gym/question/de/en')
        assert r1.data != r2.data


if __name__ == '__main__':
    unittest.main()
