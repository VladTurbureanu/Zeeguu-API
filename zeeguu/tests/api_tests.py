# coding=utf-8
import zeeguu_testcase
# Always must be imported first
# it sets the test DB

import unittest
import zeeguu.populate
import zeeguu.model
from zeeguu.api.model_core import User, RankedWord, Text, Language, Url, \
    Bookmark
from zeeguu import util
import json
import re
import time


sondernExampleData = dict(
    url='http://mir.lu/examples_with_karan',
    context='Wir arbeiten nicht sondern schlafen')

strassenExampleform_data = dict(
    url='http://mir.lu',
    context='chilling on the streets')



class API_Tests(zeeguu_testcase.ZeeguuTestCase):

    def test_logout(self):
        self.logout()
        rv = self.app.get('/recognize')
        assert 'Redirecting' in rv.data


    def test_logout_API(self):
        rv = self.api_get('/logout_session')
        assert rv.data == "OK"
        rv = self.api_get('/validate')
        assert rv.status== "401 UNAUTHORIZED"


    def test_bookmark_from_android(self):
        form_data = dict(
            url='http://mir.lu',
            context='somewhere over the rainbowwwwwwwww',
            title="lal")
        self.api_post('/bookmark_with_context/de/sondern/en/but', form_data)
        t = zeeguu.model.Url.find("android:app","Songs by Iz")
        assert t != None

        bookmarks = self.api_get_json('/get_learned_bookmarks/de')
        assert any(u'sondern' in y.values() for y in bookmarks )



    def test_bookmark_without_title_should_fail(self):
        form_data = dict(
            url='http://mir.lu',
            context='somewhere over the rainbowwwwwwwww')
        rv = self.api_post('/bookmark_with_context/de/sondern/en/but', form_data)
        added_bookmark_id = int(rv.data)
        elements = self.api_get_json('/bookmarks_by_day/with_context')

        first_date = elements[0]
        latest_bookmark_id = int(first_date["bookmarks"][0]['id'])
        assert latest_bookmark_id  == added_bookmark_id


    def test_get_probably_known(self):

        probably_known_words = self.api_get_json('/get_probably_known_words/de')

        # Initially none of the words is known
        assert not any(word['word'] == 'gute' for word in probably_known_words)
        assert not any(word['word'] == 'nacht' for word in probably_known_words)
        assert not any(word['word'] == 'sondern' for word in probably_known_words)

        exampleform_data = dict(
            url='http://mir.lu',
            context='gute nacht sondern')

        # Bookmark sondern
        sondernId = (self.api_post('/bookmark_with_context/de/sondern/en/but', exampleform_data)).data


        # User declares that sondern is "Too Easy" in an exercise
        self.api_post('/gym/create_new_exercise/Too easy/Recognize/10000/'+ sondernId)
        # Thus, sondern goes to the Probably known words
        probably_known_words = self.api_get_json('/get_probably_known_words/de')
        assert any(word['word'] == 'sondern' for word in probably_known_words)

        # User requests "Show solution" for sondern
        self.api_post('/gym/create_new_exercise/Show solution/Recognize/10000/'+ sondernId)
        # Thus sondern goes to unknown words again
        probably_known_words = self.api_get_json('/get_probably_known_words/de')
        assert not any(word['word'] == 'sondern' for word in probably_known_words)

        # Bookmarking the word several other times...
        self.api_post('/bookmark_with_context/de/sondern/en/but', exampleform_data)
        self.api_post('/bookmark_with_context/de/sondern/en/but', exampleform_data)
        # doesn't change anything evidently. ML: Why is this?
        probably_known_words = self.api_get_json('/get_probably_known_words/de')
        assert not any(word['word'] == 'sondern' for word in probably_known_words)






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
        rv = self.api_post('/gym/create_new_exercise/Correct/Recognize/10000/2')
        assert rv.data =="OK"
        rv = self.api_post('/gym/create_new_exercise/Correct/Recogniz/10000/3')
        assert rv.data =="FAIL"

    def test_get_exercise_log_for_bookmark(self):
       rv = self.api_get('/get_exercise_log_for_bookmark/3')
       assert "Correct" not in rv.data
       rv = self.api_post('/gym/create_new_exercise/Correct/Recognize/10000/3')
       assert rv.data =="OK"
       rv = self.api_post('/gym/create_new_exercise/Typo/Translate/10000/3')
       assert rv.data =="OK"
       rv = self.api_get('/get_exercise_log_for_bookmark/3')
       assert "Correct" in rv.data
       assert "Translate" in rv.data

    def test_add_new_translation_to_bookmark(self):
        rv = self.api_post('/add_new_translation_to_bookmark/women/1')
        assert rv.data =="OK"
        rv = self.api_get('/get_translations_for_bookmark/2')
        translations_dict_of_bookmark = json.loads(rv.data)
        first_translation_word_of_bookmark = translations_dict_of_bookmark[0]['word']
        rv = self.api_post('/add_new_translation_to_bookmark/'+str(first_translation_word_of_bookmark)+'/2')
        assert rv.data == 'FAIL'

    def test_delete_translation_from_bookmark(self):
        rv = self.api_get('/get_translations_for_bookmark/2')
        translations_dict_of_bookmark = json.loads(rv.data)
        first_word_translation_of_bookmark = translations_dict_of_bookmark[0]['word']
        rv = self.api_post('/delete_translation_from_bookmark/2/'+str(first_word_translation_of_bookmark))
        assert rv.data =='FAIL'
        rv = self.api_post('/add_new_translation_to_bookmark/women/2')
        rv = self.api_get('/get_translations_for_bookmark/2')
        translations_dict_of_bookmark = json.loads(rv.data)
        first_word_translation_of_bookmark = translations_dict_of_bookmark[0]['word']
        assert any (translation['word'] == first_word_translation_of_bookmark for translation in translations_dict_of_bookmark)
        assert any(translation['word'] == 'women' for translation in translations_dict_of_bookmark)
        rv = self.api_post('/delete_translation_from_bookmark/2/wome')
        assert rv.data == 'FAIL'
        rv = self.api_post('/delete_translation_from_bookmark/2/'+str(first_word_translation_of_bookmark))
        assert rv.data =='OK'
        rv = self.api_get('/get_translations_for_bookmark/2')
        translations_dict_of_bookmark = json.loads(rv.data)
        assert not any(translation['word'] == first_word_translation_of_bookmark for translation in translations_dict_of_bookmark)




    def test_delete_bookmark(self):
        rv = self.api_post('/delete_bookmark/2')
        assert rv.data =='OK'
        rv = self.api_post('/delete_bookmark/2')
        assert rv.data == "FAIL"



    def test_get_translations_for_bookmark(self):
       rv = self.api_get('/get_translations_for_bookmark/2')
       translations_dict_bookmark_before_add = json.loads(rv.data)
       assert len(translations_dict_bookmark_before_add) ==1
       first_translation_word = translations_dict_bookmark_before_add[0]['word']
       assert any(translation['word'] == first_translation_word for translation in translations_dict_bookmark_before_add)
       rv = self.api_post('/add_new_translation_to_bookmark/women/2')
       assert rv.data == "OK"
       rv = self.api_get('/get_translations_for_bookmark/2')
       translations_dict_bookmark_after_add = json.loads(rv.data)
       assert len(translations_dict_bookmark_after_add) ==2
       assert first_translation_word!= 'women'
       assert any(translation['word'] == first_translation_word for translation in translations_dict_bookmark_after_add)
       assert any(translation['word'] == 'women' for translation in translations_dict_bookmark_after_add)


    def test_get_known_bookmarks(self):
        self.api_post('/bookmark_with_context/de/sondern/en/but rather', sondernExampleData)
        self.api_post('/bookmark_with_context/de/strassen/en/streets', strassenExampleform_data)

        rv = self.api_get('/bookmarks_by_day/with_context')
        bookmarks_by_day = json.loads(rv.data)
        assert any(context['context'] ==  'chilling on the streets' for context in bookmarks_by_day[0]['bookmarks'])
        #assert 'chilling on the streets' == bookmarks_by_day[0]['bookmarks'][0]['context']
        #assert sondernExampleData["context"] == bookmarks_by_day[0]['bookmarks'][1]['context']
        assert any (context ['context'] == sondernExampleData["context"] for context in bookmarks_by_day[0]['bookmarks'])
        latest_bookmark_id = bookmarks_by_day[0]['bookmarks'][0]['id']
        # print bookmarks_by_day[0]

        second_latest_bookmark_id = bookmarks_by_day[0]['bookmarks'][1]['id']
        rv = self.api_get('/get_exercise_log_for_bookmark/'+str(latest_bookmark_id))
        'Too easy' not in rv.data
        rv = self.api_get('/get_exercise_log_for_bookmark/'+str(second_latest_bookmark_id))
        'Too easy' not in rv.data
        self.api_post('/gym/create_new_exercise/Too easy/Recognize/10000/'+ str(latest_bookmark_id))
        rv = self.api_get('/get_known_bookmarks/de')
        known_bookmarks_before = json.loads(rv.data)
        assert any(bookmark['id'] == latest_bookmark_id for bookmark in known_bookmarks_before)
        assert not any(bookmark['id'] == second_latest_bookmark_id for bookmark in known_bookmarks_before)
        self.api_post('/gym/create_new_exercise/Too easy/Recognize/10000/'+ str(second_latest_bookmark_id))
        rv3 = self.api_get('/get_known_bookmarks/de')
        known_bookmarks_after = json.loads(rv3.data)
        assert any(bookmark['id'] == latest_bookmark_id for bookmark in known_bookmarks_after)
        assert any(bookmark['id'] == second_latest_bookmark_id for bookmark in known_bookmarks_after)

        time.sleep(2) # delays for 5 seconds
        self.api_post('/gym/create_new_exercise/Show solution/Recognize/10000/'+ str(second_latest_bookmark_id))
        rv4 = self.api_get('/get_known_bookmarks/de')
        known_bookmarks_after = json.loads(rv4.data)
        assert not any(bookmark['id'] == second_latest_bookmark_id for bookmark in known_bookmarks_after)




    def test_get_known_words(self):
        rv = self.api_post('/bookmark_with_context/de/sondern/en/but', sondernExampleData)
        form_data = dict(
            url='http://mir.lu',
            context='saying hi to girls')
        rv = self.api_post('/bookmark_with_context/de/maedchen/en/girls', form_data)
        form_data = dict(
            url='http://mir.lu',
            context='chilling with the girls')
        rv = self.api_post('/bookmark_with_context/de/maedchen/en/girls', form_data)
        rv = self.api_get('/bookmarks_by_day/with_context')
        bookmarks_by_day = json.loads(rv.data)
        latest_bookmark_id = bookmarks_by_day[0]['bookmarks'][0]['id']
        second_latest_bookmark_id = bookmarks_by_day[0]['bookmarks'][1]['id']
        third_latest_bookmark_id = bookmarks_by_day[0]['bookmarks'][2]['id']
        latest_bookmark_word = bookmarks_by_day[0]['bookmarks'][0]['from']
        second_latest_bookmark_word = bookmarks_by_day[0]['bookmarks'][1]['from']
        third_latest_bookmark_word = bookmarks_by_day[0]['bookmarks'][2]['from']
        rv = self.api_get('/get_known_words/de')
        known_words = json.loads(rv.data)
        known_words_count_before = len(known_words)
        assert not any(word['from'] == latest_bookmark_word for word in known_words)
        rv = self.api_post('/gym/create_new_exercise/Too easy/Recognize/10000/'+ str(latest_bookmark_id))
        rv = self.api_get('/get_known_words/de')
        known_words = json.loads(rv.data)
        assert any(word['word'] == latest_bookmark_word for word in known_words)
        assert known_words_count_before +1 == len(known_words)
        rv = self.api_post('/gym/create_new_exercise/Too easy/Recognize/10000/'+ str(second_latest_bookmark_id))
        rv = self.api_get('/get_known_words/de')
        known_words = json.loads(rv.data)
        assert any(word['word'] == latest_bookmark_word for word in known_words)
        assert any(word['word'] == second_latest_bookmark_word for word in known_words)
        assert known_words_count_before +1 == len(known_words)
        rv = self.api_post('/gym/create_new_exercise/Too easy/Recognize/10000/'+ str(third_latest_bookmark_id))
        rv = self.api_get('/get_known_words/de')
        known_words = json.loads(rv.data)
        assert known_words_count_before +2 == len(known_words)
        assert any(word['word'] == latest_bookmark_word for word in known_words)
        assert any(word['word'] == third_latest_bookmark_word for word in known_words)
        time.sleep(5) # delays for 5 seconds
        rv = self.api_post('/gym/create_new_exercise/Show solution/Recognize/10000/'+ str(third_latest_bookmark_id))
        rv = self.api_get('/get_known_words/de')
        known_words = json.loads(rv.data)
        assert not any(word['word'] == third_latest_bookmark_word for word in known_words)


    def test_get_learned_bookmarks(self):
        form_data = dict(
            url='http://mir.lu',
            context='somewhere over the rainbowwwwwwwww')
        rv = self.api_post('/bookmark_with_context/de/sondern/en/but', form_data)
        # print rv.data
        latest_bookmark_id = json.loads(rv.data)
        #rv = self.api_get('/bookmarks_by_day/with_context')
        #bookmarks_by_day = json.loads(rv.data)
        #latest_bookmark_id = bookmarks_by_day[0]['bookmarks'][0]['id']
        rv = self.api_get('/get_learned_bookmarks/de')
        learned_bookmarks = json.loads(rv.data)
        assert any(bookmark['id'] == latest_bookmark_id for bookmark in learned_bookmarks)
        learned_bookmarks_count = len(learned_bookmarks)
        form_data = dict(
            url='http://mir.lu',
            context='chilling on the streets')
        rv = self.api_post('/bookmark_with_context/de/strassen/en/streets', form_data)
        new_latest_bookmark_id = json.loads(rv.data)
        #rv = self.api_get('/bookmarks_by_day/with_context')
        #bookmarks_by_day = json.loads(rv.data)
        #new_latest_bookmark_id = bookmarks_by_day[0]['bookmarks'][1]['id']
        rv = self.api_get('/get_learned_bookmarks/de')
        learned_bookmarks = json.loads(rv.data)
        assert learned_bookmarks_count +1 == len(learned_bookmarks)
        assert any(bookmark['id'] == latest_bookmark_id for bookmark in learned_bookmarks)
        assert any(bookmark['id'] == new_latest_bookmark_id for bookmark in learned_bookmarks)
        self.api_post('/gym/create_new_exercise/Too easy/Recognize/10000/'+ str(latest_bookmark_id))
        rv = self.api_get('/get_learned_bookmarks/de')
        learned_bookmarks = json.loads(rv.data)
        assert not any(bookmark['id'] == latest_bookmark_id for bookmark in learned_bookmarks)
        assert learned_bookmarks_count== len(learned_bookmarks)
        time.sleep(5)
        self.api_post('/gym/create_new_exercise/Show solution/Recognize/10000/'+ str(latest_bookmark_id))
        rv = self.api_get('/get_learned_bookmarks/de')
        learned_bookmarks = json.loads(rv.data)
        assert learned_bookmarks_count+1== len(learned_bookmarks)
        assert any(bookmark['id'] == latest_bookmark_id for bookmark in learned_bookmarks)

    def test_get_not_looked_up_words(self):
        rv = self.api_get('/bookmarks_by_day/with_context')
        bookmarks_by_day = []
        bookmarks_by_day_with_date = json.loads(rv.data)
        rv = self.api_get('/get_not_looked_up_words/de')
        estimated_user_voc_before = json.loads(rv.data)
        assert not any (bookmark['word'] == 'es' for bookmark in estimated_user_voc_before)
        assert not any (bookmark['word'] == 'an' for bookmark in estimated_user_voc_before)
        assert not any (bookmark['word'] == 'auch' for bookmark in estimated_user_voc_before)
        for i in range(0, len(bookmarks_by_day_with_date)):
            for j in range (0, len(bookmarks_by_day_with_date[i]['bookmarks'])):
                bookmarks_by_day.append(bookmarks_by_day_with_date[i]['bookmarks'][j]['context'])
        for bookmark in bookmarks_by_day:
            bookmark_content_words = re.sub("[^\w]", " ",  bookmark).split()
        assert not 'es' in bookmark_content_words
        assert not 'an' in bookmark_content_words
        assert not 'auch' in bookmark_content_words
        form_data = dict(
            url='http://mir.lu',
            context='es an auch')
        rv = self.api_post('/bookmark_with_context/de/auch/en/also', form_data)
        rv = self.api_get('/get_not_looked_up_words/de')
        estimated_user_voc_after = json.loads(rv.data)
        assert len(estimated_user_voc_after)==len(estimated_user_voc_before)+2
        assert any (bookmark['word'] == 'es' for bookmark in estimated_user_voc_after)
        assert any (bookmark['word'] == 'an' for bookmark in estimated_user_voc_after)
        assert not any (bookmark['word'] == 'auch' for bookmark in estimated_user_voc_after)


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
        # print rv.data


    def test_create_user(self):
        form_data = dict(
            username= "gigi",
            password= "lala"
        )
        rv = self.api_post('/add_user/i@i.la',form_data)
        # print rv.data
        assert rv.data > 1


    def test_get_language(self):
        rv = self.api_get('/learned_language')
        # print rv.data

    def test_get_bookmarks_by_date(self):
        elements  = self.api_get_json ('/bookmarks_by_day/with_context')
        some_date = elements[0]
        assert some_date ["date"]

        some_bookmark = some_date ["bookmarks"][0]
        for key in ["from", "to", "id", "context", "title", "url"]:
            assert key in some_bookmark

        # if we don't pass the context argument, we don't get
        # the context
        elements = self.api_get_json ('/bookmarks_by_day/no_context')
        some_date = elements[0]
        some_contrib = some_date ["bookmarks"][0]
        assert not "context" in some_contrib


    def test_password_hash(self):
        p1 = "test"
        p2 = "pass"
        user = User.find("i@mir.lu")

        hash1 = util.password_hash(p1,user.password_salt)
        hash2 = util.password_hash(p2, user.password_salt)
        assert hash1 != hash2

        assert user.authorize("i@mir.lu", "pass") != None



    def test_text_difficulty(self):
        data = """
            {
            "texts":
                [
                    {"content": "Der die das warum, wer nicht fragt bleibt bew\u00f6lkt!", "id": 1},
                    {"content": "Dies ist ein Test.", "id": 2}],
            "personalized": "true"
            }
        """

        RankedWord.cache_ranked_words()

        rv = self.api_post('/get_difficulty_for_text/de', data, 'application/json')

        difficulties = json.loads(rv.data)['difficulties']
        for difficulty in difficulties:
            assert 0.0 <= difficulty['score_median'] <= 1.0
            assert 0.0 <= difficulty['score_average'] <= 1.0
            if difficulty['id'] is 1:
                assert difficulty['score_median'] == 1.0
                assert round(difficulty['score_average'], 2) == 0.67
            elif difficulty['id'] is 2:
                assert difficulty['score_median'] == 1.0
                assert difficulty['score_average'] == 0.50075


    def test_text_learnability(self):
        data = """
            {"texts":
                [
                    {"content": "Der die das besteht warum, wer nicht fragt bleibt jeweils sogar dumm!", "id": 3},
                    {"content": "Dies ist ein weiterer Test!", "id": 4}
                ]
            }
        """

        rv = self.api_post('/get_learnability_for_text/de', data, 'application/json')

        learnabilities = json.loads(rv.data)['learnabilities']
        for learnability in learnabilities:
            assert 0.0 <= learnability['score'] <= 1.0
            if learnability['id'] is 3:
                assert learnability['score'] == 0.25
            elif learnability['id'] is 4:
                assert learnability['score'] == 0.0


    def test_get_lower_bound_percentage_of_vocabulary(self):
        rv_basic = self.api_get('/get_lower_bound_percentage_of_basic_vocabulary')
        rv_extended = self.api_get('/get_lower_bound_percentage_of_extended_vocabulary')
        basic_lower_bound = float (rv_basic.data)
        extended_lower_bound = float (rv_extended.data)
        assert basic_lower_bound > extended_lower_bound > 0


    def test_get_upper_bound_percentage_of_vocabulary(self):
        rv_basic = self.api_get('/get_upper_bound_percentage_of_basic_vocabulary')
        rv_extended = self.api_get('/get_upper_bound_percentage_of_extended_vocabulary')
        basic_upper_bound = float (rv_basic.data)
        extended_upper_bound = float (rv_extended.data)
        assert 1 > basic_upper_bound > extended_upper_bound


    def test_get_percentage_of_probably_known_bookmarked_words(self):
        rv = self.api_get('/get_percentage_of_probably_known_bookmarked_words')
        assert 0 <= float(rv.data) < 1


    def test_translate(self):
        form_data = dict(
            url='http://mir.lu',
            context=u'Die kleine Jägermeister',
            word="Die")
        rv = self.api_post('/translate/de/en', form_data)
        # print rv.data



    def test_same_text_does_not_get_created_multiple_Times(self):

        context = u'Die kleine Jägermeister'
        url = Url.find('http://mir.lu/stories/german/jagermeister', "Die Kleine Jagermeister (Mircea's Stories)")
        source_language = Language.find('de')

        form_data = dict(
            url=url.as_string(),
            context=context,
            word="Die")

        self.api_post('/translate_and_bookmark/de/en', form_data)
        text1 = Text.find_or_create(context, source_language, url)
        self.api_post('/translate_and_bookmark/de/en', form_data)
        text2 = Text.find_or_create(context, source_language, url)
        assert (text1 == text2)


    def test_delete_bookmark(self):

        form_data = dict(
            url='http://mir.lu',
            context=u'Die kleine Jägermeister',
            word="Die")
        bookmark1 = self.api_post_json('/translate_and_bookmark/de/en', form_data)
        b1 = Bookmark.find(bookmark1["bookmark_id"])
        # print b1.text
        # print b1.text.id

        form_data = dict(
            url='http://mir.lu',
            context=u'Die kleine Jägermeister',
            word="kleine")
        bookmark2 = self.api_post_json('/translate_and_bookmark/de/en', form_data)
        b2 = Bookmark.find(bookmark2["bookmark_id"])
        # print b2.text
        # print b2.text.id

        assert len (b2.text.all_bookmarks()) == 2
        self.api_post("delete_bookmark/27")
        assert len (b2.text.all_bookmarks()) == 1


    def test_translate_and_bookmark(self):

        form_data = dict(
            url='http://mir.lu',
            context=u'Die kleine Jägermeister',
            word="Die")

        bookmark1 = self.api_post_json('/translate_and_bookmark/de/en', form_data)
        bookmark2 = self.api_post_json('/translate_and_bookmark/de/en', form_data)
        bookmark3  = self.api_post_json('/translate_and_bookmark/de/en', form_data)

        assert (bookmark1["bookmark_id"] == bookmark2["bookmark_id"] == bookmark3["bookmark_id"])


    def test_get_user_details(self):

        details = self.api_get_json('/get_user_details')
        assert details
        assert details["name"]
        assert details["email"]

    # getting content from url
    def test_content_from_url(self):
        # parameters
        manual_check = False

        data = """
            {"urls":
                [
                    {"url": "http://www.derbund.ch/wirtschaft/unternehmen-und-konjunktur/die-bankenriesen-in-den-bergkantonen/story/26984250", "id": 1},

                    {"url": "http://www.computerbase.de/2015-11/bundestag-parlament-beschliesst-das-ende-vom-routerzwang-erneut/", "id": 2}
                ]
            }
        """

        rv = self.api_post('/get_content_from_url', data, 'application/json')

        urls = json.loads(rv.data)['contents']
        for url in urls:
            assert url['content'] is not None
            assert url['image'] is not None
            if manual_check:
                print url['content']
                print url['image']

    # From here on we have several tests for the RSS feed related endpoints
    # .....................................................................

    def test_get_feeds_at_inexistent_source(self):
        url_to_test = ["http://nothinghere.is"]

        form_data = dict(
            url=url_to_test)
        feeds = self.api_post_json('/get_feeds_at_url', form_data)
        assert len(feeds) == 0


    def test_get_feeds_at_url(self):

        resulting_feeds = []

        urls_to_test = ["http://derspiegel.de",
                        "http://tageschau.de",
                        "http://derbund.ch",
                        "http://zeit.de",
                        "http://www.handelsblatt.com"]


        for each_url in urls_to_test:
            form_data = dict(
                url=each_url)
            feeds = self.api_post_json('/get_feeds_at_url', form_data)
            resulting_feeds += feeds

            # following assertion makes sure that we find at least on feed
            # in each o the urls_to_test
            assert (feeds[0]["title"])

        # following assertion assumes that each site has at least one feed
        assert len(resulting_feeds) >= 4
        return resulting_feeds

    def test_start_following_feeds(self):

        feeds = self.test_get_feeds_at_url()
        feed_urls = [feed["url"] for feed in feeds]

        form_data = dict(
            feeds=json.dumps(feed_urls))
        self.api_post('/start_following_feeds', form_data)

        feeds = self.api_get_json("get_feeds_being_followed")
        # Assumes that the derspiegel site will always have two feeds
        assert len(feeds) >= 1
        assert feeds[0]["language"] == "de"

    def test_stop_following_feed(self):

        self.test_start_following_feeds()
        # After this test, we will have a bunch of feeds for the user

        feeds = self.api_get_json("get_feeds_being_followed")
        initial_feed_count = len(feeds)

        # Now delete one
        response = self.api_get("stop_following_feed/1")
        assert response.data == "OK"

        feeds = self.api_get_json("get_feeds_being_followed")
        assert len(feeds) == initial_feed_count - 1

        # Now delete the second
        self.api_get("stop_following_feed/2")
        assert response.data == "OK"

        feeds = self.api_get_json("get_feeds_being_followed")
        assert len(feeds) == initial_feed_count - 2

    def test_multiple_stop_following_same_feed(self):

        self.test_stop_following_feed()
        # After this test, we will have removed both the feeds 1 and 2

        # Now try to delete the first one more time
        response = self.api_get("stop_following_feed/1")
        assert response.data == "OOPS. FEED AIN'T BEING THERE"

    def test_get_feed_items(self):

        self.test_start_following_feeds()
        # After this test, we will have two feeds for the user

        feed_items = self.api_get_json("get_feed_items/1")
        assert len(feed_items) > 0
        assert feed_items[0]["title"]
        assert feed_items[0]["summary"]



if __name__ == '__main__':
    unittest.main()
