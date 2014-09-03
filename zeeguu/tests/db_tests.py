__author__ = 'mircea'
from zeeguu_testcase import ZeeguuTestCase
import unittest
from zeeguu import model, db
from zeeguu.model import Word, Language, User


class Dbtest(ZeeguuTestCase):

    def test_languages_exists(self):
        de = model.Language.find("de")
        assert de.name == "German"


    def test_preferred_word(self):
        mir = model.User.find("i@mir.lu")
        de = model.Language.find("de")
        someword = model.Word.find("hauen",de)
        assert mir
        assert someword

        mir.starred_words.append(someword)
        db.session.commit()

    def test_add_new_word_to_DB(self):
        deutsch = Language.find("de")
        new_word = Word("baum", deutsch)
        mircea = User.find("i@mir.lu")

        db.session.add(new_word)
        mircea.star(new_word)
        db.session.commit()















    # def test_preferred_words(self):
    #     mir = model.User.find("i@mir.lu")
    #     de = model.Language.find("de")
    #     someword = model.Word.find("hauen",de)
    #     assert mir
    #     assert someword
    #     # add someword to starred words
    #     mir.starred_words.append(someword)
    #     db.session.commit()
    #
    #     mir = model.User.find("i@mir.lu")
    #     assert someword in mir.starred_words
    #
    #     mir.starred_words.remove(someword)
    #     db.session.commit()
    #     assert not mir.starred_words


if __name__ == '__main__':
    unittest.main()
