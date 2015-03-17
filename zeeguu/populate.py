# -*- coding: utf8 -*-
import re

import zeeguu
import datetime
from zeeguu import model


WORD_PATTERN = re.compile("\[?([^{\[]+)\]?( {[^}]+})?( \[[^\]]\])?")


class WordCache(object):
    def __init__(self):
        self.cache = {}

    def __getitem__(self, args):
        word = self.cache.get(args, None)
        if word is None:
            word = model.Word(*args)
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


def clean_word(word):
    match = re.match(WORD_PATTERN, word)
    if match is None:
        print word
        return word.decode("utf8")
    return match.group(1).decode("utf8")


def add_contribution(user, original_language, original_word, translation_language, translation_word,  date, the_context, the_url, the_url_title):

    url = model.Url.find (the_url, the_url_title)
    text = model.Text(the_context, translation_language, url)

    w1 = model.Word(original_word, original_language)
    w2 = model.Word(translation_word, translation_language)
    zeeguu.db.session.add(url)
    zeeguu.db.session.add(text)
    zeeguu.db.session.add(w1)
    zeeguu.db.session.add(w2)
    t1= model.Contribution(w1,w2, user, text, date)
    zeeguu.db.session.add(t1)

    zeeguu.db.session.commit()
    return


def create_test_db():
    zeeguu.app.test_request_context().push()

    zeeguu.db.session.commit()
    zeeguu.db.drop_all()
    zeeguu.db.create_all()

    fr = model.Language("fr", "French")
    de = model.Language("de", "German")
    dk = model.Language("dk", "Danish")
    en = model.Language("en", "English")
    it = model.Language("it", "Italian")
    no = model.Language("no", "Norwegian")
    ro = model.Language("ro", "Romanian")
    es = model.Language("es", "Spanish")

    zeeguu.db.session.add(en)
    zeeguu.db.session.add(fr)
    zeeguu.db.session.add(de)
    zeeguu.db.session.add(dk)
    zeeguu.db.session.add(no)
    zeeguu.db.session.add(it)
    zeeguu.db.session.add(ro)
    zeeguu.db.session.add(es)
    zeeguu.db.session.commit()

    print "created the langages tabele"

    not_know = model.EventOutcome("Do not know")
    retry = model.EventOutcome("Retry")
    correct = model.EventOutcome("Correct")
    wrong = model.EventOutcome("Wrong")
    typo = model.EventOutcome("Typo")
    i_know = model.EventOutcome("I know")

    recognize = model.EventSource("Recognize")
    translate = model.EventSource("Translate")

    zeeguu.db.session.add(not_know)
    zeeguu.db.session.add(retry)
    zeeguu.db.session.add(correct)
    zeeguu.db.session.add(wrong)
    zeeguu.db.session.add(typo)
    zeeguu.db.session.add(i_know)

    zeeguu.db.session.add(recognize)
    zeeguu.db.session.add(translate)



    user = model.User("i@mir.lu", "Mircea", "pass", de, ro)
    user2 = model.User("i@ada.lu", "Ada", "pass", fr)

    zeeguu.db.session.add(user)


    jan111 = datetime.date(2011,01,01)
    ian101 = datetime.date(2001,01,01)
    jan14 = datetime.date(2014,1,14)


    today_dict = {
        'sogar':'actually',
        'sperren':'to lock, to close',
        'Gitter':'grates',
        'erfahren':'to experience',
        'Betroffen':'affected',
        'jeweils':'always',
        'Darstellung':'presentation',
        'Vertreter':'representative',
        'Knecht':'servant',
        'besteht':'smtg. exists'
    }

    for key in today_dict:
        add_contribution(user, de, key, en, today_dict[key], jan111, "Keine bank durfe auf immunitat pochen, nur weil sie eine besonders herausgehobene bedeutung fur das finanzsystem habe, sagte holder, ohne namen von banken zu nennen" + key,
                         "http://url2", "title of url2")


    dict = {
            u'Spaß': 'fun',
            'solche': 'suchlike',
            'ehemaliger': 'ex',
            'betroffen': 'affected',
            'Ufer':'shore',
            u'höchstens':'at most'
            }


    for key in dict:
        add_contribution(user, de, key, en, dict[key], ian101, "Deutlich uber dem medianlohn liegen beispielsweise forschung und entwicklung, tabakverarbeitung, pharma oder bankenwesen, am unteren ende der skala liegen die tieflohnbranchen detailhandel, gastronomie oder personliche dienstleistungen. "+key,
                         "http://url1", "title of url1")



    dict = {
        'jambes':'legs',
        'de':'of',
        'et':'and'
            }


    for key in dict:
        add_contribution(user2, fr, key, en, dict[key], ian101, "Keine bank durfe auf immunitat pochen, nur weil sie eine besonders herausgehobene bedeutung fur das finanzsystem habe, sagte holder, ohne namen von banken zu nennen." + key,
                         "http://localhost.com", "title of url1")


    story_url = 'http://www.gutenberg.org/files/23393/23393-h/23393-h.htm'
    japanese_story = [
            # ['recht', 'right', 'Du hast recht', story_url],
            ['hauen', 'to chop', 'Es waren einmal zwei Holzhauer', story_url],
            [u'Wald','to arrive', u'Um in den Walden zu gelangen, mußten sie einen großen Fluß passieren. Um in den Walden zu gelangen, mußten sie einen großen Fluß passieren. Um in den Walden zu gelangen, mußten sie einen großen Fluß passieren. Um in den Walden zu gelangen, mußten sie einen großen Fluß passieren', story_url],
            ['eingerichtet','established',u'Um in den Wald zu gelangen, mußten sie einen großen Fluß passieren, über den eine Fähre eingerichtet war', story_url],
            [u'vorläufig','temporary',u'von der er des rasenden Sturmes wegen vorläufig nicht zurück konnte', story_url],
            [u'werfen', 'to throw',u'Im Hause angekommen, warfen sie sich zur Erde,', story_url],
            ['Tosen','roar',u'sie Tür und Fenster wohl verwahrt hatten und lauschten dem Tosen des Sturmes.sie Tür und Fenster wohl verwahrt hatten und lauschten dem Tosen des Sturmes.sie Tür und Fenster wohl verwahrt hatten und lauschten dem Tosen des Sturmes',story_url],
            ['Entsetzen','horror','Entsetzt starrte Teramichi auf die Wolke',story_url]
        ]

    for w in japanese_story:
        if w[0] == 'recht':
            # something special
            add_contribution(user, de, w[0], en, w[1],jan14, w[2],w[3], "japanese story")
        else:
            add_contribution(user, de, w[0], en, w[1],jan14, w[2],w[3], "japanese story")


    zeeguu.db.session.commit()
    # print "temp db recreated..."


if __name__ == "__main__":
    create_test_db()
