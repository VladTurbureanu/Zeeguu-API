# -*- coding: utf8 -*-
import re

import zeeguu
import datetime
from zeeguu.model.url import Url
from zeeguu.model.text import Text
from zeeguu.model.exercise_outcome import ExerciseOutcome
from zeeguu.model.exercise_source import ExerciseSource
from zeeguu.model.user_word import UserWord
from zeeguu import RankedWord
from zeeguu.model.bookmark import Bookmark
from zeeguu.model.language import Language
from zeeguu.model.user import User

WORD_PATTERN = re.compile("\[?([^{\[]+)\]?( {[^}]+})?( \[[^\]]\])?")


class WordCache(object):
    def __init__(self):
        self.cache = {}

    def __getitem__(self, args):
        word = self.cache.get(args, None)
        if word is None:
            word = UserWord(*args)
            zeeguu.db.session.add(word)
            self.cache[args] = word
        return word


def populate(from_, to, dict_file):
    cache = WordCache()
    with open(dict_file, "r") as f:
        for line in f:
            if line.startswith("#") or line.strip() == "":
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                return
            orig = cache[clean_word(parts[0]), from_]
            trans = cache[clean_word(parts[1]), to]
            if trans not in orig.translations:
                orig.translations.append(trans)


def filter_word_list(word_list):
    filtered_word_list = []
    lowercase_word_list = []
    for word in word_list:
         if word.lower() not in lowercase_word_list:
            lowercase_word_list.append(word.lower())
    for lc_word in lowercase_word_list:
        for word in word_list:
            if word.lower()  == lc_word:
                filtered_word_list.append(word)
                break
    return filtered_word_list


def path_of_language_resources():
    """
    the easiest way to make sure that the langauge dictionary files
    are found when running the test cases, either from IDE or from the
    command line is to
    - compute the path relative to this file
    :return:
    """
    import os
    path = os.path.dirname(__file__)
    return path+"/../languages/"


def test_word_list(lang_code):

    words_file = open(path_of_language_resources()+lang_code+"-test.txt")
    words_list = words_file.read().splitlines()
    return words_list


def add_ranked_word_to_db(lang_code):
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    from_lang = Language.find(lang_code)
    initial_line_number = 1

    for word in filter_word_list(test_word_list(lang_code)):
        r = RankedWord(word.lower(), from_lang,initial_line_number)
        zeeguu.db.session.add(r)
        initial_line_number+=1
    zeeguu.db.session.commit()


def clean_word(word):
    match = re.match(WORD_PATTERN, word)
    if match is None:
        return word.decode("utf8")
    return match.group(1).decode("utf8")


def add_bookmark(user, original_language, original_word, translation_language, translation_word,  date, the_context, the_url, the_url_title):

    url = Url.find (the_url)
    text = Text.find_or_create(the_context, translation_language, url)
    origin = UserWord.find(original_word.lower(), original_language)
    translation = UserWord.find(translation_word.lower(), translation_language)


    zeeguu.db.session.add(url)
    zeeguu.db.session.add(text)
    zeeguu.db.session.add(origin)
    zeeguu.db.session.add(translation)
    t1= Bookmark(origin, translation, user, text, date)
    zeeguu.db.session.add(t1)

    zeeguu.db.session.commit()
    add_probability_to_existing_words_of_user(user,t1,original_language)



def add_probability_to_existing_words_of_user(user,bookmark,language):
    bookmark.calculate_probabilities_after_adding_a_bookmark(user,language)


def create_test_db():

    de = Language("de", "German")
    da = Language("da", "Danish")
    en = Language("en", "English")
    es = Language("es", "Spanish")
    fr = Language("fr", "French")
    it = Language("it", "Italian")
    no = Language("no", "Norwegian")
    nl = Language("nl", "Dutch")
    pt = Language("pt", "Portughese")
    ro = Language("ro", "Romanian")

    zeeguu.db.session.add(de)
    zeeguu.db.session.add(da)
    zeeguu.db.session.add(en)
    zeeguu.db.session.add(es)
    zeeguu.db.session.add(fr)
    zeeguu.db.session.add(it)
    zeeguu.db.session.add(no)
    zeeguu.db.session.add(nl)
    zeeguu.db.session.add(pt)
    zeeguu.db.session.add(ro)
    zeeguu.db.session.commit()

    show_solution = ExerciseOutcome("Show solution")
    retry = ExerciseOutcome("Retry")
    correct = ExerciseOutcome("Correct")
    wrong = ExerciseOutcome("Wrong")
    typo = ExerciseOutcome("Typo")
    too_easy = ExerciseOutcome("Too easy")

    recognize = ExerciseSource("Recognize")
    translate = ExerciseSource("Translate")
    zeekoe = ExerciseSource("ZeeKoe")

    zeeguu.db.session.add(show_solution)
    zeeguu.db.session.add(retry)
    zeeguu.db.session.add(correct)
    zeeguu.db.session.add(wrong)
    zeeguu.db.session.add(typo)
    zeeguu.db.session.add(too_easy)

    zeeguu.db.session.add(recognize)
    zeeguu.db.session.add(translate)
    zeeguu.db.session.add(zeekoe)

    user = User("i@mir.lu", "Mircea", "pass", de, ro)
    user2 = User("i@ada.lu", "Ada", "pass", fr)

    zeeguu.db.session.add(user)
    zeeguu.db.session.add(user2)

    jan111 = datetime.datetime(2011,01,01,01,01,01)
    ian101 = datetime.datetime(2001,01,01,01,01,01)
    jan14 = datetime.datetime(2014,1,14,01,01,01)

    today_dict = {
        'sogar':'actually',
        'sperren':'to lock, to close',
        'Gitter':'grates',
        'erfahren':'to experience',
        'treffen':'hit',
        'jeweils':'always',
        'Darstellung':'presentation',
        'Vertreter':'representative',
        'Knecht':'servant',
        'der':'the'
    }

    dict = {
            u'Spaß': 'fun',
            'solche': 'suchlike',
            'ehemaliger': 'ex',
            'betroffen': 'affected',
            'Ufer':'shore',
            u'höchstens':'at most'
            }

    french_dict = {
        'jambes':'legs',
        'de':'of',
        'et':'and'
            }

    story_url = 'http://www.gutenberg.org/files/23393/23393-h/23393-h.htm'
    japanese_story = [
            # ['recht', 'right', 'Du hast recht', story_url],
            ['Holzhauer', 'wood choppers', 'Da waren einmal zwei Holzhauer können', story_url],
            ['Da', 'there', 'Da waren einmal zwei Holzhauer können', story_url],
            ['zwei', 'two', 'Da waren einmal zwei Holzhauer können', story_url],
            [u'Wald','to arrive', u'Um in den Walden zu gelangen, mußten sie einen großen Fluß passieren. Um in den Walden zu gelangen, mußten sie einen großen Fluß passieren. Um in den Walden zu gelangen, mußten sie einen großen Fluß passieren. Um in den Walden zu gelangen, mußten sie einen großen Fluß passieren', story_url],
            ['eingerichtet','established',u'Um in den Wald zu gelangen, mußten sie einen großen Fluß passieren, über den eine Fähre eingerichtet war', story_url],
            [u'vorläufig','temporary',u'von der er des rasenden Sturmes wegen vorläufig nicht zurück konnte', story_url],
            [u'werfen', 'to throw',u'Im Hause angekommen, warfen sie sich zur Erde,', story_url],
            ['Tosen','roar',u'sie Tür und Fenster wohl verwahrt hatten und lauschten dem Tosen des Sturmes.sie Tür und Fenster wohl verwahrt hatten und lauschten dem Tosen des Sturmes.sie Tür und Fenster wohl verwahrt hatten und lauschten dem Tosen des Sturmes',story_url],
            ['Entsetzen','horror','Entsetzt starrte Teramichi auf die Wolke',story_url]
        ]

    add_ranked_word_to_db('de')

    for key in today_dict:
        add_bookmark(user, de, key, en, today_dict[key], jan111, "Keine bank durfe auf immunitat pochen, nur weil sie eine besonders herausgehobene bedeutung fur das finanzsystem habe, sagte holder, ohne namen von banken zu nennen",
                         "http://url2", "title of url2")

    for key in dict:
        add_bookmark(user, de, key, en, dict[key], ian101, "Deutlich uber dem medianlohn liegen beispielsweise forschung und entwicklung, tabakverarbeitung, pharma oder bankenwesen, am unteren ende der skala liegen die tieflohnbranchen detailhandel, gastronomie oder personliche dienstleistungen. ",
                         "http://url1", "title of url1")

    for key in french_dict:
        add_bookmark(user, de, key, en, french_dict[key], ian101, "Deutlich uber dem medianlohn liegen beispielsweise forschung und entwicklung, tabakverarbeitung, pharma oder bankenwesen, am unteren ende der skala liegen die tieflohnbranchen detailhandel, gastronomie oder personliche dienstleistungen. ",
                         "http://url1", "title of url1")
    for w in japanese_story:
        add_bookmark(user, de, w[0], en, w[1],jan14, w[2],w[3], "japanese story")

    zeeguu.db.session.commit()


if __name__ == "__main__":

    "in populate..."
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    zeeguu.db.drop_all()
    zeeguu.db.create_all()
    create_test_db()
