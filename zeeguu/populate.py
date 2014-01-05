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


def add_contribution(original, translation, date):
    w1 = model.Word(original, de)
    w2 = model.Word(translation, en)
    zeeguu.db.session.add(w1)
    zeeguu.db.session.add(w2)
    t1= model.Contribution(w1,w2,user, date)
    zeeguu.db.session.add(t1)
    return



if __name__ == "__main__":
    zeeguu.app.test_request_context().push()

    zeeguu.db.drop_all()
    zeeguu.db.create_all()
    de = model.Language("de", "German")
    en = model.Language("en", "English")
    user = model.User("user@localhost.com", "password", de)
    zeeguu.db.session.add(user)
    zeeguu.db.session.add(en)

    today = datetime.datetime.now()
    yes = datetime.date(2001,01,01)


    today_dict = {
        'Betroffen':'affected',
        'jeweils':'always',
        'Darstellung':'presentation',
        'Vertreter':'representative',
        'Knecht':'servant',
        'besteht':'smtg. exists'
    }

    for key in today_dict:
        add_contribution(key, today_dict[key], today)


    dict = {
            u'Spaß': 'fun',
            'solche': 'suchlike',
            'ehemaliger': 'ex',
            'betroffen': 'affected',
            'Ufer':'shore'
            }


    for key in dict:
        add_contribution(key, dict[key], yes)


    zeeguu.db.session.commit()
