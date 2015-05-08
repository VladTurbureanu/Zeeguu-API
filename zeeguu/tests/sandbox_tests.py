__author__ = 'mircea'
import urllib
import unittest

class SandboxTests(unittest.TestCase):

    def test_example_read_from_url(self):
        handle = urllib.urlopen("http://scg.unibe.ch/staff/mircea")
        assert "Mircea F. Lungu" in handle.read()
        handle.close()




if __name__ == '__main__':
    unittest.main()
