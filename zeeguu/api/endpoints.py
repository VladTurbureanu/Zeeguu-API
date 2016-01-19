# -*- coding: utf8 -*-
#
# This file defines most the Zeeguu REST API endpoints.
#
# For an example of endpoint definition, scroll down
# to the definition of the learned_language() function.
#
# __author__ = 'mir.lu'

import json
import datetime
import time
import threading
import Queue

from urllib import quote_plus, unquote_plus
import urllib2

import flask
import sqlalchemy.exc
import feedparser
from BeautifulSoup import BeautifulSoup

import zeeguu
from zeeguu import util
from zeeguu.api.model_core import RankedWord, Language, Bookmark, UserWord
from zeeguu.api.model_core import Session, User, Url, KnownWordProbability, Text
from zeeguu.api.model_feeds import RSSFeed, RSSFeedRegistration

from endpoint_utils import cross_domain, with_session, json_result

api = flask.Blueprint("api", __name__)

@api.route("/learned_language", methods=["GET"])
@cross_domain
@with_session
def learned_language():
    """
    Each endpoint is defined by a function definition
    of the same form as this one.

    The important information for understanding the
    endpoint is in the annotations before the function
    and in the comment immediately after the function
    name.

    Two types of annotations are important:

     @api.route gives you the endpoint name together
        with the expectd HTTP method
        it is normally appended to the API_URL (https://www.zeeguu.unibe.ch/)

     @with_session means that you must submit a session
        argument together wit your API request
        e.g. API_URL/learned_language?session=123141516
    """

    return flask.g.user.learned_language_id


@api.route("/learned_language/<language_code>", methods=["POST"])
@cross_domain
@with_session
def learned_language_set(language_code):
    """
    Set the learned language
    :param language_code: one of the ISO language codes
    :return: "OK" for success
    """
    flask.g.user.set_learned_language(language_code)
    zeeguu.db.session.commit()
    return "OK"


@api.route("/native_language", methods=["GET"])
@cross_domain
@with_session
def native_language():
    """
    Get the native language of the user in session
    :return:
    """
    return flask.g.user.native_language_id


@api.route("/learned_and_native_language", methods=["GET"])
@cross_domain
@with_session
def learned_and_native_language():
    """
    Get the native language of the user in session
    :return:
    """
    res = {"native": flask.g.user.native_language_id,
           "learned": flask.g.user.learned_language_id}

    return json_result(res)


@api.route("/native_language/<language_code>", methods=["POST"])
@cross_domain
@with_session
def native_language_set(language_code):
    """
    set the native language of the user in session
    :param language_code:
    :return: OK for success
    """
    flask.g.user.set_native_language(language_code)
    zeeguu.db.session.commit()
    return "OK"


@api.route("/available_languages", methods=["GET"])
@cross_domain
def available_languages():
    """
    :return: jason with language codes for the
    supported languages.
    e.g. ["en", "fr", "de", "it", "no", "ro"]
    """
    available_language_codes = map((lambda x: x.id), (Language.available_languages()))
    return json.dumps(available_language_codes)


@api.route("/available_native_languages", methods=["GET"])
@cross_domain
def available_native_languages():
    """
    :return: jason with language codes for the
    supported native languages. curently only english...
    e.g. ["en", "fr", "de", "it", "no", "ro"]
    """
    available_language_codes = map((lambda x: x.id), (Language.native_languages()))
    return json.dumps(available_language_codes)


@api.route("/add_user/<email>", methods=["POST"])
@cross_domain
def add_user(email):
    """
    Creates user, then redirects to the get_session
    endpoint. Returns a session
    """
    password = flask.request.form.get("password", None)
    username = flask.request.form.get("username", None)
    if password is None:
        flask.abort(400)
    try:
        zeeguu.db.session.add(User(email, username, password))
        zeeguu.db.session.commit()
    except ValueError:
        flask.abort(400)
    except sqlalchemy.exc.IntegrityError:
        flask.abort(400)
    return get_session(email)


@api.route("/session/<email>", methods=["POST"])
@cross_domain
def get_session(email):
    """
    If the email and password match,
    a new sessionId is created, and returned
    as a string. This sessionId has to be passed
    along all the other requests that are annotated
    with @with_user in this file
    """
    password = flask.request.form.get("password", None)
    if password is None:
        flask.abort(400)
    user = User.authorize(email, password)
    if user is None:
        flask.abort(401)
    session = Session.for_user(user)
    zeeguu.db.session.add(session)
    zeeguu.db.session.commit()
    return str(session.id)


@api.route("/user_words", methods=["GET"])
@cross_domain
@with_session
def studied_words():
    """
    Returns a list of the words that the user is currently studying.
    """
    return json_result(flask.g.user.user_words())


@api.route("/bookmarks_by_day/<return_context>", methods=["GET"])
@cross_domain
@with_session
def bookmarks_by_day(return_context):
    """
    Returns the bookmarks of this user organized by date
    If <return_context> is "with_context" it also returns the
    text where the bookmark was found. If <return_context>
    is anything else, the context is not returned.

    """
    with_context = return_context == "with_context"

    bookmarks_by_date, sorted_dates = flask.g.user.bookmarks_by_date()

    dates = []
    for date in sorted_dates:
        bookmarks = []
        for b in bookmarks_by_date[date]:
            bookmark = {}
            bookmark['id'] = b.id
            bookmark['from'] = b.origin.word
            bookmark['to'] = b.translation_words_list()
            bookmark['from_lang'] = b.origin.language_id
            bookmark['to_lang'] = b.translation().language.id
            bookmark['title'] = b.text.url.title
            bookmark['url'] = b.text.url.as_string()

            if with_context:
                bookmark['context'] = b.text.content
            bookmarks.append(bookmark)
        date_entry = {}
        date_entry['date'] = date.strftime("%A, %d %B %Y")
        date_entry['bookmarks'] = bookmarks
        dates.append(date_entry)

    return json_result(dates)


def translate_from_to(word, from_lang_code, to_lang_code):
    translate_url = "https://www.googleapis.com/language/translate/v2"
    api_key = zeeguu.app.config.get("TRANSLATE_API_KEY")

    # Note, that there is quote and quote_plus. The Google API prefers quote_plus,
    # This seems to be the convention for info submitted from forms via GET.
    url = translate_url + \
          "?q=" + quote_plus(word.encode('utf8')) + \
          "&target=" + to_lang_code.encode('utf8') + \
          "&format=text".encode('utf8') + \
          "&source=" + from_lang_code.encode('utf8') + \
          "&key=" + api_key
    # print url
    result = json.loads(urllib2.urlopen(url).read())
    translation = result['data']['translations'][0]['translatedText']
    return translation


@api.route("/translate_and_bookmark/<from_lang_code>/<to_lang_code>", methods=["POST"])
@cross_domain
@with_session
def translate_and_bookmark(from_lang_code, to_lang_code):
    """
    This expects in the post parameter the following:
        - word (to translate)
        - context (surrounding paragraph of the original word )
        - url (of the origin)
        - title (of the origin page)
    :param from_lang_code:
    :param to_lang_code:
    :return:
    """

    word_str = (unquote_plus(flask.request.form['word']))

    url_str = flask.request.form.get('url', '')
    title_str = flask.request.form.get('title', '')
    context_str = flask.request.form.get('context', '')

    # Call the translate API
    translation_str = translate_from_to(word_str, from_lang_code, to_lang_code)
    translation_str = unquote_plus(translation_str)

    id = bookmark_with_context(from_lang_code, to_lang_code, word_str, url_str, title_str, context_str, translation_str)

    return json_result(
            {"bookmark_id": id,
             "translation": translation_str
             })


def bookmark_with_context(from_lang_code, to_lang_code, word_str, url_str, title_str, context_str, translation_str):
    """
        This function will lookup a given word-text pair, and if found, it will return
     that bookmark rather than a new one

    :param from_lang_code:
    :param to_lang_code:
    :param word_str:
    :param url_str:
    :param title_str:
    :param context_str:
    :param translation_str:
    :return:
    """
    from_lang = Language.find(from_lang_code)
    to_lang = Language.find(to_lang_code)

    user_word = UserWord.find(word_str, from_lang)

    url = Url.find(url_str, title_str)
    zeeguu.db.session.add(url)
    zeeguu.db.session.commit()

    context = Text.find_or_create(context_str, from_lang, url)
    zeeguu.db.session.add(context)
    zeeguu.db.session.commit()

    translation = UserWord.find(translation_str, to_lang)

    try:
        bookmark = Bookmark.find_all_by_user_word_and_text(flask.g.user, user_word, context)[0]
    except Exception:
        bookmark = Bookmark(user_word, translation, flask.g.user, context, datetime.datetime.now())
        zeeguu.db.session.add(bookmark)
        bookmark.calculate_probabilities_after_adding_a_bookmark(flask.g.user, bookmark.origin.language)
        zeeguu.db.session.commit()

    return str(bookmark.id)


@api.route("/bookmark_with_context/<from_lang_code>/<term>/<to_lang_code>/<translation>",
           methods=["POST"])
@cross_domain
@with_session
def bookmark_with_context_api(from_lang_code, term, to_lang_code, translation):
    """
    The preferred way of a user saving a word/translation/context to his  profile.
    :param from_lang_code:
    :param term:
    :param to_lang_code:
    :param translation:
    :return: Response containing the bookmark id
    """

    word_str = (unquote_plus(term))
    translation_str = unquote_plus(translation)

    url_str = flask.request.form.get('url', '')
    title_str = flask.request.form.get('title', '')
    context_str = flask.request.form.get('context', '')

    id = bookmark_with_context(from_lang_code, to_lang_code, word_str, url_str, title_str, context_str, translation_str)

    return id


@api.route("/delete_bookmark/<bookmark_id>",
           methods=["POST"])
@cross_domain
@with_session
def delete_bookmark(bookmark_id):
    # Beware, the web app uses the /delete_bookmark endpoint from the gym API
    bookmark = Bookmark.query.filter_by(
            id=bookmark_id
    ).first()

    try:
        zeeguu.db.session.delete(bookmark)
        zeeguu.db.session.commit()
        return "OK"
    except Exception:
        return "FAIL"


@api.route("/get_exercise_log_for_bookmark/<bookmark_id>", methods=("GET",))
@cross_domain
@with_session
def get_exercise_log_for_bookmark(bookmark_id):
    bookmark = Bookmark.query.filter_by(
            id=bookmark_id
    ).first()
    exercise_log_dict = []
    exercise_log = bookmark.exercise_log
    for exercise in exercise_log:
        exercise_dict = {}
        exercise_dict['id'] = exercise.id
        exercise_dict['outcome'] = exercise.outcome.outcome
        exercise_dict['source'] = exercise.source.source
        exercise_dict['exercise_log_solving_speed'] = exercise.solving_speed
        exercise_dict['time'] = exercise.time.strftime('%m/%d/%Y')
        exercise_log_dict.append(exercise_dict)

    return json_result(exercise_log_dict)


@api.route("/add_new_translation_to_bookmark/<word_translation>/<bookmark_id>",
           methods=["POST"])
@cross_domain
@with_session
def add_new_translation_to_bookmark(word_translation, bookmark_id):
    bookmark = Bookmark.query.filter_by(
            id=bookmark_id
    ).first()
    translations_of_bookmark = bookmark.translations_list
    for transl in translations_of_bookmark:
        if transl.word == word_translation:
            return 'FAIL'

    translation_user_word = UserWord.find(word_translation, translations_of_bookmark[0].language)
    bookmark.add_new_translation(translation_user_word)
    zeeguu.db.session.add(translation_user_word)
    zeeguu.db.session.commit()
    return "OK"


@api.route("/delete_translation_from_bookmark/<bookmark_id>/<translation_word>",
           methods=["POST"])
@cross_domain
@with_session
def delete_translation_from_bookmark(bookmark_id, translation_word):
    bookmark = Bookmark.query.filter_by(
            id=bookmark_id
    ).first()
    if len(bookmark.translations_list) == 1:
        return 'FAIL'
    translation_id = -1
    for b in bookmark.translations_list:
        if translation_word == b.word:
            translation_id = b.id
            break
    if translation_id == -1:
        return 'FAIL'
    translation = UserWord.query.filter_by(
            id=translation_id
    ).first()
    bookmark.remove_translation(translation)
    zeeguu.db.session.commit()
    return "OK"


@api.route("/get_translations_for_bookmark/<bookmark_id>", methods=("GET",))
@cross_domain
@with_session
def get_translations_for_bookmark(bookmark_id):
    bookmark = Bookmark.query.filter_by(
            id=bookmark_id
    ).first()
    translation_dict_list = []
    translation_list = bookmark.translations_list
    for translation in translation_list:
        translation_dict = {}
        translation_dict['id'] = translation.id
        translation_dict['word'] = translation.word
        translation_dict['language'] = translation.language.name
        translation_dict['ranked_word'] = translation.rank
        translation_dict_list.append(translation_dict)

    return json_result(translation_dict_list)


@api.route("/get_not_encountered_words/<lang_code>", methods=("GET",))
@cross_domain
@with_session
def get_not_encountered_words(lang_code):
    return json_result(flask.g.user.get_not_encountered_words(Language.find(lang_code)))


@api.route("/get_known_bookmarks/<lang_code>", methods=("GET",))
@cross_domain
@with_session
def get_known_bookmarks(lang_code):
    return json_result(flask.g.user.get_known_bookmarks(Language.find(lang_code)))


@api.route("/get_known_words/<lang_code>", methods=("GET",))
@cross_domain
@with_session
def get_known_words(lang_code):
    lang_id = Language.find(lang_code)
    bookmarks = flask.g.user.all_bookmarks()
    known_words = []
    filtered_known_words_from_user = []
    filtered_known_words_dict_list = []
    for bookmark in bookmarks:
        if bookmark.check_is_latest_outcome_too_easy():
            known_words.append(bookmark.origin.word)
    for word_known in known_words:
        if RankedWord.exists(word_known, lang_id):
            filtered_known_words_from_user.append(word_known)
            zeeguu.db.session.commit()
    filtered_known_words_from_user = list(set(filtered_known_words_from_user))
    for word in filtered_known_words_from_user:
        filtered_known_words_dict_list.append({'word': word})
    return json_result(filtered_known_words_dict_list)


@api.route("/get_probably_known_words/<lang_code>", methods=("GET",))
@cross_domain
@with_session
def get_probably_known_words(lang_code):
    return json_result(flask.g.user.get_probably_known_words(Language.find(lang_code)))


@api.route("/get_lower_bound_percentage_of_basic_vocabulary", methods=["GET"])
@cross_domain
@with_session
def get_lower_bound_percentage_of_basic_vocabulary():
    """
    :return: string representation of positive sub-unitary float
    """
    return str(flask.g.user.get_lower_bound_percentage_of_basic_vocabulary())


@api.route("/get_upper_bound_percentage_of_basic_vocabulary", methods=("GET",))
@cross_domain
@with_session
def get_upper_bound_percentage_of_basic_vocabulary():
    """

    :return: string representation of positive, sub-unitary float
    """
    return str(flask.g.user.get_upper_bound_percentage_of_basic_vocabulary())


@api.route("/get_lower_bound_percentage_of_extended_vocabulary", methods=("GET",))
@cross_domain
@with_session
def get_lower_bound_percentage_of_extended_vocabulary():
    """

    :return: string representation of positive sub-unitary float
    """
    return str(flask.g.user.get_lower_bound_percentage_of_extended_vocabulary())


@api.route("/get_upper_bound_percentage_of_extended_vocabulary", methods=("GET",))
@cross_domain
@with_session
def get_upper_bound_percentage_of_extended_vocabulary():
    """

    :return: string representation of positive sub-unitary float
    """
    return str(flask.g.user.get_upper_bound_percentage_of_extended_vocabulary())


# returns the percentage of how many bookmarks are known to the user out of all the bookmarks
@api.route("/get_percentage_of_probably_known_bookmarked_words", methods=("GET",))
@cross_domain
@with_session
def get_percentage_of_probably_known_bookmarked_words():
    """

    :return: string representation of positive sub-unitary float
    """
    return str(flask.g.user.get_percentage_of_probably_known_bookmarked_words())


@api.route("/get_learned_bookmarks/<lang>", methods=("GET",))
@cross_domain
@with_session
def get_learned_bookmarks(lang):
    lang = Language.find(lang)
    bookmarks = flask.g.user.all_bookmarks()
    too_easy_bookmarks = []
    learned_bookmarks_dict_list = []
    for bookmark in bookmarks:
        if bookmark.check_is_latest_outcome_too_easy() and bookmark.origin.language == lang:
            too_easy_bookmarks.append(bookmark)
    learned_bookmarks = [bookmark for bookmark in bookmarks if bookmark not in too_easy_bookmarks]
    for bookmark in learned_bookmarks:
        learned_bookmarks_dict = {}
        learned_bookmarks_dict['id'] = bookmark.id
        learned_bookmarks_dict['origin'] = bookmark.origin.word
        learned_bookmarks_dict['text'] = bookmark.text.content
        learned_bookmarks_dict_list.append(learned_bookmarks_dict)

    return json_result(learned_bookmarks_dict_list)


@api.route("/get_not_looked_up_words/<lang_code>", methods=("GET",))
@cross_domain
@with_session
def get_not_looked_up_words(lang_code):
    return json_result(flask.g.user.get_not_looked_up_words(Language.find(lang_code)))


@api.route("/get_difficulty_for_text/<lang_code>", methods=("POST",))
@cross_domain
@with_session
def get_difficulty_for_text(lang_code):
    """
    URL parameters:
    :param lang_code: the language of the text

    Json data:
    :param texts: json array that contains the texts to calculate the difficulty for. Each text consists of an array
        with the text itself as 'content' and an additional 'id' which gets roundtripped unchanged
    :param personalized (optional): calculate difficulty score for a specific user? (Enabled by default)
    :param rank_boundary (optional): upper boundary for word frequency rank (between 1 and 10'000)

    For an example of how the Json data looks like, see
        ../tests/api_tests.py#test_txt_difficulty(self):

    :return difficulties: json array, contains the difficulties as arrays with the key 'score_median' for the median
        and 'score_average' for the average difficulty the value (between 0 (easy) and 1 (hard)) and the 'id' parameter
        to identify the corresponding text
    """
    language = Language.find(lang_code)
    if language is None:
        return 'FAIL'

    data = flask.request.get_json()

    texts = []
    if 'texts' in data:
        for text in data['texts']:
            texts.append(text)
    else:
        return 'FAIL'

    personalized = True
    if 'personalized' in data:
        personalized = data['personalized'].lower()
        if personalized == 'false' or personalized == '0':
            personalized = False

    rank_boundary = 10000.0
    if 'rank_boundary' in data:
        rank_boundary = float(data['rank_boundary'])
        if rank_boundary > 10000.0:
            rank_boundary = 10000.0

    user = flask.g.user
    known_probabilities = KnownWordProbability.find_all_by_user_cached(user)

    difficulties = []
    for text in texts:
        # Calculate difficulty for each word
        words = util.split_words_from_text(text['content'])
        words_difficulty = []
        for word in words:
            ranked_word = RankedWord.find_cache(word, language)

            word_difficulty = 1.0  # Value between 0 (easy) and 1 (hard)
            if ranked_word is not None:
                # Check if the user knows the word
                try:
                    known_propability = known_probabilities[word]  # Value between 0 (unknown) and 1 (known)
                except KeyError:
                    known_propability = None

                if personalized and known_propability is not None:
                    word_difficulty -= float(known_propability)
                elif ranked_word.rank <= rank_boundary:
                    word_frequency = (rank_boundary - (
                    ranked_word.rank - 1)) / rank_boundary  # Value between 0 (rare) and 1 (frequent)
                    word_difficulty -= word_frequency

            words_difficulty.append(word_difficulty)

        # Uncomment to print data for histogram generation
        # text.generate_histogram(words_difficulty)

        # Median difficulty for text
        words_difficulty.sort()
        center = int(round(len(words_difficulty) / 2, 0))
        difficulty_median = words_difficulty[center]

        # Average difficulty for text
        difficulty_average = sum(words_difficulty) / float(len(words_difficulty))

        difficulties.append(dict(score_median=difficulty_median, score_average=difficulty_average, id=text['id']))

    return json_result(dict(difficulties=difficulties))


@api.route("/get_learnability_for_text/<lang_code>", methods=("POST",))
@cross_domain
@with_session
def get_learnability_for_text(lang_code):
    """
    URL parameters:
    :param lang_code: the language of the text

    Json data:
    :param texts: json array that contains the texts to calculate the learnability for. Each text consists of an array
        with the text itself as 'content' and an additional 'id' which gets roundtripped unchanged
        For an example of how the Json data looks like, see
            ../tests/api_tests.py#test_text_learnability(self):


    :return learnabilities: json array, contains the learnabilities as arrays with the key 'score' for the learnability
        value (percentage of words from the text that the user is currently learning), the 'count' of the learned
        words in the text and the 'id' parameter to identify the corresponding text
    """
    language = Language.find(lang_code)
    if language is None:
        return 'FAIL'

    data = flask.request.get_json()

    texts = []
    if 'texts' in data:
        for text in data['texts']:
            texts.append(text)
    else:
        return 'FAIL'

    user = flask.g.user

    # Get the words the user is currently learning
    words_learning = {}
    bookmarks = Bookmark.find_by_specific_user(user)
    for bookmark in bookmarks:
        learning = not bookmark.check_is_latest_outcome_too_easy()
        user_word = bookmark.origin
        if learning and user_word.language == language:
            words_learning[user_word.word] = user_word.word

    learnabilities = []
    for text in texts:
        # Calculate learnability
        words = util.split_words_from_text(text['content'])
        words_learnability = []
        for word in words:
            if word in words_learning:
                words_learnability.append(word)

        count = len(words_learnability)
        learnability = count / float(len(words))

        learnabilities.append(dict(score=learnability, count=count, id=text['id']))

    return json_result(dict(learnabilities=learnabilities))


@api.route("/get_content_from_url", methods=("POST",))
@cross_domain
def get_content_from_url():
    """
    Json data:
    :param urls: json array that contains the urls to get the article content for. Each url consists of an array
        with the url itself as 'url' and an additional 'id' which gets roundtripped unchanged.
        For an example of how the Json data looks like, see
            ../tests/api_tests.py#test_content_from_url(self):

    :param timeout (optional): maximal time in seconds to wait for the results

    :return contents: json array, contains the contents of the urls that responded within the timeout as arrays
        with the key 'content' for the article content, the url of the main image as 'image' and the 'id' parameter
        to identify the corresponding url

    """
    data = flask.request.get_json()
    queue = Queue.Queue()

    urls = []
    if 'urls' in data:
        for url in data['urls']:
            urls.append(url)
    else:
        return 'FAIL'

    if 'timeout' in data:
        timeout = int(data['timeout'])
    else:
        timeout = 10

    # Start worker threads to get url contents
    threads = []
    for url in urls:
        thread = threading.Thread(target=util.PageExtractor.worker, args=(url['url'], url['id'], queue))
        thread.daemon = True
        threads.append(thread)
        thread.start()

    # Wait for workers to finish until timeout
    stop = time.time() + timeout
    while any(t.isAlive() for t in threads) and time.time() < stop:
        time.sleep(0.1)

    contents = []
    for i in xrange(len(urls)):
        try:
            contents.append(queue.get_nowait())
        except Queue.Empty:
            pass

    return json_result(dict(contents=contents))


@api.route("/validate")
@cross_domain
@with_session
def validate():
    return "OK"


@api.route("/logout_session",
           methods=["GET"])
@cross_domain
@with_session
def logout():
    # Note: the gym uses another logout endpoint.

    try:
        session_id = int(flask.request.args['session'])
    except:
        flask.abort(401)
    session = Session.query.get(session_id)

    # print "about to expire session..." + str(session_id)
    zeeguu.db.session.delete(session)
    zeeguu.db.session.commit()

    return "OK"


@api.route("/get_user_details", methods=("GET",))
@cross_domain
@with_session
def get_user_details():
    """
    after the login, this information might be useful to be displayed
    by an app
    :param lang_code:
    :return:
    """
    return json_result(flask.g.user.details_as_dictionary())


@api.route("/get_feeds_at_url", methods=("POST",))
@cross_domain
@with_session
def get_feeds_at_url():
    """
    :return: a list of feeds that can be found at the given URL
    Empty list if soemething
    """
    domain = flask.request.form.get('url', '')

    try:
        feed_data = []
        page = urllib2.urlopen(domain)
        soup = BeautifulSoup(page)
        feed_urls = soup.findAll("link", type="application/rss+xml")

        for feed_url in feed_urls:
            feed_url = feed_url["href"]
            if feed_url[0] == "/":
                feed_url = domain + feed_url

            feed = feedparser.parse(feed_url).feed
            feed_data.append({
                "url": feed_url,
                "title": feed.title,
                "description": feed.description,
                "image_url": feed.image["href"],
                "language": feed.language
            })

        return json_result(feed_data)

    except Exception as e:
        print e
        return json_result([])


@api.route("/get_feeds_being_followed", methods=("GET",))
@cross_domain
@with_session
def get_feeds_being_followed():
    """
    A user might be following multiple feeds at once.
    This endpoint returns them as a list.

    :return: a json list with feeds for which the user is registered;
     every feed in this list is a dictionary with the following info:
                id = unique id of the feed; uniquely identifies feed in other endpoints
                title = <unicode string>
                url = ...
                language = ...
                image_url = ...
    """
    registrations = RSSFeedRegistration.feeds_for_user(flask.g.user)
    return json_result([reg.rss_feed.as_dictionary() for reg in registrations])


@api.route("/start_following_feeds", methods=("POST",))
@cross_domain
@with_session
def start_following_feeds():
    """
    A user can start following multiple feeds at once.

    The feeds are passed as the post parameter :feeds:
     which contains a json list with URLs for the feeds to be followed.

    :return:
    """

    json_array_with_feeds = json.loads(flask.request.form.get('feeds', ''))

    for urlString in json_array_with_feeds:
        feed = feedparser.parse(urlString).feed
        feed_image_url_string = feed.image["href"]

        # feed.language conforms to
        # http://www.rssboard.org/rss-language-codes
        # sometimes it is of the form de-de, de-au providing a hint of dialect
        # thus, we only pick the first two letters of this code
        lan = Language.find(feed.language[:2])
        url = Url.find(urlString)
        zeeguu.db.session.add(url)
        # Important to commit this url first; otherwise we end up creating
        # two domains with the same name for both the urls...
        zeeguu.db.session.commit()

        feed_image_url = Url.find(feed_image_url_string)
        feedObject = RSSFeed.find_or_create(url, feed.title, feed.description, feed_image_url, lan)
        feedRegistration = RSSFeedRegistration.find_or_create(flask.g.user, feedObject)

        zeeguu.db.session.add_all([feed_image_url, feedObject, feedRegistration])
        zeeguu.db.session.commit()

    return "OK"


@api.route("/stop_following_feed/<feed_id>", methods=("GET",))
@cross_domain
@with_session
def stop_following_feed(feed_id):
    """
    A user can stop following the feed with a given ID
    :return: OK / ERROR
    """

    try:
        registrationToDelete = RSSFeedRegistration.with_feed_id(feed_id, flask.g.user)
        zeeguu.db.session.delete(registrationToDelete)
        zeeguu.db.session.commit()
    except sqlalchemy.orm.exc.NoResultFound as e:
        return "OOPS. FEED AIN'T BEING THERE"

    return "OK"


@api.route("/get_feed_items/<feed_id>", methods=("GET",))
@cross_domain
@with_session
def get_feed_items_for(feed_id):
    """
    Get a list of feed items for a given feed ID

    :return: json list of dicts, with the following info:
                    title   = <unicode string>
                    url     = <unicode string>
                    content = <list> e.g.:
                        [{u'base': u'http://www.spiegel.de/schlagzeilen/index.rss',
                         u'type': u'text/html', u'language': None, u'value': u'\xdcberwachungskameras, die bei Aldi verkauft wurden, haben offenbar ein Sicherheitsproblem: Hat man kein Passwort festgelegt, \xfcbertragen sie ihre Aufnahmen ungesch\xfctzt ins Netz - und verraten au\xdferdem WLAN- und E-Mail-Passw\xf6rter.'}]
                    summary = <unicode string>
                    published= <unicode string> e.g.
                        'Fri, 15 Jan 2016 15:26:51 +0100'
    """
    registration = RSSFeedRegistration.with_feed_id(feed_id, flask.g.user)
    return json_result(registration.rss_feed.feed_items())


# Warning:
# Might be deprecated at some point... or at least, reduced to translating single words...
# It would make more sense to use translate_and_bookmark instead
#
# Sincerely your's,
# Tom Petty and the Zeeguus

@api.route("/translate/<from_lang_code>/<to_lang_code>", methods=["POST"])
@cross_domain
def translate(from_lang_code, to_lang_code):
    """
    This will be deprecated soon...
    # TODO: Zeeguu Translate for Android should stop relying on this
    :param word:
    :param from_lang_code:
    :param to_lang_code:
    :return:
    """

    # print str(flask.request.get_data())
    context = flask.request.form.get('context', '')
    url = flask.request.form.get('url', '')
    word = flask.request.form['word']
    translation = translate_from_to(word, from_lang_code, to_lang_code)

    return translation
