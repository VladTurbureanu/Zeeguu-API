# -*- coding: utf8 -*-
#
# This file encapsulates the algorithm for computing the difficulty of
# a given text taking.
#
# The algorithm was extracted from a really impressive single method
# that used to live in the /get_difficulty_for_text endpoint implementation
#
# Algo was initially written by Linus Schab
#
# __author__ = 'mircea'
#

from zeeguu import util
from zeeguu.api.model_core import RankedWord

def text_difficulty(known_probabilities, language, personalized, rank_boundary, text):
    """

    :param known_probabilities:
    :param language:
    :param personalized:
    :param rank_boundary:
    :param text:
    :return:
    """

    # Calculate difficulty for each word
    words = util.split_words_from_text(text['content'])
    word_difficulties = []

    for word in words:
        ranked_word = RankedWord.find_cache(word, language)
        word_difficulty = word_difficulty(known_probabilities, personalized, rank_boundary, ranked_word, word)
        word_difficulties.append(word_difficulty)

    # Uncomment to print data for histogram generation
    # text.generate_histogram(word_difficulties)
    # Median difficulty for text
    word_difficulties.sort()
    center = int(round(len(word_difficulties) / 2, 0))
    difficulty_median = word_difficulties[center]
    # Average difficulty for text
    difficulty_average = sum(word_difficulties) / float(len(word_difficulties))
    difficulty_scores = dict(score_median=difficulty_median, score_average=difficulty_average, id=text['id'])
    return difficulty_scores


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

