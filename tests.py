import os
import zeeguu
import unittest
import tempfile

class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
    	print "test setup"
        self.db_fd, zeeguu.app.config['DATABASE'] = tempfile.mkstemp()
        zeeguu.app.config['TESTING'] = True
        self.app = zeeguu.app.test_client()
        zeeguu.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(flaskr.app.config['DATABASE'])

    def test_empty_db(self):
	    print "test_empty_db"
	    rv = self.app.get('/')
	    print rv.data
	    assert 'No entries here so far' in rv.data

if __name__ == '__main__':
    unittest.main()
