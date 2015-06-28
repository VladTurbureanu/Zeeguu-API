
# -*- coding: utf8 -*-
import re
import zeeguu
from zeeguu import model



def set_default_exercise_based_prob():
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    bookmarks = model.Bookmark.find_all()
    for bookmark in bookmarks:
        prob = model.ExerciseBasedProbability.find(bookmark.user, bookmark.origin)
        zeeguu.db.session.add(prob)
        zeeguu.db.session.commit()
    print 'job1'

def set_default_encounter_based_prob():
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    default_probability = 0.5
    languages = model.Language.all()
    users = model.User.find_all()
    for user in users:
        for lang in languages:
            marked_words_of_user_in_text = []
            words_of_all_bookmarks_content = []
            for bookmark in model.Bookmark.find_by_specific_user(user):
                if bookmark.origin.language == lang:
                    bookmark_content_words = re.sub("[^\w]", " ",  bookmark.text.content).split()
                    words_of_all_bookmarks_content.extend(bookmark_content_words)
                    marked_words_of_user_in_text.append(bookmark.origin.word)
            words_known_from_user= [word for word in words_of_all_bookmarks_content if word not in marked_words_of_user_in_text]
            for word_known in words_known_from_user:
                if model.WordRank.exists(word_known.lower(), lang):
                   rank = model.WordRank.find(word_known.lower(), lang)
                   if model.EncounterBasedProbability.exists(user, rank):
                       prob = model.EncounterBasedProbability.find(user,rank, default_probability)
                       prob.count_not_looked_up +=1
                   else:
                       prob = model.EncounterBasedProbability.find(user,rank,default_probability)
                       zeeguu.db.session.add(prob)
    zeeguu.db.session.commit()
    print 'job2'





if __name__ == "__main__":
    set_default_exercise_based_prob()
    set_default_encounter_based_prob()


