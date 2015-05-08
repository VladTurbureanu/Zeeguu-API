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
            word = model.UserWord(*args)
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


def add_bookmark(user, language, original, translation, date, the_context, the_url):

    en = model.Language.find("en")
    url = model.Url.find (the_url)
    text = model.Text(the_context, en, url)
    word1 = model.Word.find(original)
    word2 = model.Word.find(translation)
    rank1 = model.UserWord.find_rank(word1, language)
    rank2 = model.UserWord.find_rank(word2, en)
    w1 = model.UserWord(word1, language,rank1)
    w2 = model.UserWord(word2, en,rank2)
    zeeguu.db.session.add(url)
    zeeguu.db.session.add(text)
    zeeguu.db.session.add(w1)
    zeeguu.db.session.add(w2)
    t1= model.Bookmark(w1,w2, user, text, date)
    zeeguu.db.session.add(t1)

    zeeguu.db.session.commit()
    return


def create_url_and_texts():

    reader = model.Url("www.reader.com")
    session.add(reader)
    mens = model.Text("mens", de, reader)
    homo = model.Text("homo", de, reader)
    zeeguu.db.session.add(mens)
    zeeguu.db.session.add(homo)
    session.commit()
    mensid = mens.id
    homoid = homo.id
    readerid = reader.id

def get_url_and_texts():
    mens = session.query(model.Text).filter_by(content="mens").first()
    homo = session.query(model.Text).filter_by(content="homo").first()
    reader = session.query(model.Url).filter_by(url="www.reader.com").first()

    return mens, homo, reader



if __name__ == "__main__":
    print("testing...")
    zeeguu.app.test_request_context().push()

    de = model.Language.find("de")
    user = model.User("user4@localhost.com", "password3", de)
    session = zeeguu.db.session
    session.add(user)
    print (zeeguu.db.session.commit())
    print "user4 added"

    user = model.User.find("user4@localhost.com")
    zeeguu.db.session.delete(user)
    print (zeeguu.db.session.commit())
    print "user4 removed"

    create_url_and_texts()
    t1, t2, url = get_url_and_texts()
    print t1.content, t2.content, url.url


    session.delete(t1)
    session.delete(t2)
    session.commit()
    if not url.texts:
        print "no more texts..."
    session.delete(url)
    session.commit()

    print "===after delete..."
    t1, t2, url = get_url_and_texts()
    if t1:
        print t1.content
    if t2:
        print t2.content
    if url:
        print url.url


