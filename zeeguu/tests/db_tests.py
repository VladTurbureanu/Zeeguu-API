__author__ = 'mircea'
from zeeguu_testcase import ZeeguuTestCase
import unittest
from zeeguu import model, db
from zeeguu.model import Word, Language, User
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
        someword = model.Word.find("hauen", de)
        assert mir
        assert someword

        mir.starred_words.append(someword)
        db.session.commit()

    def test_user_contribution_count(self):
        mir = model.User.find("i@mir.lu")
        assert mir
        assert len(mir.all_contributions()) > 0

    def test_add_new_word_to_DB(self):
        deutsch = Language.find("de")
        new_word = Word("baum", deutsch)
        mircea = User.find("i@mir.lu")

        db.session.add(new_word)
        mircea.star(new_word)
        db.session.commit()

    def test_find_word(self):
        deutsch = Language.find("de")
        assert Word.find("baum", deutsch)


    def test_user_words(self):
        mir = model.User.find("i@mir.lu")
        assert mir.user_words() == map((lambda x: x.origin.word), mir.all_contributions())
        print mir.user_words()



    def test_preferred_words(self):
        mir = model.User.find("i@mir.lu")
        de = model.Language.find("de")
        someword = model.Word.find("hauen",de)
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


    def test_user_daily_contributions(self):

        mir = model.User.find("i@mir.lu")
        date = datetime.datetime(2011,01,01)

        assert len(mir.all_contributions()) > 0

        count_contributions = 0
        for contribution in mir.all_contributions():
            if contribution.time == date:
                count_contributions += 1

        assert (count_contributions > 0)


    def test_user_set_language(self):
        mir = model.User.find("i@mir.lu")
        print mir.learned_language
        mir.set_learned_language("it")
        print mir.learned_language

    def test_importance_level(self):
        deutsch = Language.find("de")
        new_word = Word("beschloss ", deutsch)
        mircea = User.find("i@mir.lu")

        db.session.add(new_word)
        db.session.commit()

        beschloss = Word.find("unexistantablewordindeutsch", deutsch)
        assert beschloss
        assert beschloss.importance_level() == 0


    # User Date No_ contributions


if __name__ == '__main__':
    unittest.main()
