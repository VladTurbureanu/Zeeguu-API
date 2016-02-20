# -*- coding: utf8 -*-
#
# This file defines most the Zeeguu REST API endpoints.
#
# For an example of endpoint definition, scroll down
# to the definition of the learned_language() function.
#
# __author__ = '(mostly)mircea'
# with contributions from Karan S, and Linus S

import Queue
import json
import threading
import time
from urllib import unquote_plus

import datetime
import feedparser
import flask
import sqlalchemy.exc

import zeeguu
import translation_service

from route_wrappers import cross_domain, with_session, json_result
from feedparser_extensions import two_letter_language_code, list_of_feeds_at_url
from zeeguu import util
from zeeguu.api.model_core import RankedWord, Language, Bookmark, UserWord
from zeeguu.api.model_core import Session, User, Url, KnownWordProbability, Text
from zeeguu.api.model_feeds import RSSFeed, RSSFeedRegistration
from zeeguu.language.knowledge_estimator import SethiKnowledgeEstimator
from zeeguu.language.text_difficulty import text_difficulty
from zeeguu.language.text_learnability import text_learnability
from zeeguu.language import knowledge_estimator


from flask import request

from zeeguu.the_librarian.page_content_extractor import PageExtractor

REFERENCE_VOCABULARY_SIZE = 10000.0

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
    u = flask.g.user
    res = dict( native  = u.native_language_id,
                learned = u.learned_language_id)
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
    available_language_codes = map((lambda x: x.id), Language.available_languages())
    return json.dumps(available_language_codes)


@api.route("/available_native_languages", methods=["GET"])
@cross_domain
def available_native_languages():
    """
    :return: jason with language codes for the
    supported native languages. curently only english...
    e.g. ["en", "fr", "de", "it", "no", "ro"]unquote_plus(flask.r
    """
    available_language_codes = map((lambda x: x.id), Language.native_languages())
    return json.dumps(available_language_codes)


@api.route("/add_user/<email>", methods=["POST"])
@cross_domain
def add_user(email):
    """
    Creates user, then redirects to the get_session
    endpoint. Returns a session
    """
    password = request.form.get("password", None)
    username = request.form.get("username", None)
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
    password = request.form.get("password", None)
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
    return json_result(flask.g.user.bookmarks_by_day(with_context))




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

    word_str = unquote_plus(request.form['word'])

    url_str = request.form.get('url', '')
    title_str = request.form.get('title', '')
    context_str = request.form.get('context', '')

    # Call the translate API
    translation_str = translation_service.translate_from_to(word_str, from_lang_code, to_lang_code)
    translation_str = unquote_plus(translation_str)

    id = bookmark_with_context(from_lang_code, to_lang_code, word_str, url_str, title_str, context_str, translation_str)

    return json_result(dict(
                            bookmark_id = id,
                            translation = translation_str))


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

    word_str = unquote_plus(term)
    translation_str = unquote_plus(translation)

    url_str = request.form.get('url', '')
    title_str = request.form.get('title', '')
    context_str = request.form.get('context', '')

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
    bookmark = Bookmark.query.filter_by(id=bookmark_id).first()

    exercise_log_dict = []
    exercise_log = bookmark.exercise_log
    for exercise in exercise_log:
        exercise_log_dict.append(dict(id = exercise.id,
                                      outcome = exercise.outcome.outcome,
                                      source = exercise.source.source,
                                      exercise_log_solving_speed = exercise.solving_speed,
                                      time = exercise.time.strftime('%m/%d/%Y')))

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
    bookmark = Bookmark.query.filter_by(id=bookmark_id).first()

    result = [
        dict(id=translation.id,
                 word=translation.word,
                 language=translation.language.name,
                 ranked_word=translation.rank)
        for translation in bookmark.translations_list]

    return json_result(result)


@api.route("/get_not_encountered_words/<lang_code>", methods=("GET",))
@cross_domain
@with_session
def get_not_encountered_words(lang_code):
    return json_result(flask.g.user.get_not_encountered_words(Language.find(lang_code)))


@api.route("/get_known_bookmarks/<lang_code>", methods=("GET",))
@cross_domain
@with_session
def get_known_bookmarks(lang_code):
    e = SethiKnowledgeEstimator(flask.g.user, lang_code)
    return json_result(e.get_known_bookmarks())


@api.route("/get_known_words/<lang_code>", methods=("GET",))
@cross_domain
@with_session
def get_known_words(lang_code):
    """
    :param lang_code: only show the words for a given language (e.g. 'de')
    :return: Returns all the bookmarks of a given user in the given lang
    """
    e = SethiKnowledgeEstimator(flask.g.user, lang_code)
    return json_result(e.known_words_list())


@api.route("/get_probably_known_words/<lang_code>", methods=("GET",))
@cross_domain
@with_session
def get_probably_known_words(lang_code):
    e = SethiKnowledgeEstimator(flask.g.user, lang_code)
    return json_result(e.get_probably_known_words())


@api.route("/get_lower_bound_percentage_of_basic_vocabulary", methods=["GET"])
@cross_domain
@with_session
def get_lower_bound_percentage_of_basic_vocabulary():
    """
    :return: string representation of positive sub-unitary float
    """
    e = SethiKnowledgeEstimator(flask.g.user)
    return str(e.get_lower_bound_percentage_of_basic_vocabulary())


@api.route("/get_upper_bound_percentage_of_basic_vocabulary", methods=("GET",))
@cross_domain
@with_session
def get_upper_bound_percentage_of_basic_vocabulary():
    """

    :return: string representation of positive, sub-unitary float
    """
    e = SethiKnowledgeEstimator(flask.g.user)
    return str(e.get_upper_bound_percentage_of_basic_vocabulary())


@api.route("/get_lower_bound_percentage_of_extended_vocabulary", methods=("GET",))
@cross_domain
@with_session
def get_lower_bound_percentage_of_extended_vocabulary():
    """

    :return: string representation of positive sub-unitary float
    """
    e = SethiKnowledgeEstimator(flask.g.user)
    return str(e.get_lower_bound_percentage_of_extended_vocabulary())


@api.route("/get_upper_bound_percentage_of_extended_vocabulary", methods=("GET",))
@cross_domain
@with_session
def get_upper_bound_percentage_of_extended_vocabulary():
    """

    :return: string representation of positive sub-unitary float
    """
    e = SethiKnowledgeEstimator(flask.g.user)
    return str(e.get_upper_bound_percentage_of_extended_vocabulary())


# returns the percentage of how many bookmarks are known to the user out of all the bookmarks
@api.route("/get_percentage_of_probably_known_bookmarked_words", methods=("GET",))
@cross_domain
@with_session
def get_percentage_of_probably_known_bookmarked_words():
    """

    :return: string representation of positive sub-unitary float
    """
    e = SethiKnowledgeEstimator(flask.g.user)
    return str(e.get_percentage_of_probably_known_bookmarked_words())


@api.route("/get_learned_bookmarks/<lang>", methods=("GET",))
@cross_domain
@with_session
def get_learned_bookmarks(lang):
    lang = Language.find(lang)

    estimator = SethiKnowledgeEstimator(flask.g.user, lang.id)
    bk_list = [dict (id = bookmark.id,
                     origin = bookmark.origin.word,
                     text = bookmark.text.content
                     ) for bookmark in estimator.learned_bookmarks()]

    return json_result(bk_list )


@api.route("/get_not_looked_up_words/<lang_code>", methods=("GET",))
@cross_domain
@with_session
def get_not_looked_up_words(lang_code):
    e = SethiKnowledgeEstimator(flask.g.user)
    return json_result(e.get_not_looked_up_words())


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
    if not language:
        return 'FAIL'

    data = request.get_json()

    if not 'texts' in data:
        return 'FAIL'

    texts = []
    for text in data['texts']:
        texts.append(text)

    personalized = True
    if 'personalized' in data:
        personalized = data['personalized'].lower()
        if personalized == 'false' or personalized == '0':
            personalized = False

    rank_boundary = REFERENCE_VOCABULARY_SIZE
    if 'rank_boundary' in data:
        rank_boundary = float(data['rank_boundary'])
        if rank_boundary > REFERENCE_VOCABULARY_SIZE:
            rank_boundary = REFERENCE_VOCABULARY_SIZE

    user = flask.g.user
    known_probabilities = KnownWordProbability.find_all_by_user_cached(user)

    difficulties = [
        text_difficulty(
            known_probabilities,
            language,
            personalized,
            rank_boundary,
            text)
        for text in texts]

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
    user = flask.g.user

    language = Language.find(lang_code)
    if language is None:
        return 'FAIL'

    data = request.get_json()

    texts = []
    if 'texts' in data:
        for text in data['texts']:
            texts.append(text)
    else:
        return 'FAIL'

    learnabilities = []
    for text in texts:
        e = SethiKnowledgeEstimator(user)
        count, learnability = text_learnability(text, e.words_being_learned(language))
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
    data = request.get_json()
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
        thread = threading.Thread(target=PageExtractor.worker, args=(url['url'], url['id'], queue))
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
        session_id = int(request.args['session'])
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
    domain = request.form.get('url', '')
    return json_result(list_of_feeds_at_url(domain))



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

    json_array_with_feeds = json.loads(request.form.get('feeds', ''))

    for urlString in json_array_with_feeds:
        feed = feedparser.parse(urlString).feed

        feed_image_url_string = ""
        if "image" in feed:
            feed_image_url_string = feed.image["href"]

        lan = None
        if "language" in feed:
            lan = Language.find(two_letter_language_code(feed))

        url = Url.find(urlString)
        zeeguu.db.session.add(url)
        # Important to commit this url first; otherwise we end up creating
        # two domains with the same name for both the urls...
        zeeguu.db.session.commit()

        feed_image_url = Url.find(feed_image_url_string)
        feed_object = RSSFeed.find_or_create(url, feed.title, feed.description, feed_image_url, lan)
        feed_registration = RSSFeedRegistration.find_or_create(flask.g.user, feed_object)

        zeeguu.db.session.add_all([feed_image_url, feed_object, feed_registration])
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
        to_delete = RSSFeedRegistration.with_feed_id(feed_id, flask.g.user)
        zeeguu.db.session.delete(to_delete)
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

    # print str(request.get_data())
    context = request.form.get('context', '')
    url = request.form.get('url', '')
    word = request.form['word']
    translation = translation_service.translate_from_to(word, from_lang_code, to_lang_code)

    return translation
