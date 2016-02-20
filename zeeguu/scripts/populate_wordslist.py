
# -*- coding: utf8 -*-
import sys
import zeeguu
from zeeguu import model



def filter_word_list(word_list):
    filtered_word_list = []
    lowercase_word_list = set()
    for word in word_list:
        lowercase_word_list.add(word)

    for word in word_list:
        if word.lower() in lowercase_word_list:
            filtered_word_list.append(word)

    return filtered_word_list


def word_list(lang_code):
    words_file = open("languages/"+lang_code+".txt")
    words_list = words_file.read().splitlines()
    return words_list




def add_ranked_word_to_db(lang_code):
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    print ("looking for language ..." + lang_code)
    from_lang = model.Language.find(lang_code)
    initial_line_number = 1

    for word in filter_word_list(word_list(lang_code)):
        r = model.RankedWord(word.lower(), from_lang,initial_line_number)
        zeeguu.db.session.add(r)
        initial_line_number+=1
        if (initial_line_number % 1000 == 0):
            print (str(initial_line_number // 1000) + "k words done.")
    zeeguu.db.session.commit()

    print ('done importing the words in the DB')


def change_db(lang_code):
    add_ranked_word_to_db(lang_code)


if __name__ == "__main__":
    if len(sys.argv)<2:
        print ("pass the language code that you want to import")

    change_db(sys.argv[1])

