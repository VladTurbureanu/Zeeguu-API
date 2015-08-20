
# -*- coding: utf8 -*-
import re

import zeeguu
import sys
from zeeguu.model import RankedWord, Language


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


def word_list(lang_code):
    words_file = open("languages/"+lang_code+".txt")
    words_list = words_file.read().splitlines()
    return words_list




def add_ranked_words_to_db(lang_code):
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    from_lang = Language.find(lang_code)
    initial_line_number = 1
    for word in filter_word_list(word_list(lang_code)):
        r = RankedWord(word.lower(), from_lang,initial_line_number)
        zeeguu.db.session.add(r)
        initial_line_number+=1
    zeeguu.db.session.commit()




if __name__ == "__main__":
    try:
        add_ranked_words_to_db(sys.argv[1])
    except :
        print "Usage: add_ranked_word <language_code>"
