# -*- coding: utf8 -*-
#
# This file encapsulates the algorithm for computing the difficulty of
# a given text taking.
#
# The algorithm was extracted from a really impressive single method
# that used to live in the /get_difficulty_for_text endpoint implementation
#
# Original algo implementation was initially written by Linus Schab
#
# __author__ = 'mircea'
#

from zeeguu.the_librarian.text import split_words_from_text
from zeeguu.api.model_core import RankedWord


def text_difficulty(text, language, known_probabilities, rank_boundary, personalized):
    """
    :param known_probabilities: the probabilities that the user knows individual words
    :param language: the learned language
    :param personalized: if true, the text_difficulty is computed with personalization
    :param rank_boundary: 10.000 words
    :param text: text to analyse
    :return:
    """
    word_difficulties = []

    # Calculate difficulty for each word
    words = split_words_from_text(text['content'])

    for word in words:
        ranked_word = RankedWord.find_cache(word, language)
        difficulty = word_difficulty(known_probabilities, personalized, rank_boundary, ranked_word, word)
        word_difficulties.append(difficulty)

    # Average difficulty for text
    difficulty_average = sum(word_difficulties) / float(len(word_difficulties))
    return difficulty_average


def word_difficulty(known_probabilities, personalized, rank_boundary, ranked_word, word):
    """
    # estimate the difficulty of a word, given:
        :param known_probabilities:
        :param personalized:
        :param rank_boundary:
        :param ranked_word:
        :param word:

    :return: a normalized value where 0 is (easy) and 1 is (hard)
    """

    # Assume word is difficult and unknown
    estimated_difficulty = 1.0

    if not ranked_word:
        return estimated_difficulty

    # Check if the user knows the word
    try:
        known_probability = known_probabilities[word]  # Value between 0 (unknown) and 1 (known)
    except KeyError:
        known_probability = None

    if personalized and known_probability is not None:
        estimated_difficulty -= float(known_probability)
    elif ranked_word.rank <= rank_boundary:
        word_frequency = (rank_boundary - (
            ranked_word.rank - 1)) / rank_boundary  # Value between 0 (rare) and 1 (frequent)
        estimated_difficulty -= word_frequency
    return estimated_difficulty

