# -*- coding: utf8 -*-
# Author: Mircea Lungu
#
# The script imports the words
# It takes as first argument a two letter <language code> that conforms to ISO 639-1
# and as a second argument, the file name which contains the word frequencies

# It expects to find a file ./languages/<language code>.txt which contains the words
# of the language in decreasing order of their frequency in the language
# The format of the file is simply one single word per page


import sys
import zeeguu
from zeeguu import RankedWord
from zeeguu.model.language import Language
from zeeguu.model.user_word import UserWord


def remove_duplicates_based_on_case(word_list):
    """
    only return a word form once,
    either when uppercase or lowercase

    :param word_list:
    :return:
    """
    filtered_word_list = []
    lowercase_word_list = set()
    for word in word_list:
        lowercase_word_list.add(word.lower())

    for word in word_list:
        if word.lower() in lowercase_word_list:
            filtered_word_list.append(word)

    return filtered_word_list


def read_words_from_file(word_list_file):
    """
    Reads a given file and returns an array with the
    first word on every line up to the first space.
     This happens to work with the words in the
     https://github.com/hermitdave/FrequencyWords
     which have the format

        word <no-occurrences>

    :param word_list_file:
    :return:
    """
    words_file = open(word_list_file)
    word_lines = words_file.read().splitlines()
    words_list = [w.split(" ")[0] for w in word_lines]

    return words_list


def add_ranked_word_to_db(lang_code, word_list_file, number_of_words):
    """
      Adds the ranks of the words to the DB.


    :param lang_code:
    :param word_list_file:
    :return:
    """
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()

    print ("Looking for language ..." + lang_code)
    language = Language.find(lang_code)

    print "-> Starting to import words in the DB"
    current_line_number = 1
    word_list = remove_duplicates_based_on_case(read_words_from_file(word_list_file))
    word_list = word_list[0:number_of_words]

    for word in word_list:

        if RankedWord.exists(word, language):
            ranked_word = RankedWord.find(word, language)
            ranked_word.set_rank(current_line_number)
        else:
            ranked_word = RankedWord(word, language, current_line_number)
        zeeguu.db.session.add(ranked_word)

        current_line_number += 1
        print_progress_stats(current_line_number, word)

    # Commit everything at once - twice as fast as committing  after every word
    zeeguu.db.session.commit()

    print ('-> Done importing the ranked words in the DB')

    print ('-> Updating word ranks for words already in the DB...')
    update_existing_word_ranks(language)



def update_existing_word_ranks(language):
    for user_word in UserWord.find_by_language(language):
        new_rank = RankedWord.find(user_word.word, language)
        user_word.set_rank(new_rank)
        zeeguu.db.session.add(user_word)
    zeeguu.db.session.commit()


def print_progress_stats(current_line_number, word):
    if current_line_number % 1000 == 0:
        print (str(current_line_number // 1000) + "k words done.")
        print "last word added: " + word


if __name__ == "__main__":
    if len(sys.argv)<4:
        print ("\nusage: python " + sys.argv[0] + " <language code> <file name> <number of words to import>")
        exit()

    # The first argument is the language code cf. ISO 639-1
    lang_code = sys.argv[1]

    # The second argument is the file to process
    word_list_file = sys.argv[2]

    # The third argument is how many words should we put in the DB
    number_of_words = int(sys.argv[3])

    add_ranked_word_to_db(lang_code, word_list_file, number_of_words)

