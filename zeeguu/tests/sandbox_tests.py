__author__ = 'mircea'
import urllib
import unittest

class SandboxTests(unittest.TestCase):

    def test_example_read_from_url(self):
        handle = urllib.urlopen("http://scg.unibe.ch/staff/mircea")
        assert "Mircea F. Lungu" in handle.read()
        handle.close()

    def test_feedfinder(self):
        import urllib2
        import feedparser
        from BeautifulSoup import BeautifulSoup

        for domain in ["http://www.derspiegel.de"]:
            print "--> " + domain
            page = urllib2.urlopen(domain)
            soup = BeautifulSoup(page)
            rel_links = soup.findAll("link", type="application/rss+xml")

            for rel_link in rel_links:
                rel_link = rel_link["href"]
                if rel_link[0] == "/":
                    rel_link = domain + rel_link
                print rel_link

                d = feedparser.parse(rel_link)
                print d.feed.title
                print d.feed.link
                print len(d.entries)

                print " "









if __name__ == '__main__':
    unittest.main()
