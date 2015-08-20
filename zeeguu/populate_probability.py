
# -*- coding: utf8 -*-
import re
import zeeguu
from zeeguu.model import RankedWord, Language,Bookmark,User,ExerciseBasedProbability, EncounterBasedProbability
from re import compile as _Re



def set_default_exercise_based_prob():
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    bookmarks = Bookmark.find_all()
    for bookmark in bookmarks:
        prob = ExerciseBasedProbability.find(bookmark.user, bookmark.origin)
        zeeguu.db.session.add(prob)
        zeeguu.db.session.commit()
    print 'job1'

def set_default_encounter_based_prob():
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    default_probability = 0.5
    languages = Language.all()
    users = User.find_all()
    for user in users:
        for lang in languages:
            marked_words_of_user_in_text = []
            words_of_all_bookmarks_content = []
            for bookmark in Bookmark.find_by_specific_user(user):
                if bookmark.origin.language == lang:
                    # bookmark_content_words = re.sub("[^\w]", " ",  bookmark.text.content).split()
                    bookmark_content_words = re.findall(r'(?u)\w+', bookmark.text.content)
                    words_of_all_bookmarks_content.extend(bookmark_content_words)
                    marked_words_of_user_in_text.append(bookmark.origin.word)
            words_known_from_user= [word for word in words_of_all_bookmarks_content if word not in marked_words_of_user_in_text]
            for word_known in words_known_from_user:
                if RankedWord.exists(word_known, lang):
                   rank = RankedWord.find(word_known, lang)
                   if EncounterBasedProbability.exists(user, rank):
                       prob = EncounterBasedProbability.find(user,rank, default_probability)
                       prob.not_looked_up_counter +=1
                   else:
                       prob = EncounterBasedProbability.find(user,rank,default_probability)
                       zeeguu.db.session.add(prob)
    zeeguu.db.session.commit()
    print 'job2'





if __name__ == "__main__":
    set_default_exercise_based_prob()
    set_default_encounter_based_prob()


