__author__ = 'mircea'
import urllib
import unittest

class SandboxTests(unittest.TestCase):

    def test_example_read_from_url(self):
        handle = urllib.urlopen("http://scg.unibe.ch/staff/mircea")
        assert "Mircea F. Lungu" in handle.read()
        handle.close()


    def test_get_url(self):
        dictionaries = [
            'http://www.dict.cc/?s=fantastic',
            'http://www.wordreference.com/deen/fantastisch',
            'http://dictionary.sensagent.com/fantastisch/de-en/'
        ]

        for d in dictionaries:
            rv = self.app.get(self.in_session('/get_page/'+ urllib.quote(d,"") ))
            print rv.data
            if 'fantastic' in rv.data:
                print "OK for " + d
            else:
                print "Fail for " + d
                print rv.data
                assert False



if __name__ == '__main__':
    unittest.main()
