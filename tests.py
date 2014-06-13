import os
import zeeguu
import unittest
import tempfile
import zeeguu.populate

class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
    	print "test setup"
        # self.db_fd, zeeguu.app.config['DATABASE'] = tempfile.mkstemp()
        zeeguu.app.config['TESTING'] = True
        self.app = zeeguu.app.test_client()
        zeeguu.populate.create_test_db()

    def tearDown(self):
        # os.close(self.db_fd)
        # os.unlink(zeeguu.app.config['DATABASE'])
        pass

    def test_homepage_rendered_correctly(self):
	    rv = self.app.get('/')
	    assert 'The Language Gym' in rv.data

if __name__ == '__main__':
    unittest.main()
