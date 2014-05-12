# -*- coding: utf8 -*-
import functools

import flask
import sqlalchemy.exc

import zeeguu
from zeeguu import model


api = flask.Blueprint("api", __name__)


def with_user(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        try:
            session_id = int(flask.request.args['session'])
        except:
            flask.abort(401)
        session = model.Session.query.get(session_id)
        if session is None:
            flask.abort(401)
        flask.g.user = session.user
        session.update_use_date()
        return view(*args, **kwargs)

    return wrapped_view


def with_user_test(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        flask.g.user = model.User.find("user@localhost.com")
        return view(*args, **kwargs)

    return wrapped_view


def cross_domain(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        response = flask.make_response(view(*args, **kwargs))
        response.headers['Access-Control-Allow-Origin'] = "*"
        return response

    return wrapped_view


def decode_word(word):
    return word.replace("+", " ")


@api.route("/adduser/<email>", methods=["POST"])
def add_user(email):
    password = flask.request.form.get("password", None)
    if password is None:
        flask.abort(400)
    try:
        zeeguu.db.session.add(model.User(email, password))
        zeeguu.db.session.commit()
    except ValueError:
        flask.abort(400)
    except sqlalchemy.exc.IntegrityError:
        flask.abort(400)
    return get_session(email)


@api.route("/session/<email>", methods=["POST"])
@cross_domain
def get_session(email):
    password = flask.request.form.get("password", None)
    if password is None:
        flask.abort(400)
    user = model.User.authorize(email, password)
    if user is None:
        flask.abort(401)
    session = model.Session.for_user(user)
    zeeguu.db.session.add(session)
    zeeguu.db.session.commit()
    return str(session.id)


@api.route("/learned_language", methods=["GET"])
@cross_domain
@with_user
def learned_language():
    print "---->" + flask.g.user.preferred_language_id
    return flask.g.user.preferred_language_id

@api.route("/contribs", methods=["GET"])
@cross_domain
@with_user
def contributions():
    #at this moment it seems nice to exchange data in json format
    contributions = flask.g.user.contribs_chronologically()

    words = []
    for contrib in contributions:
        word = {}
        word['from'] = contrib.origin.word
        word['to'] = contrib.translation.word
        words.append(word)

    import json

    js = json.dumps(words)
    resp = flask.Response(js, status=200, mimetype='application/json')
    return resp


@api.route("/contribs_by_day", methods=["GET"])
@cross_domain
@with_user
def contributions_by_day():
    usr = flask.g.user
    contribs_by_date, sorted_dates = usr.contribs_by_date()

    dates = []
    for date in sorted_dates:
        words = []
        for contrib in contribs_by_date[date]:
            word = {}
            word['from'] = contrib.origin.word
            word['to'] = contrib.translation.word
            words.append(word)
        date_entry = {}
        date_entry['date'] = date.strftime("%A, %d %B")
        date_entry['contribs'] = words
        dates.append(date_entry)

    import json

    js = json.dumps(dates)
    resp = flask.Response(js, status=200, mimetype='application/json')
    return resp


@api.route("/contribute/<from_lang_code>/<term>/<to_lang_code>/<translation>",
           methods=["POST"])
@cross_domain
@with_user
def contribute(from_lang_code, term, to_lang_code, translation):
    from_lang = model.Language.find(from_lang_code)
    to_lang = model.Language.find(to_lang_code)

    word = model.Word.find(decode_word(term), from_lang)
    translation = model.Word.find(decode_word(translation), to_lang)
    search = model.Search.query.filter_by(
        user=flask.g.user, word=word, language=to_lang
    ).order_by(model.Search.id.desc()).first()
    import datetime

    search.contribution = model.Contribution(word, translation, flask.g.user, datetime.datetime.now())

    zeeguu.db.session.commit()

    return "OK"


@api.route("/contribute_with_context/<from_lang_code>/<term>/<to_lang_code>/<translation>",
           methods=["POST"])
@cross_domain
@with_user
def contribute_with_context(from_lang_code, term, to_lang_code, translation):
    url = model.Url.find(str(flask.request.form['url']))
    context = flask.request.form['context']

    from_lang = model.Language.find(from_lang_code)
    to_lang = model.Language.find(to_lang_code)

    word = model.Word.find(decode_word(term), from_lang)
    translation = model.Word.find(decode_word(translation), to_lang)
    search = model.Search.query.filter_by(
        user=flask.g.user, word=word, language=to_lang
    ).order_by(model.Search.id.desc()).first()

    #create the text entity first
    new_text = model.Text(context, from_lang, url)
    import datetime

    search.contribution = model.Contribution(word, translation, flask.g.user, new_text, datetime.datetime.now())

    zeeguu.db.session.commit()

    return "OK"


@api.route("/lookup/<from_lang>/<term>/<to_lang>", methods=("POST",))
@cross_domain
@with_user
def lookup(from_lang, term, to_lang):
    from_lang = model.Language.find(from_lang)
    if not isinstance(to_lang, model.Language):
        to_lang = model.Language.find(to_lang)
    user = flask.g.user
    content = flask.request.form.get("text")
    if content is not None:
        text = model.Text.find(content, from_lang)
        user.read(text)
    else:
        text = None
    user.searches.append(
        model.Search(user, model.Word.find(decode_word(term), from_lang),
                     to_lang, text)
    )
    zeeguu.db.session.commit()
    return "OK"


@api.route("/lookup/<from_lang>/<term>", methods=("POST",))
@cross_domain
@with_user
def lookup_preferred(from_lang, term):
    return lookup(from_lang, term, flask.g.user.preferred_language)


@api.route("/validate")
@cross_domain
@with_user
def validate():
    return "OK"
