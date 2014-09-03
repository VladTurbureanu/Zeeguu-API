__author__ = 'mircea'
from zeeguu_testcase import ZeeguuTestCase
import unittest
from zeeguu import model, db


class Dbtest(ZeeguuTestCase):

    def test_languages_exists(self):
        de = model.Language.find("de")
        assert de.name == "German"

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


if __name__ == '__main__':
    unittest.main()
