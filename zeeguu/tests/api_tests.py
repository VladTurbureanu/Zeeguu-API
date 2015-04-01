import zeeguu_testcase
# Always must be imported first
# it sets the test DB

import unittest
import zeeguu.populate
import zeeguu.model
from zeeguu.model import User
from zeeguu import util
import json

class API_Tests(zeeguu_testcase.ZeeguuTestCase):

    def test_logout(self):
        self.logout()
        rv = self.app.get('/recognize')
        assert 'Redirecting' in rv.data

    def test_bookmark_from_android(self):
        formData = dict(
            url='android:app',
            context='User uploaded sentence / user uploaded picture / pre-existing Context (e.g. Harry Potter Book)!',
            title='Zeeguu for Android')
        rv = self.api_post('/bookmark_with_context/de/befurchten/en/fear',formData)
        assert rv.data == "OK"
        t = zeeguu.model.Url.find("android:app","Songs by Iz")

        assert t != None

        rv = self.api_get('/bookmarks')
        assert 'befurchten' in rv.data
        assert 'Zeeguu for Android' in rv.data


    def test_bookmark_without_title_should_fail(self):
        formData = dict(
            url='http://mir.lu',
            context='somewhere over the rainbowwwwwwwww')
        rv = self.api_post('/bookmark_with_context/de/sondern/en/but', formData)
        assert rv.data == "OK"

    def test_delete_bookmark(self):
        rv = self.api_get('/bookmarks_by_day/with_context')
        bookmarks_by_day_dict_before_delete = json.loads(rv.data)
        bookmarks_on_first_date_before_delete = bookmarks_by_day_dict_before_delete[0]['bookmarks']
        first_bookmark_on_first_date_id = bookmarks_on_first_date_before_delete [0] ['id']
        assert any(bookmark['id'] == first_bookmark_on_first_date_id for bookmark in bookmarks_on_first_date_before_delete)
        assert first_bookmark_on_first_date_id is not None
        rv = self.api_post('/delete_bookmark/'+ str(first_bookmark_on_first_date_id))
        assert rv.data == "OK"
        rv = self.api_get('/bookmarks_by_day/with_context')
        bookmarks_by_day_dict_after_delete = json.loads(rv.data)
        bookmarks_on_first_date_after_delete = bookmarks_by_day_dict_after_delete[0]['bookmarks']
        assert not any(bookmark['id'] == first_bookmark_on_first_date_id for bookmark in bookmarks_on_first_date_after_delete)

    def test_create_new_exercise(self):
        rv = self.api_post('/create_new_exercise/Correct/Recognize/10000/2')
        assert rv.data =="OK"
        rv = self.api_post('/create_new_exercise/Correct/Recogniz/10000/3')
        assert rv.data =="FAIL"

    def test_get_exercise_history_for_bookmark(self):
       rv = self.api_get('/get_exercise_history_for_bookmark/3')
       assert "Correct" not in rv.data
       rv = self.api_post('/create_new_exercise/Correct/Recognize/10000/3')
       assert rv.data =="OK"
       rv = self.api_post('/create_new_exercise/Typo/Translate/10000/3')
       assert rv.data =="OK"
       rv = self.api_get('/get_exercise_history_for_bookmark/3')
       assert "Correct" in rv.data
       assert "Translate" in rv.data

    def test_add_new_translation_to_bookmark(self):
        rv = self.api_post('/add_new_translation_to_bookmark/women/1')
        assert rv.data =="OK"
        rv = self.api_get('/get_translations_of_bookmark/2')
        translations_dict_of_bookmark = json.loads(rv.data)
        first_translation_word_of_bookmark = translations_dict_of_bookmark[0]['word']
        rv = self.api_post('/add_new_translation_to_bookmark/'+str(first_translation_word_of_bookmark)+'/2')
        assert rv.data == 'FAIL'

    def test_delete_translation_of_bookmark(self):
        rv = self.api_get('/get_translations_of_bookmark/2')
        translations_dict_of_bookmark = json.loads(rv.data)
        first_word_translation_of_bookmark = translations_dict_of_bookmark[0]['word']
        rv = self.api_post('/delete_translation_of_bookmark/2/'+str(first_word_translation_of_bookmark))
        assert rv.data =='FAIL'
        rv = self.api_post('/add_new_translation_to_bookmark/women/2')
        rv = self.api_get('/get_translations_of_bookmark/2')
        translations_dict_of_bookmark = json.loads(rv.data)
        first_word_translation_of_bookmark = translations_dict_of_bookmark[0]['word']
        assert any (translation['word'] == first_word_translation_of_bookmark for translation in translations_dict_of_bookmark)
        assert any(translation['word'] == 'women' for translation in translations_dict_of_bookmark)
        rv = self.api_post('/delete_translation_of_bookmark/2/wome')
        assert rv.data == 'FAIL'
        rv = self.api_post('/delete_translation_of_bookmark/2/'+str(first_word_translation_of_bookmark))
        assert rv.data =='OK'
        rv = self.api_get('/get_translations_of_bookmark/2')
        translations_dict_of_bookmark = json.loads(rv.data)
        assert not any(translation['word'] == first_word_translation_of_bookmark for translation in translations_dict_of_bookmark)


    def test_get_translations_of_bookmark(self):
       rv = self.api_get('/get_translations_of_bookmark/2')
       translations_dict_bookmark_before_add = json.loads(rv.data)
       assert len(translations_dict_bookmark_before_add) ==1
       first_translation_word = translations_dict_bookmark_before_add[0]['word']
       assert any(translation['word'] == first_translation_word for translation in translations_dict_bookmark_before_add)
       rv = self.api_post('/add_new_translation_to_bookmark/women/2')
       assert rv.data == "OK"
       rv = self.api_get('/get_translations_of_bookmark/2')
       translations_dict_bookmark_after_add = json.loads(rv.data)
       assert len(translations_dict_bookmark_after_add) ==2
       assert first_translation_word!= 'women'
       assert any(translation['word'] == first_translation_word for translation in translations_dict_bookmark_after_add)
       assert any(translation['word'] == 'women' for translation in translations_dict_bookmark_after_add)

    def test_get_count_asked_outcome(self):
        rv1 = self.api_get('/get_count_asked_outcome/I know')
        rv2 = self.api_post('/create_new_exercise/I know/Recognize/10000/2')
        rv2 = self.api_get('/get_count_asked_outcome/I know')
        assert int(rv1.data) +1 == int(rv2.data)
        rv2 = self.api_get('/get_count_asked_outcome/I kno')
        int(rv2.data)==-1
        formData = dict(
            url='http://mir.lu',
            context='sondern machte ab')
        rv0 = self.api_get('/get_count_asked_outcome/I know')
        rv1 = self.api_get('/get_count_asked_outcome/Do not know')
        rv2 = self.api_post('/bookmark_with_context/de/sondern/en/but', formData)
        rv2 = self.api_get('/get_count_asked_outcome/Do not know')
        assert int(rv2.data) == int(rv1.data) +1
        rv2 = self.api_get('/get_count_asked_outcome/I know')
        assert int(rv0.data)+2 == int(rv2.data)



    def test_set_language(self):
        rv = self.api_post('/learned_language/it')
        rv = self.api_post('/native_language/fr')
        assert "OK" in rv.data
        rv = self.api_get('/learned_language')
        assert rv.data== "it"
        rv = self.api_get('/native_language')
        assert rv.data== "fr"


    def test_available_languages(self):
        rv = self.api_get('/available_languages')
        print rv.data

    def test_get_language(self):
        rv = self.api_get('/learned_language')
        print rv.data

    def test_get_bookmarks_by_date(self):
        rv = self.api_get('/bookmarks_by_day/with_context')

        elements = json.loads(rv.data)
        some_date = elements[0]
        assert some_date ["date"]

        some_bookmark = some_date ["bookmarks"][0]
        for key in ["from", "to", "id", "context", "title", "url"]:
            assert key in some_bookmark

        # if we don't pass the context argument, we don't get
        # the context
        rv = self.api_get('/bookmarks_by_day/no_context')
        elements = json.loads(rv.data)
        some_date = elements[0]
        some_bookmark = some_date ["bookmarks"][0]
        assert not "context" in some_bookmark


    def test_translate(self):
        rv = self.api_get('/translate_from_to/frauen/de/en')
        assert rv.data == "women"

        formData = dict(
            url='http://mir.lu',
            context='somewhere over the rainbowwwwwwwww')
        rv = self.api_post('/translate_with_context/kinder/de/en', formData)
        assert rv.data == "children"




    def test_password_hash(self):
        p1 = "test"
        p2 = "pass"
        user = User.find("i@mir.lu")

        hash1 = util.password_hash(p1,user.password_salt)
        hash2 = util.password_hash(p2, user.password_salt)
        assert hash1 != hash2

        assert user.authorize("i@mir.lu", "pass") != None


if __name__ == '__main__':
    unittest.main()
