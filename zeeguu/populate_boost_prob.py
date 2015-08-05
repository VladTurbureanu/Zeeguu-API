
# -*- coding: utf8 -*-
import re
import zeeguu
import decimal
from zeeguu.model import WordRank, Language,Bookmark, UserWord, User, ExerciseBasedProbability, EncounterBasedProbability,AggregatedProbability



def set_default_exercise_based_prob():
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    users = User.find_all()
    languages = Language.all()


    for user in users:
        for language in languages:
            user_word = UserWord.find_by_language(language)
            for word in user_word:
                if ExerciseBasedProbability.exists(user,word):
                    prob = ExerciseBasedProbability.find(user,word)
                    bookmarks_by_user_and_word = Bookmark.find_all_by_user_and_word(user,word)
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
    encounter_prob = EncounterBasedProbability.find_all()
    for prob in encounter_prob:
        for i in range(1,prob.count_not_looked_up):
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
    enc_probs = EncounterBasedProbability.find_all()
    ex_probs = ExerciseBasedProbability.find_all()
    for prob in enc_probs:
        user = prob.user
        word = prob.word_rank.word
        language = prob.word_rank.language
        user_word = None
        if UserWord.exists(word, language):
            user_word = UserWord.find(word, language)
        if ExerciseBasedProbability.exists(user, user_word):
            ex_prob = ExerciseBasedProbability.find(user, user_word)
            aggreg_prob = AggregatedProbability.calculateAggregatedProb(ex_prob.probability, prob.probability)
            aggreg_probability_obj = AggregatedProbability.find(user,user_word,prob.word_rank,aggreg_prob)
        else:
            aggreg_probability_obj = AggregatedProbability.find(user,None, prob.word_rank,prob.probability)
        zeeguu.db.session.add(aggreg_probability_obj)
        zeeguu.db.session.commit()
    for prob in ex_probs:
        user = prob.user
        language = prob.user_word.language
        word = prob.user_word.word
        word_rank = None
        if WordRank.exists(word,language):
            word_rank = WordRank.find(word,language)
        if not EncounterBasedProbability.exists(user,word_rank):
            if UserWord.exists(word, language):
                user_word = UserWord.find(word, language)
                aggreg_probability_obj = AggregatedProbability(user,user_word,word_rank,prob.probability)
                zeeguu.db.session.add(aggreg_probability_obj)
                zeeguu.db.session.commit()
    print 'job3'










if __name__ == "__main__":
    set_default_exercise_based_prob()
    set_default_encounter_based_prob()
    set_aggregated_prob()


