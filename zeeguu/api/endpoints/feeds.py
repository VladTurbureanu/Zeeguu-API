import json

import feedparser
import sqlalchemy.exc
import flask
from flask import request

import zeeguu
from zeeguu.api import api
from zeeguu.api.feedparser_extensions import list_of_feeds_at_url, two_letter_language_code
from zeeguu.api.route_wrappers import cross_domain, with_session
from zeeguu.api.json_result import json_result
from zeeguu.model.feeds import RSSFeedRegistration, RSSFeed
from zeeguu.model.language import Language
from zeeguu.model.url import Url


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

        feed_object = RSSFeed.find_by_url(url)
        if not feed_object:
            feed_image_url = Url.find(feed_image_url_string)
            title = url
            if "title" in feed:
                title = feed.title
            feed_object = RSSFeed.find_or_create(url, title, feed.description, feed_image_url, lan)
            zeeguu.db.session.add_all([feed_image_url, feed_object])
            zeeguu.db.session.commit()

        feed_registration = RSSFeedRegistration.find_or_create(flask.g.user, feed_object)

        zeeguu.db.session.add(feed_registration)
        zeeguu.db.session.commit()

    return "OK"


@api.route("/start_following_feed", methods=("POST",))
@cross_domain
@with_session
def start_following_feed():
    """
    Start following a feed for which the client provides all the
    metadata. This is useful for the cases where badly formed
    feeds can't be parsed by feedparser.

    :return:
    """

    feed_info = json.loads(request.form.get('feed_info', ''), "utf-8")

    image_url = feed_info["image"]
    language = Language.find(feed_info["language"])
    url_string = feed_info["url"]
    title = feed_info["title"]
    description = feed_info["description"]

    url = Url.find(url_string)
    zeeguu.db.session.add(url)
    # Important to commit this url first; otherwise we end up creating
    # two domains with the same name for both the urls...
    zeeguu.db.session.commit()

    feed_image_url = Url.find(image_url)

    feed_object = RSSFeed.find_or_create(url, title, description, feed_image_url, language)
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


