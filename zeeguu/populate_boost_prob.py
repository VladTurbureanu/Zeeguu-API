
# -*- coding: utf8 -*-
import re
import zeeguu
import decimal
from zeeguu import model



def set_default_exercise_based_prob():
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    users = model.User.find_all()
    languages = model.Language.all()


    for user in users:
        for language in languages:
            user_words = model.UserWord.find_by_language(language)
            for word in user_words:
                if model.ExerciseBasedProbability.exists(user,word):
                    prob = model.ExerciseBasedProbability.find(user,word)
                    bookmarks_by_user_and_word = model.Bookmark.find_all_by_user_and_word(user,word)
                    total_prob = 0
                    for bookmark in bookmarks_by_user_and_word:
                        prob.calculate_bookmark_probability(bookmark)
                        total_prob += float(prob.probability)
                    if bookmarks_by_user_and_word:
                        prob.probability = total_prob/len(bookmarks_by_user_and_word)
                    zeeguu.db.session.commit()
    print 'job1'


def set_default_encounter_based_prob():
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    encounter_prob = model.EncounterBasedProbability.find_all()
    for prob in encounter_prob:
        for i in range(0,prob.count_not_looked_up):
            a = decimal.Decimal('1.0')
            b = prob.probability
            c = decimal.Decimal('0.1')
            if b < a:
                prob.probability = b + c
                zeeguu.db.session.commit()
    print 'job2'

def set_aggregated_prob():
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    languages = model.Language.all()
    enc_probs = model.EncounterBasedProbability.find_all()
    ex_probs = model.ExerciseBasedProbability.find_all()
    for prob in enc_probs:
        user = prob.user
        word = prob.word_ranks.word
        language = prob.word_ranks.language
        user_word = None
        if model.UserWord.exists(word, language):
            user_word = model.UserWord.find(word, language)
        if model.ExerciseBasedProbability.exists(user, user_word):
            ex_prob = model.ExerciseBasedProbability.find(user, user_word)
            aggreg_prob = model.AggregatedProbability.calculateAggregatedProb(ex_prob.probability, prob.probability)
            aggreg_probability_obj = model.AggregatedProbability.find(user,user_word,prob.word_ranks,aggreg_prob)
        else:
            aggreg_probability_obj = model.AggregatedProbability.find(user,None, prob.word_ranks,prob.probability)
        zeeguu.db.session.add(aggreg_probability_obj)
        zeeguu.db.session.commit()
    for prob in ex_probs:
        user = prob.user
        language = prob.user_words.language
        word = prob.user_words.word
        word_rank = None
        if model.WordRank.exists(word,language):
            word_rank = model.WordRank.find(word,language)
        if not model.EncounterBasedProbability.exists(user,word_rank):
            if model.UserWord.exists(word, language):
                user_word = model.UserWord.find(word, language)
                aggreg_probability_obj = model.AggregatedProbability(user,user_word,None,prob.probability)
                zeeguu.db.session.add(aggreg_probability_obj)
                zeeguu.db.session.commit()
    print 'job3'










if __name__ == "__main__":
    # set_default_exercise_based_prob()
    # set_default_encounter_based_prob()
    set_aggregated_prob()


