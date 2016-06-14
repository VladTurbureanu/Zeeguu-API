
# -*- coding: utf8 -*-
import re
import zeeguu
import decimal
from zeeguu.model.exercise_based_probability import ExerciseBasedProbability
from zeeguu.model.encounter_based_probability import EncounterBasedProbability
from zeeguu.model.known_word_probability import KnownWordProbability
from zeeguu.model.user_word import UserWord
from zeeguu import RankedWord
from zeeguu.model.bookmark import Bookmark
from zeeguu.model.language import Language
from zeeguu.model.user import User


def set_default_exercise_based_prob():
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    users = User.find_all()
    languages = Language.all()


    for user in users:
        for language in languages:
            user_words_by_language = UserWord.find_by_language(language)
            for word in user_words_by_language:
                if ExerciseBasedProbability.exists(user,word):
                    prob = ExerciseBasedProbability.find(user,word)
                    bookmarks_by_user_and_word = Bookmark.find_all_by_user_and_word(user,word)
                    total_prob = 0
                    for bookmark in bookmarks_by_user_and_word:
                        prob.calculate_known_bookmark_probability(bookmark)
                        total_prob += float(prob.probability)
                    if bookmarks_by_user_and_word:
                        prob.probability = total_prob/len(bookmarks_by_user_and_word)
                    zeeguu.db.session.commit()
    print ('job1')


def set_default_encounter_based_prob():
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    encounter_prob = EncounterBasedProbability.find_all()
    for prob in encounter_prob:
        for i in range(1,prob.not_looked_up_counter):
            a = decimal.Decimal('1.0')
            b = prob.probability
            c = decimal.Decimal('0.1')
            if b < a:
                prob.probability = b + c
                zeeguu.db.session.commit()
    print ('job2')

def set_know_word_prob():
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    enc_probs = EncounterBasedProbability.find_all()
    ex_probs = ExerciseBasedProbability.find_all()
    for prob in enc_probs:
        user = prob.user
        word = prob.ranked_word.word
        language = prob.ranked_word.language
        user_word = None
        if UserWord.exists(word, language):
            user_word = UserWord.find(word, language)
        if ExerciseBasedProbability.exists(user, user_word):
            ex_prob = ExerciseBasedProbability.find(user, user_word)
            known_word_prob = KnownWordProbability.calculateKnownWordProb(ex_prob.probability, prob.probability)
            known_word_probability_obj = KnownWordProbability.find(user,user_word,prob.ranked_word,known_word_prob)
        else:
            known_word_probability_obj = KnownWordProbability.find(user,None, prob.ranked_word,prob.probability)
        zeeguu.db.session.add(known_word_probability_obj)
        zeeguu.db.session.commit()
    for prob in ex_probs:
        user = prob.user
        language = prob.user_word.language
        word = prob.user_word.word
        ranked_word = None
        if RankedWord.exists(word,language):
            ranked_word = RankedWord.find(word,language)
        if not EncounterBasedProbability.exists(user,ranked_word):
            if UserWord.exists(word, language):
                user_word = UserWord.find(word, language)
                known_word_probability_obj = KnownWordProbability(user,user_word,ranked_word,prob.probability)
                zeeguu.db.session.add(known_word_probability_obj)
                zeeguu.db.session.commit()
    print ('job3')










if __name__ == "__main__":
    set_default_exercise_based_prob()
    set_default_encounter_based_prob()
    set_know_word_prob()


