

# Always must be imported first
# it sets the test DB

__author__ = 'mircea'
import zeeguu_testcase

from zeeguu_testcase import ZeeguuTestCase
import unittest
from zeeguu import model, db
from zeeguu.model import UserWord, Language, User
import datetime
import random


class Dbtest(ZeeguuTestCase):

    def setUp(self):
        # Superclass does prepare the DB before each of the tests
        super(Dbtest, self).setUp()

        # Some common test fixtures
        self.mir = model.User.find("i@mir.lu")
        assert self.mir
        self.de = Language.find("de")


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
        rank = model.UserWord.find_rank(word, self.de)
        new_word = UserWord(word, self.de, rank)

        db.session.add(new_word)
        self.mir.star(new_word)
        db.session.commit()


    def test_find_word(self):
        word = "baum"
        rank = model.UserWord.find_rank(word, self.de)
        assert UserWord.find(word, self.de, rank)


    def test_user_words(self):
        assert self.mir.user_words() == map((lambda x: x.origin.word), self.mir.all_bookmarks())


    def test_search_1(self):
        word = UserWord.find("hauen345", self.de)
        s = model.Search(self.mir, word, self.de)
        db.session.add(s)
        db.session.commit()


    def test_preferred_words(self):
        word = "hauen"
        if(model.WordRank.exists(word.lower(), self.de)):
            rank = model.UserWord.find_rank(word.lower(), self.de)
            someword = model.UserWord.find(word,self.de,rank)
        else:
            someword = model.UserWord.find(word,self.de,None)
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
        if(model.WordRank.exists(word.lower(), self.de)):
            rank = model.UserWord.find_rank(word.lower(), self.de)
            new_word = model.UserWord.find(word,self.de,rank)
        else:
            new_word = model.UserWord.find(word,self.de,None)

        db.session.add(new_word)
        db.session.commit()

        word = "unexistingword"
        beschloss = UserWord.find(word, self.de, None)
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

        print random.choice(bookmarks).origin.word




    # User Date No_ bookmarks


if __name__ == '__main__':
    unittest.main()
