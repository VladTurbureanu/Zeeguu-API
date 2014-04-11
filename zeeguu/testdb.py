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


def add_contribution(user, language, original, translation, date, the_context, the_url):

    url = model.Url.find (the_url)
    text = model.Text(the_context, en, url)

    w1 = model.Word(original, language)
    w2 = model.Word(translation, en)
    zeeguu.db.session.add(url)
    zeeguu.db.session.add(text)
    zeeguu.db.session.add(w1)
    zeeguu.db.session.add(w2)
    t1= model.Contribution(w1,w2, user, text, date)
    zeeguu.db.session.add(t1)

    zeeguu.db.session.commit()
    return



if __name__ == "__main__":
    print("testing...")
    zeeguu.app.test_request_context().push()

    de = model.Language.find("de")
    user = model.User("user4@localhost.com", "password3", de)
    zeeguu.db.session.add(user)
    print (zeeguu.db.session.commit())
    print "user4 added"

    user = model.User.find("user4@localhost.com")
    zeeguu.db.session.delete(user)
    print (zeeguu.db.session.commit())
    print "user4 removed"
