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







