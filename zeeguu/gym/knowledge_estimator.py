import flask
from zeeguu.api.model_core import db
from zeeguu.api.model_core import Bookmark, ExerciseBasedProbability, RankedWord, EncounterBasedProbability, KnownWordProbability


# TODO: Possible bug: here we might have to lookup also based on language
def update_probabilities_for_word(word):

    bookmarks_for_this_word = Bookmark.find_all_by_user_and_word(flask.g.user, word)

    ex_prob = ExerciseBasedProbability.find(flask.g.user, word)
    total_prob = 0
    for b in bookmarks_for_this_word:
        ex_prob.calculate_known_bookmark_probability(b)
        total_prob += float(ex_prob.probability)
    ex_prob.probability = total_prob / len(bookmarks_for_this_word)

    if RankedWord.exists(word.word, word.language):
        ranked_word = RankedWord.find(word.word, word.language)
        if EncounterBasedProbability.exists(flask.g.user, ranked_word):
            enc_prob = EncounterBasedProbability.find(flask.g.user, ranked_word)
            known_word_prob = KnownWordProbability.find(flask.g.user, word, ranked_word)
            known_word_prob.probability = KnownWordProbability.calculateKnownWordProb(ex_prob.probability,
                                                                                      enc_prob.probability)
        else:
            known_word_prob = KnownWordProbability.find(flask.g.user, word, ranked_word)
            known_word_prob.probability = ex_prob.probability

    db.session.commit()