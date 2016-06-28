# Always must be imported first
# it sets the test DB

__author__ = 'mircea'
import zeeguu_testcase
import time


from zeeguu.model.url import Url

from zeeguu.model.bookmark import Bookmark
from zeeguu.model.smartwatch.watch_interaction_event import WatchInteractionEvent
from zeeguu.model.user_activitiy_data import UserActivityData
from zeeguu.model.feeds import RSSFeed

import zeeguu.model.ranked_word
from zeeguu.model.smartwatch.watch_event_type import WatchEventType
from zeeguu.model.user import User
from zeeguu.the_librarian.website_recommender import recent_domains_with_times, frequent_domains

import unittest
from zeeguu import model, db
from zeeguu.model.user_word import UserWord
from zeeguu.model.language import Language
from datetime import datetime
import random
import zeeguu


class Dbtest(zeeguu_testcase.ZeeguuTestCase):

    def setUp(self):
        # Superclass does prepare the DB before each of the tests
        super(Dbtest, self).setUp()

        # Some common test fixtures
        self.mir = User.find("i@mir.lu")
        assert self.mir
        self.de = Language.find("de")

    def tearDown(self):
        super(Dbtest, self).tearDown()
        self.de = None #if we don't do this, the test holds onto this object across runs sometimes, and
        # this messes up the test db initialization. two hours well spent... aiii iaaa!
        self.mir = None

    def test_languages_exists(self):
        assert self.de.name == "German"


    def test_get_all_languages(self):
        assert model.Language.all()
        assert u'en' in [lan.id for lan in model.Language.all()]
        assert u'German' in [lan.name for lan in model.Language.all()]


    def test_preferred_word(self):
        starred_words_count_before = len(self.mir.starred_words)

        hauen = model.UserWord.find("hauen", self.de)
        self.mir.starred_words.append(hauen)
        db.session.commit()

        starred_words_count_after = len(self.mir.starred_words)

        assert starred_words_count_after == starred_words_count_before + 1


    def test_user_bookmark_count(self):
        assert len(self.mir.all_bookmarks()) > 0


    def test_add_new_word_to_DB(self):
        word = "baum"
        rank = UserWord.find_rank(word, self.de)
        new_word = UserWord(word, self.de, rank)

        db.session.add(new_word)
        self.mir.star(new_word)
        db.session.commit()


    def test_find_word(self):
        word = "baum"
        assert UserWord.find(word, self.de)


    def test_user_word(self):
        assert self.mir.user_words() == map((lambda x: x.origin.word), self.mir.all_bookmarks())


    def test_search_1(self):
        word = UserWord.find("hauen345", self.de)
        s = model.Search(self.mir, word, self.de)
        db.session.add(s)
        db.session.commit()


    def test_preferred_words(self):
        word = "hauen"
        if(zeeguu.model.ranked_word.RankedWord.exists(word.lower(), self.de)):
            rank = model.UserWord.find_rank(word.lower(), self.de)
            someword = model.UserWord.find(word,self.de)
        else:
            someword = model.UserWord.find(word,self.de)
        assert someword
        # add someword to starred words
        self.mir.starred_words.append(someword)
        db.session.commit()

        assert someword in self.mir.starred_words

        self.mir.starred_words.remove(someword)
        db.session.commit()
        assert not self.mir.starred_words



    def test_user_daily_bookmarks(self):

        date = datetime.datetime(2011,01,01)

        assert len(self.mir.all_bookmarks()) > 0

        count_bookmarks = 0
        for bookmark in self.mir.all_bookmarks():
            if bookmark.time == date:
                count_bookmarks += 1

        assert (count_bookmarks > 0)


    def test_user_set_language(self):
        self.mir.set_learned_language("it")
        assert self.mir.learned_language.id == "it"


    def test_importance_level(self):
        word = "beschloss"
        if zeeguu.model.ranked_word.RankedWord.exists(word.lower(), self.de):
            rank = model.UserWord.find_rank(word.lower(), self.de)
            new_word = model.UserWord.find(word,self.de)
        else:
            new_word = model.UserWord.find(word,self.de)

        db.session.add(new_word)
        db.session.commit()

        word = "unexistingword"
        beschloss = UserWord.find(word, self.de)
        assert beschloss
        assert beschloss.importance_level() == 0


    def test_native_language(self):
        assert self.mir.native_language.id == "ro"

        ada = model.User.find("i@ada.lu")
        assert ada.native_language.id == "en"


    def test_get_random_bookmark(self):

        bookmarks = (
            model.Bookmark.query.filter_by(user=self.mir)
                                    .join(model.UserWord, model.Bookmark.origin)
        ).all()

        print (random.choice(bookmarks).origin.word)


    def test_url_domain(self):
        url = model.Url("http://news.mir.com/page1", "Mir News")
        assert url.domain() == "http://news.mir.com"

        url = model.Url("news.mir.com/page1", "Mir News")
        assert url.domain() == "news.mir.com"

        url = model.Url("https://news.mir.com/page1", "Mir News")
        assert url.domain() == "https://news.mir.com"

        url = model.Url("", "Mir News")
        assert url.domain() == ""

    def test_user_recently_visited_domains(self):
        assert len(recent_domains_with_times(self.mir)) == 3

    def test_user_recently_visited_domains_does_not_include_android(self):
        assert not(any("android" in dom[0] for dom in recent_domains_with_times(self.mir)))

    def test_frequent_domains(self):
        print (frequent_domains(self.mir))


    def test_one_domain_multiple_urls(self):
        # Funny thing: you have to make sure to commit ASAP
        # otherwise, you end up having two domain name objects
        # because each Url creates one...
        u1 = model.Url("https://mir.lu/tralala/trilili", "")
        db.session.add(u1)
        db.session.commit()


        u2 = model.Url("https://mir.lu/tralala/trilili2", "")
        db.session.add(u2)
        db.session.commit()

        d = model.DomainName.find("https://mir.lu")
        print (d.domainNameString)

    def test_watch_event_type(self):
        retrieved = WatchEventType.find_by_name("glance")
        if not retrieved:
            retrieved = WatchEventType("glance")
            db.session.add(retrieved)
            db.session.commit()

        retrieved = WatchEventType.find_by_name("glance")
        assert (retrieved.name == "glance")
        return retrieved

    def test_watch_event(self):
        glance = self.test_watch_event_type()
        a_bookmark = Bookmark.find(1)

        new_glance = WatchInteractionEvent(glance, 1, datetime.now())
        db.session.add(new_glance)
        db.session.commit()

        assert len(WatchInteractionEvent.events_for_bookmark(a_bookmark)) == 1

    def test_user_activity_data(self):
        uad = UserActivityData(self.mir,
                               datetime.now(),
                               "reading",
                               "1200",
                               "")
        assert uad.event == "reading"
        db.session.add(uad)
        db.session.commit()


    def test_get_user_activity_data(self):
        events = WatchInteractionEvent.events_for_user(self.mir)
        assert len(events) == 0
        self.test_watch_event()
        events = WatchInteractionEvent.events_for_user(self.mir)
        assert len(events) == 1

    def test_feed_items(self):
        url = Url("http://www.bild.de/rss-feeds/rss-16725492,feed=home.bild.html", "Build")
        feed = RSSFeed(url, "Bild.de Home", "build", image_url = None, language = None)
        items = feed.feed_items()

        first_item_date = items[0]["published"]
        assert first_item_date


    # User Date No_ bookmarks


if __name__ == '__main__':
    unittest.main()
