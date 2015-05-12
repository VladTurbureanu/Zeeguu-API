

# Always must be imported first
# it sets the test DB

__author__ = 'mircea'
import zeeguu_testcase

from zeeguu_testcase import ZeeguuTestCase
import unittest
from zeeguu import model, db
from zeeguu.model import UserWord, Language, User
import datetime


class Dbtest(ZeeguuTestCase):


    def test_languages_exists(self):
        de = model.Language.find("de")
        assert de.name == "German"

    def test_get_all_languages(self):
        assert model.Language.all()
        assert u'en' in [lan.id for lan in model.Language.all()]
        assert u'German' in [lan.name for lan in model.Language.all()]

    def test_preferred_word(self):
        mir = model.User.find("i@mir.lu")
        de = model.Language.find("de")
        word = "hauen"
        rank = model.UserWord.find_rank(word, de)
        someword = model.UserWord.find(word, de, rank)
        assert mir
        assert someword

        mir.starred_words.append(someword)
        db.session.commit()

    def test_user_bookmark_count(self):
        mir = model.User.find("i@mir.lu")
        assert mir
        assert len(mir.all_bookmarks()) > 0

    def test_add_new_word_to_DB(self):
        deutsch = Language.find("de")
        word = "baum"
        rank = model.UserWord.find_rank(word, deutsch)
        new_word = UserWord(word, deutsch,rank)
        mircea = User.find("i@mir.lu")

        db.session.add(new_word)
        mircea.star(new_word)
        db.session.commit()

    def test_find_word(self):
        deutsch = Language.find("de")
        word = "baum"
        rank = model.UserWord.find_rank(word, deutsch)
        assert UserWord.find(word, deutsch, rank)


    def test_user_words(self):
        mir = model.User.find("i@mir.lu")
        assert mir.user_words() == map((lambda x: x.origin.word), mir.all_bookmarks())



    def test_preferred_words(self):
        mir = model.User.find("i@mir.lu")
        de = model.Language.find("de")
        word = "hauen"
        if(model.WordRank.exists(word.lower(), de)):
            rank = model.UserWord.find_rank(word.lower(), de)
            someword = model.UserWord.find(word,de,rank)
        else:
            someword = model.UserWord.find(word,de,None)
        assert mir
        assert someword
        # add someword to starred words
        mir.starred_words.append(someword)
        db.session.commit()

        mir = model.User.find("i@mir.lu")
        assert someword in mir.starred_words

        mir.starred_words.remove(someword)
        db.session.commit()
        assert not mir.starred_words


    def test_user_daily_bookmarks(self):

        mir = model.User.find("i@mir.lu")
        date = datetime.datetime(2011,01,01)

        assert len(mir.all_bookmarks()) > 0

        count_bookmarks = 0
        for bookmark in mir.all_bookmarks():
            if bookmark.time == date:
                count_bookmarks += 1

        assert (count_bookmarks > 0)


    def test_user_set_language(self):
        mir = model.User.find("i@mir.lu")
        mir.set_learned_language("it")
        assert mir.learned_language.id == "it"


    def test_importance_level(self):
        deutsch = Language.find("de")
        word = "beschloss"
        if(model.WordRank.exists(word.lower(), deutsch)):
            rank = model.UserWord.find_rank(word.lower(), deutsch)
            new_word = model.UserWord.find(word,deutsch,rank)
        else:
            new_word = model.UserWord.find(word,deutsch,None)
        mircea = User.find("i@mir.lu")

        db.session.add(new_word)
        db.session.commit()

        word = "unexistingword"
        beschloss = UserWord.find(word, deutsch, None)
        assert beschloss
        assert beschloss.importance_level() == 0


    def test_native_language(self):
        mir = model.User.find("i@mir.lu")
        ada = model.User.find("i@ada.lu")
        assert mir.native_language.id == "ro"
        assert ada.native_language.id == "en"



    # User Date No_ bookmarks


if __name__ == '__main__':
    unittest.main()
