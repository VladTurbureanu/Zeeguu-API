# This file contains utilities that
from BeautifulSoup import BeautifulSoup
import urllib2
import feedparser

def retrieve_feeds_at_url(domain):
    """
    a list of feed sthat can be found at the given url,
    or an empty list if something goes wrong
    :param domain:
    :return:
    """
    try:
        feed_data = []
        page = urllib2.urlopen(domain)
        soup = BeautifulSoup(page)
        feed_urls = soup.findAll("link", type="application/rss+xml")

        for feed_url in feed_urls:
            feed_url = feed_url["href"]
            if feed_url[0] == "/":
                feed_url = domain + feed_url

            feed = feedparser.parse(feed_url).feed

            feed_data.append({
                "url": feed_url,
                "title": feed.get("title",""),
                "description": feed.get("description",""),
                "image_url": feed.get("image",""),
                "language": feed.get("language","")
            })

        return feed_data

    except Exception as e:
        print e
        return []
