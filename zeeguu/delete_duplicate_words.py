# -*- coding: utf8 -*-


import zeeguu
from zeeguu import model

def delete_duplicates(lang_code):
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()
    word_temp_list = []
    language_id = model.Language.find(lang_code)
    for rank in model.WordRank.find_all(language_id):
        if rank.word not in word_temp_list:
            word_temp_list.append(rank.word)
        else:
            zeeguu.db.session.delete(rank)
    zeeguu.db.session.commit()




if __name__ == "__main__":
   delete_duplicates('de')