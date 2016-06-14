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
import traceback

import datetime
import feedparser
import flask
import sqlalchemy.exc
from flask import request

import zeeguu.api.translation_service
import zeeguu
from zeeguu.api.endpoints.sessions import get_session
from zeeguu.api.feedparser_extensions import two_letter_language_code, list_of_feeds_at_url
from zeeguu.api.route_wrappers import cross_domain, with_session
from zeeguu.api.json_result import json_result
from zeeguu.model.session import Session
from zeeguu.language.text_difficulty import text_difficulty
from zeeguu.language.text_learnability import text_learnability
from zeeguu.model.bookmark import Bookmark
from zeeguu.model.exercise import Exercise
from zeeguu.model.exercise_outcome import ExerciseOutcome
from zeeguu.model.exercise_source import ExerciseSource
from zeeguu.model.known_word_probability import KnownWordProbability
from zeeguu.model.language import Language
from zeeguu.model.feeds import RSSFeed, RSSFeedRegistration
from zeeguu.model.text import Text
from zeeguu.model.url import Url
from zeeguu.model.user import User
from zeeguu.model.user_word import UserWord
from zeeguu.the_librarian.page_content_extractor import PageExtractor

from zeeguu.api import api


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


@api.route("/report_exercise_outcome/<exercise_outcome>/<exercise_source>/<exercise_solving_speed>/<bookmark_id>",
           methods=["POST"])
@with_session
def report_exercise_outcome(exercise_outcome,exercise_source,exercise_solving_speed,bookmark_id):
    """
    In the model parlance, an exercise is an entry in a table that
    logs the performance of an exercise. Every such performance, has a source, and an outcome.

    :param exercise_outcome: One of: Correct, Retry, Wrong, Typo, Too easy
    :param exercise_source: has been assigned to your app by zeeguu
    :param exercise_solving_speed: in milliseconds
    :param bookmark_id: the bookmark for which the data is reported
    :return:
    """

    try:
        bookmark = Bookmark.find(bookmark_id)
        new_source = ExerciseSource.find_by_source(exercise_source)
        new_outcome = ExerciseOutcome.find(exercise_outcome)

        if not new_source:
            return "could not find source"

        if not new_outcome:
            return "could not find outcome"

        exercise = Exercise(new_outcome,new_source,exercise_solving_speed,datetime.datetime.now())
        bookmark.add_new_exercise(exercise)
        zeeguu.db.session.add(exercise)
        zeeguu.db.session.commit()

        from zeeguu.language.knowledge_estimator import update_probabilities_for_word
        update_probabilities_for_word(bookmark.origin)
        return "OK"
    except :
        traceback.print_exc()
        return "FAIL"






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


@api.route("/interesting_feeds/<language_id>", methods=("GET",))
@cross_domain
@with_session
def get_interesting_feeds_for_language_id(language_id):
    """
    Get a list of feeds for the given language

    :return:
    """
    feed_data = []
    for feed in RSSFeed.find_for_language_id(language_id):
        feed_data.append(feed.as_dictionary())
    return json_result(feed_data)


@api.route("/get_possible_translations/<from_lang_code>/<to_lang_code>", methods=["POST"])
@cross_domain
@with_session
def get_possible_translations(from_lang_code, to_lang_code):
    """
    Returns a list of possible translations for this
    :param word: word to be translated
    :param from_lang_code:
    :param to_lang_code:
    :return: json array with dictionaries. each of the dictionaries contains at least
        one 'translation' and one 'translation_id' key.

        In the future we envision that the dict will contain
        other types of information, such as relative frequency,
    """

    translations_json = []
    context = request.form.get('context', '')
    url = request.form.get('url', '')
    word = request.form['word']

    main_translation, alternatives = zeeguu.api.translation_service.translate_from_to(word, from_lang_code, to_lang_code)

    lan = Language.find(from_lang_code)
    likelihood = 1.0
    for translation in alternatives:
        wor = UserWord.find(translation, lan)
        zeeguu.db.session.add(wor)
        zeeguu.db.session.commit()
        t_dict = dict(translation_id= wor.id,
                 translation=translation,
                 likelihood=likelihood)
        translations_json.append(t_dict)
        likelihood -= 0.01

    return json_result(dict(translations=translations_json))



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
    main_translation, alternatives = zeeguu.api.translation_service.translate_from_to(word, from_lang_code, to_lang_code)

    return main_translation
