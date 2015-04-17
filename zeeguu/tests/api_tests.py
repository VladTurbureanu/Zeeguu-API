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

    def test_contribute_from_android(self):
        formData = dict(
            url='android:app',
            context='User uploaded sentence / user uploaded picture / pre-existing Context (e.g. Harry Potter Book)!',
            title='Zeeguu for Android')
        rv = self.api_post('/contribute_with_context/de/befurchten/en/fear',formData)
        assert rv.data == "OK"
        t = zeeguu.model.Url.find("android:app","Songs by Iz")

        assert t != None

        rv = self.api_get('/contributions')
        assert 'befurchten' in rv.data
        assert 'Zeeguu for Android' in rv.data


    def test_contribute_without_title_should_fail(self):
        formData = dict(
            url='http://mir.lu',
            context='somewhere over the rainbowwwwwwwww')
        rv = self.api_post('/contribute_with_context/de/sondern/en/but', formData)
        assert rv.data == "OK"

    def test_delete_contribution(self):
        rv = self.api_get('/contribs_by_day/with_context')
        contribs_by_day_dict_before_delete = json.loads(rv.data)
        contribs_on_first_date_before_delete = contribs_by_day_dict_before_delete[0]['contribs']
        first_contrib_on_first_date_id = contribs_on_first_date_before_delete [0] ['id']
        assert contribs_on_first_date_before_delete[0]["from_language"]=="de"
        assert any(contrib['id'] == first_contrib_on_first_date_id for contrib in contribs_on_first_date_before_delete)
        assert first_contrib_on_first_date_id is not None
        rv = self.api_post('/delete_contribution/'+ str(first_contrib_on_first_date_id))
        assert rv.data == "OK"
        rv = self.api_get('/contribs_by_day/with_context')
        contribs_by_day_dict_after_delete = json.loads(rv.data)
        contribs_on_first_date_after_delete = contribs_by_day_dict_after_delete[0]['contribs']
        assert not any(contrib['id'] == first_contrib_on_first_date_id for contrib in contribs_on_first_date_after_delete)

    def test_create_new_exercise(self):
        rv = self.api_post('/create_new_exercise/Correct/Recognize/10000/2')
        assert rv.data =="OK"
        rv = self.api_post('/create_new_exercise/Correct/Recogniz/10000/3')
        assert rv.data =="FAIL"

    def test_get_exercise_history_for_contribution(self):
       rv = self.api_get('/get_exercise_history_for_contribution/3')
       assert "Correct" not in rv.data
       rv = self.api_post('/create_new_exercise/Correct/Recognize/10000/3')
       assert rv.data =="OK"
       rv = self.api_post('/create_new_exercise/Typo/Translate/10000/3')
       assert rv.data =="OK"
       rv = self.api_get('/get_exercise_history_for_contribution/3')
       assert "Correct" in rv.data
       assert "Translate" in rv.data


    def test_get_contribs(self):
        rv = self.api_get('/contribs')
        assert "Wald" in rv.data


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


    def test_create_user(self):
        formData = dict(
            username= "gigi",
            password= "lala"
        )
        rv = self.api_post('/add_user/i@i.la',formData)
        print rv.data
        assert rv.data > 1


    def test_get_language(self):
        rv = self.api_get('/learned_language')
        print rv.data

    def test_get_contributions_by_date(self):
        rv = self.api_get('/contribs_by_day/with_context')

        elements = json.loads(rv.data)
        some_date = elements[0]
        assert some_date ["date"]

        some_contrib = some_date ["contribs"][0]
        for key in ["from", "to", "id", "context", "title", "url"]:
            assert key in some_contrib

        # if we don't pass the context argument, we don't get
        # the context
        rv = self.api_get('/contribs_by_day/no_context')
        elements = json.loads(rv.data)
        some_date = elements[0]
        some_contrib = some_date ["contribs"][0]
        assert not "context" in some_contrib


    def test_translate(self):
        rv = self.api_get('/translate_from_to/Z%C3%B6llner/de/en')
        assert rv.data == "Publican"

        formData = dict(
            url='http://mir.lu',
            context='somewhere over the rainbowwwwwwwww')
        rv = self.api_post('/translate_with_context/Kinder/de/en', formData)
        assert rv.data == "Children"




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
