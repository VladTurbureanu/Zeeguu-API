# -*- coding: utf8 -*-

"""
endpoints.py
This file defines all the Zeeguu API endpoints.

For an example of endpoint definition, scroll down
to the definition of the learned_language() function.

"""
import functools

import flask
import urllib2
import sqlalchemy.exc
import urllib
import zeeguu
import json
import goslate
import datetime
import re
from zeeguu import model


api = flask.Blueprint("api", __name__)



def with_session(view):
    """
    Decorator checks that user is in a session.

    Every API endpoint annotated with @with_session
     expects a session object to be passed as a GET parameter

    Example: API_URL/learned_language?session=123141516
    """
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


def cross_domain(view):
    """
    Decorator enables x-origin requests from any domain.

    More about Cross-Origin Resource Sharing: http://www.w3.org/TR/cors/
    """
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        response = flask.make_response(view(*args, **kwargs))
        response.headers['Access-Control-Allow-Origin'] = "*"
        return response

    return wrapped_view



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

    js = json.dumps(res)
    resp = flask.Response(js, status=200, mimetype='application/json')
    return resp





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
@with_session
def available_languages():
    """
    :return: jason with language codes for the
    supported languages.
    e.g. ["en", "fr", "de", "it", "no", "ro"]
    """
    available_language_codes = map((lambda x: x.id), (model.Language.available_languages()))
    return json.dumps(available_language_codes)


# TO DO: This function looks quite ugly here.
# Need a better place to put it.
def decode_word(word):
    return word.replace("+", " ")


@api.route("/adduser/<email>", methods=["POST"])
@cross_domain
def add_user(email):
    """
    Creates user, then redirects to the get_session
    endpoint. Returns a session
    """
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
    user = model.User.authorize(email, password)
    if user is None:
        flask.abort(401)
    session = model.Session.for_user(user)
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
    js = json.dumps(flask.g.user.user_words())
    resp = flask.Response(js, status=200, mimetype='application/json')
    return resp



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
            bookmark['to'] = b.get_translation_words_list(b.translations_list)
            bookmark['title'] = b.text.url.title
            bookmark['url'] = b.text.url.url

            if with_context:
                bookmark['context'] = b.text.content
            bookmarks.append(bookmark)
        date_entry = {}
        date_entry['date'] = date.strftime("%A, %d %B")
        date_entry['bookmarks'] = bookmarks
        dates.append(date_entry)

    js = json.dumps(dates)
    resp = flask.Response(js, status=200, mimetype='application/json')
    return resp



# THIS API WILL BE RETIRED
@api.route ("/goslate/<word>/<from_lang_code>", methods=["GET"])
@cross_domain
# @with_user
def translate (word, from_lang_code):
    gs = goslate.Goslate()
    return gs.translate(word, "en", from_lang_code)

@api.route ("/translate_from_to/<word>/<from_lang_code>/<to_lang_code>", methods=["GET"])
@cross_domain
# @with_user
def translate_from_to (word, from_lang_code,to_lang_code):
    gs = goslate.Goslate()
    return gs.translate(word, to_lang_code, from_lang_code)


@api.route ("/translate_with_context/<word>/<from_lang_code>/<to_lang_code>", methods=["POST"])
@cross_domain
# @with_user
def translate_from_to_with_context (word, from_lang_code,to_lang_code):
    """
    This assumes that you pass the context and url in the post parameter
    :param word:
    :param from_lang_code:
    :param to_lang_code:
    :return:
    """
    context = flask.request.form['context']
    url = flask.request.form['url']
    gs = goslate.Goslate()
    return gs.translate(word, to_lang_code, from_lang_code)




@api.route("/bookmark_with_context/<from_lang_code>/<term>/<to_lang_code>/<translation>",
           methods=["POST"])
@cross_domain
@with_session
def bookmark_with_context(from_lang_code, term, to_lang_code, translation):
    """
    The preferred way of a user saving a word/translation/context to his
    profile.
    :param from_lang_code:
    :param term:
    :param to_lang_code:
    :param translation:
    :return:
    """

    if 'title' in flask.request.form:
        bookmarked_url_title = flask.request.form['title']
    else:
        bookmarked_url_title = ''

    bookmarked_url = flask.request.form['url']
    context = flask.request.form['context']


    url = model.Url.find(bookmarked_url, bookmarked_url_title)

    from_lang = model.Language.find(from_lang_code)
    to_lang = model.Language.find(to_lang_code)


    word = model.Word.find(decode_word(term), from_lang)
    translation = model.Word.find(decode_word(translation), to_lang)
    search = model.Search.query.filter_by(
        user=flask.g.user, word=word, language=to_lang
    ).order_by(model.Search.id.desc()).first()

    #create the text entity first
    new_text = model.Text(context, from_lang, url)

    if search:
        search.bookmark = model.Bookmark(word, translation, flask.g.user, new_text, datetime.datetime.now())
    else:
        zeeguu.db.session.add(model.Bookmark(word, translation, flask.g.user, new_text, datetime.datetime.now()))

    zeeguu.db.session.commit()

    return "OK"


@api.route("/delete_bookmark/<bookmark_id>",
           methods=["POST"])
@cross_domain
@with_session
def delete_bookmark(bookmark_id):
    bookmark = model.Bookmark.query.filter_by(
        id=bookmark_id
    ).first()
    zeeguu.db.session.delete(bookmark)
    zeeguu.db.session.commit()
    return "OK"

@api.route("/create_new_exercise/<exercise_outcome>/<exercise_source>/<exercise_solving_speed>/<bookmark_id>",
           methods=["POST"])
@cross_domain
@with_session
def create_new_exercise(exercise_outcome,exercise_source,exercise_solving_speed,bookmark_id):
    bookmark = model.Bookmark.query.filter_by(
        id=bookmark_id
    ).first()
    new_source = model.ExerciseSource.query.filter_by(
        source=exercise_source
    ).first()
    new_outcome=model.ExerciseOutcome.query.filter_by(
        outcome=exercise_outcome
    ).first()
    if new_source is None or new_outcome is None :
         return "FAIL"
    exercise = model.Exercise(new_outcome,new_source,exercise_solving_speed,datetime.datetime.now())
    bookmark.add_new_exercise(exercise)
    zeeguu.db.session.add(exercise)
    zeeguu.db.session.commit()
    return "OK"

@api.route("/get_exercise_history_for_bookmark/<bookmark_id>", methods=("GET",))
@cross_domain
@with_session
def get_exercise_history_for_bookmark(bookmark_id):
    bookmark = model.Bookmark.query.filter_by(
        id=bookmark_id
    ).first()
    exercise_dict_list = []
    exercise_list = bookmark.exercise_history
    for exercise in exercise_list:
         exercise_dict = {}
         exercise_dict['id'] = exercise.id
         exercise_dict['outcome'] = exercise.outcome.outcome
         exercise_dict['source'] = exercise.source.source
         exercise_dict['exercise_solving_speed'] = exercise.solving_speed
         exercise_dict['time'] = exercise.time.strftime('%m/%d/%Y')
         exercise_dict_list.append(exercise_dict.copy())
    js = json.dumps(exercise_dict_list)
    resp = flask.Response(js, status=200, mimetype='application/json')
    return resp


@api.route("/add_new_translation_to_bookmark/<word_translation>/<bookmark_id>",
           methods=["POST"])
@cross_domain
@with_session
def add_new_translation_to_bookmark(word_translation, bookmark_id):
    bookmark = model.Bookmark.query.filter_by(
        id=bookmark_id
    ).first()
    translations_of_bookmark = bookmark.translations_list
    for transl in translations_of_bookmark:
        if transl.word ==word_translation:
            return 'FAIL'
    translation = model.Word(word_translation, translations_of_bookmark[0].language)
    bookmark.add_new_translation(translation)
    zeeguu.db.session.add(translation)
    zeeguu.db.session.commit()
    return "OK"

@api.route("/delete_translation_of_bookmark/<bookmark_id>/<translation_word>",
           methods=["POST"])
@cross_domain
@with_session
def delete_translation_of_bookmark(bookmark_id,translation_word):
    bookmark = model.Bookmark.query.filter_by(
        id=bookmark_id
    ).first()
    if len(bookmark.translations_list) == 1:
        return 'FAIL'
    translation_id = -1
    for b in bookmark.translations_list:
        if translation_word==b.word:
            translation_id = b.id
            break
    if translation_id ==-1:
        return 'FAIL'
    translation = model.Word.query.filter_by(
        id = translation_id
    ).first()
    bookmark.remove_translation(translation)
    zeeguu.db.session.delete(translation)
    zeeguu.db.session.commit()
    return "OK"


@api.route("/get_translations_of_bookmark/<bookmark_id>", methods=("GET",))
@cross_domain
@with_session
def get_translations_of_bookmark(bookmark_id):
    bookmark = model.Bookmark.query.filter_by(
        id=bookmark_id
    ).first()
    translation_dict_list = []
    translation_list = bookmark.translations_list
    for translation in translation_list:
         translation_dict = {}
         translation_dict['id'] = translation.id
         translation_dict['word'] = translation.word
         translation_dict['language'] = translation.language.name
         translation_dict['word_rank'] = translation.word_rank
         translation_dict_list.append(translation_dict.copy())
    js = json.dumps(translation_dict_list)
    resp = flask.Response(js, status=200, mimetype='application/json')
    return resp

@api.route("/get_count_asked_outcome/<outcome_exercise>", methods=("GET",))
@cross_domain
@with_session

def get_count_asked_outcome(outcome_exercise):
    bookmarks = model.Bookmark.find_all()
    count_i_know = 0
    marked_words_of_user_in_text = []
    words_of_all_bookmarks_content = []
    for bookmark in bookmarks:
        for exercise in bookmark.exercise_history:
            if exercise.outcome.outcome == 'I know':
                count_i_know = count_i_know + 1
                break
        bookmark_content_words = re.sub("[^\w]", " ",  bookmark.text.content).split()
        words_of_all_bookmarks_content.extend(bookmark_content_words)
        marked_words_of_user_in_text.append(bookmark.origin.word)

    words_of_all_bookmarks_content = list(set(words_of_all_bookmarks_content))
    marked_words_of_user_in_text = list(set(marked_words_of_user_in_text))
    words_known_from_user= [word for word in words_of_all_bookmarks_content if word not in marked_words_of_user_in_text]
    count_total_i_know_words = count_i_know + len(words_known_from_user)


    if outcome_exercise == 'I know':
        return str(count_total_i_know_words)
    elif outcome_exercise == 'Do not know':
        return str(len(bookmarks) - count_i_know)
    else:
        return str(-1)








@api.route("/lookup/<from_lang>/<term>/<to_lang>", methods=("POST",))
@cross_domain
@with_session
def lookup(from_lang, term, to_lang):
    """
    Used to log a given search.
    TODO: See what's the relation between this and goslate,
     that is, /goslate should already log the search...
     also, this requires both from and to_lang, but goslate does not.

    :param from_lang:
    :param term:
    :param to_lang:
    :return:
    """
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
@with_session
def lookup_preferred(from_lang, term):
    return lookup(from_lang, term, flask.g.user.learned_language)


@api.route("/validate")
@cross_domain
@with_session
def validate():
    return "OK"


@api.route("/get_page/<path:url>", methods=["GET"])
@cross_domain
@with_session
def get_page(url):

    # url = flask.request.form['url']
    opener = urllib2.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7')]
    print urllib.unquote(url)
    page = opener.open(urllib.unquote(url))
    content = ""
    for line in page:
        content += line
    return content

