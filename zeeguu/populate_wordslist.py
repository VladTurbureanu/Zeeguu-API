
# -*- coding: utf8 -*-
import re

import zeeguu
from zeeguu import model

def delete_duplicates(seq, current=None):
   # order preserving
   if current is None:
       def current(x): return x
   seen = {}
   result = []
   for item in seq:
       marker = current(item)
       # in old Python versions:
       # if seen.has_key(marker)
       # but in new ones:
       if marker in seen: continue
       seen[marker] = 1
       result.append(item)
   return result


def filter_word_list(word_list):
    filtered_word_list = []
    lowercase_word_list = []
    for word in word_list:
        lowercase_word_list.append(word.lower)
    lowercase_word_list = delete_duplicates(lowercase_word_list)
    for lc_word in lowercase_word_list:
        for word in word_list:
            if word.lower  == lc_word:
                filtered_word_list.append(word)
                break
    return filtered_word_list

def word_list(lang_code):
    words_file = open("languages/"+lang_code+".txt")
    words_list = words_file.read().splitlines()
    return words_list




def add_words_to_db(lang_code):
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    for word in filter_word_list(word_list(lang_code)):
        w = model.Word.find(word.decode('utf-8'))
        zeeguu.db.session.add(w)
    print 'karan the best'
    zeeguu.db.session.commit()

def add_word_ranks_to_db(lang_code):
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    from_lang = model.Language.find(lang_code)
    initial_line_number = 1
    for word in filter_word_list(word_list(lang_code)):
        w = model.Word.find(word.decode('utf-8'))
        zeeguu.db.session.add(w)
        r = model.WordRank(w, from_lang,initial_line_number)
        zeeguu.db.session.add(r)
        initial_line_number+=1
    print 'karan the worst'
    zeeguu.db.session.commit()

def change_db(lang_code):
    add_words_to_db(lang_code)
    add_word_ranks_to_db(lang_code)












if __name__ == "__main__":
    change_db('de')

