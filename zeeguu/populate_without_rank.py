# -*- coding: utf8 -*-
import re

import zeeguu
import datetime
from zeeguu import model



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

if __name__ == "__main__":
    print len(word_list('de copy'))
    print len(filter_word_list(word_list('de copy')))