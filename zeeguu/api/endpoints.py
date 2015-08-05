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
from zeeguu.model import WordRank, Language,Bookmark, Session, Search, UserWord, User, Url, ExerciseBasedProbability, EncounterBasedProbability,AggregatedProbability, Text, ExerciseOutcome
import re


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
        session = Session.query.get(session_id)
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
    available_language_codes = map((lambda x: x.id), (Language.available_languages()))
    return json.dumps(available_language_codes)


# TO DO: This function looks quite ugly here.
# Need a better place to put it.
def decode_word(word):
    return word.replace("+", " ")


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


@api.route("/user_word", methods=["GET"])
@cross_domain
@with_session
def studied_words():
    """
    Returns a list of the words that the user is currently studying.
    """
    js = json.dumps(flask.g.user.user_word())
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
            bookmark['to'] = b.translation_words_list()
            bookmark['from_lang'] = b.origin.language_id
            bookmark['to_lang'] = b.translation().language.id
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

def translate_from_to (word, from_lang_code,to_lang_code):
	translate_url = "https://www.googleapis.com/language/translate/v2"
	api_key = zeeguu.app.config.get("TRANSLATE_API_KEY")

	# Note, that there is quote and quote_plus. The Google API prefers quote_plus,
	# This seems to be the convention for info submitted from forms via GET.
	url = translate_url + \
		"?q="+ word +\
		"&target="+to_lang_code.encode('utf8')+\
		"&format=text".encode('utf8')+\
		"&source="+from_lang_code.encode('utf8')+\
		"&key="+api_key
	print url
	result=json.loads(urllib2.urlopen(url).read())
	translation = result['data']['translations'][0]['translatedText']
	return translation

@api.route ("/translate/<from_lang_code>/<to_lang_code>", methods=["POST"])
@cross_domain
# @with_user
def translate(from_lang_code,to_lang_code):
    """
    This assumes that you pass the context and url in the post parameter
    :param word:
    :param from_lang_code:
    :param to_lang_code:
    :return:
    """
    context = flask.request.form.get('context', '')
    url = flask.request.form.get('url','')
    word = flask.request.form['word']
    word = re.sub(r'%20', "+", word)
    return translate_from_to(word, from_lang_code, to_lang_code)




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


    url = Url.find(bookmarked_url, bookmarked_url_title)

    from_lang = Language.find(from_lang_code)
    to_lang = Language.find(to_lang_code)

    word = (decode_word(term))
    translation_word = decode_word(translation)
    user_word = UserWord.find(word,from_lang)
    translation = UserWord.find(translation_word,to_lang)

    # search = Search.query.filter_by(
    #     user=flask.g.user, user_word=user_word, language=to_lang
    # ).order_by(Search.id.desc()).first()

    #create the text entity first
    new_text = Text(context, from_lang, url)
    bookmark = Bookmark(user_word, translation, flask.g.user, new_text, datetime.datetime.now())
    zeeguu.db.session.add(bookmark)
    ranked_and_not_looked_up_words = bookmark.not_looked_up_words_with_rank()
    for word in ranked_and_not_looked_up_words:
        enc_prob = EncounterBasedProbability.find_or_create(word,flask.g.user)
        zeeguu.db.session.add(enc_prob)
        user_word = None
        word_rank = enc_prob.word_rank
        if UserWord.exists(word,from_lang):
            user_word = UserWord.find(word,from_lang)
            ex_prob = ExerciseBasedProbability.find(flask.g.user,user_word)
            agg_prob = AggregatedProbability.find(flask.g.user,user_word,word_rank)
            agg_prob.probability = agg_prob.calculateAggregatedProb(ex_prob, enc_prob)
        else:
            if AggregatedProbability.exists(flask.g.user, user_word,word_rank):
                agg_prob = AggregatedProbability.find(flask.g.user,user_word,word_rank)
                agg_prob.probability = enc_prob.probability
            else:
                agg_prob = AggregatedProbability.find(flask.g.user,user_word,word_rank, enc_prob.probability)
                zeeguu.db.session.add(agg_prob)

    word_rank = None
    enc_prob = None
    ex_prob = ExerciseBasedProbability.find(flask.g.user, bookmark.origin)
    if WordRank.exists(bookmark.origin.word, from_lang):
        word_rank = WordRank.find(bookmark.origin.word, from_lang)
        if EncounterBasedProbability.exists(flask.g.user, word_rank):
            enc_prob = EncounterBasedProbability.find(flask.g.user, word_rank)
            enc_prob.reset_prob()
    if ExerciseBasedProbability.exists(flask.g.user, bookmark.origin):
        ex_prob.halfProbability()
    else:
        zeeguu.db.session.add(ex_prob)

    if AggregatedProbability.exists(flask.g.user, bookmark.origin,word_rank) and enc_prob == None:
        agg_prob = AggregatedProbability.find(flask.g.user, bookmark.origin,word_rank)
        agg_prob.probability = ex_prob.probability
    elif enc_prob is not None:
        agg_prob = AggregatedProbability.find(flask.g.user, bookmark.origin,word_rank)
        agg_prob.probability = AggregatedProbability.calculateAggregatedProb(ex_prob,enc_prob)
    else:
        agg_prob = AggregatedProbability.find(flask.g.user, bookmark.origin,word_rank, ex_prob.probability)
        zeeguu.db.session.add(agg_prob)

    zeeguu.db.session.commit()

    return str(bookmark.id)


@api.route("/delete_bookmark/<bookmark_id>",
           methods=["POST"])
@cross_domain
@with_session
def delete_bookmark(bookmark_id):
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
         exercise_log_dict.append(exercise_dict.copy())
    js = json.dumps(exercise_log_dict)
    resp = flask.Response(js, status=200, mimetype='application/json')
    return resp


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
        if transl.word ==word_translation:
            return 'FAIL'


    translation_user_word = UserWord.find(word_translation,translations_of_bookmark[0].language)
    bookmark.add_new_translation(translation_user_word)
    zeeguu.db.session.add(translation_user_word)
    zeeguu.db.session.commit()
    return "OK"

@api.route("/delete_translation_from_bookmark/<bookmark_id>/<translation_word>",
           methods=["POST"])
@cross_domain
@with_session
def delete_translation_from_bookmark(bookmark_id,translation_word):
    bookmark = Bookmark.query.filter_by(
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
    translation = UserWord.query.filter_by(
        id = translation_id
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
         translation_dict['word_rank'] = translation.rank
         translation_dict_list.append(translation_dict.copy())
    js = json.dumps(translation_dict_list)
    resp = flask.Response(js, status=200, mimetype='application/json')
    return resp


@api.route("/get_known_bookmarks/<lang_code>", methods=("GET",))
@cross_domain
@with_session
def get_known_bookmarks(lang_code):
    js = json.dumps(flask.g.user.get_known_bookmarks(Language.find(lang_code)))
    resp = flask.Response(js, status=200, mimetype='application/json')
    return resp


@api.route("/get_known_words/<lang_code>", methods=("GET",))
@cross_domain
@with_session
def get_known_words(lang_code):
    lang_id = Language.find(lang_code)
    bookmarks = Bookmark.find_all_filtered_by_user()
    i_know_words=[]
    filtered_i_know_words_from_user = []
    filtered_i_know_words_dict_list =[]
    for bookmark in bookmarks:
        if Bookmark.is_sorted_exercise_log_after_date_outcome(ExerciseOutcome.IKNOW, bookmark):
                i_know_words.append(bookmark.origin.word)
    for word_known in i_know_words:
        if WordRank.exists(word_known, lang_id):
            filtered_i_know_words_from_user.append(word_known)
            zeeguu.db.session.commit()
    filtered_i_know_words_from_user = list(set(filtered_i_know_words_from_user))
    for word in filtered_i_know_words_from_user:
        filtered_i_know_word_dict = {}
        filtered_i_know_word_dict['word'] = word
        filtered_i_know_words_dict_list.append(filtered_i_know_word_dict.copy())
    js = json.dumps(filtered_i_know_words_dict_list)
    resp = flask.Response(js, status=200, mimetype='application/json')
    return resp

@api.route("/get_probable_known_words/<lang_code>", methods=("GET",))
@cross_domain
@with_session
def get_probable_known_words(lang_code):
    js = json.dumps(flask.g.user.get_probable_known_words(Language.find(lang_code)))
    resp = flask.Response(js, status=200, mimetype='application/json')
    return resp

@api.route("/get_percentage_of_known_words_of_word_rank", methods=("GET",))
@cross_domain
@with_session
def get_percentage_of_known_words_of_word_rank():
    return flask.g.user.get_percentage_of_known_words_of_word_rank()

@api.route("/get_percentage_of_known_bookmarked_words", methods=("GET",))
@cross_domain
@with_session
def get_percentage_of_known_bookmarked_words():
    return flask.g.user.get_percentage_of_known_bookmarked_words()

@api.route("/get_learned_bookmarks/<lang>", methods=("GET",))
@cross_domain
@with_session
def get_learned_bookmarks(lang):
    lang = Language.find(lang)
    bookmarks = Bookmark.find_all_filtered_by_user()
    i_know_bookmarks=[]
    learned_bookmarks_dict_list =[]
    for bookmark in bookmarks:
        if Bookmark.is_sorted_exercise_log_after_date_outcome(ExerciseOutcome.IKNOW, bookmark) and bookmark.origin.language == lang:
                i_know_bookmarks.append(bookmark)
    learned_bookmarks= [bookmark for bookmark in bookmarks if bookmark not in i_know_bookmarks]
    for bookmark in learned_bookmarks:
        learned_bookmarks_dict = {}
        learned_bookmarks_dict ['id'] = bookmark.id
        learned_bookmarks_dict ['origin'] = bookmark.origin.word
        learned_bookmarks_dict['text'] = bookmark.text.content
        learned_bookmarks_dict_list.append(learned_bookmarks_dict.copy())

    js = json.dumps(learned_bookmarks_dict_list)
    resp = flask.Response(js, status=200, mimetype='application/json')
    return resp

@api.route("/get_estimated_user_vocabulary/<lang_code>", methods=("GET",))
@cross_domain
@with_session
def get_estimated_user_vocabulary(lang_code):
    js = json.dumps(flask.g.user.get_estimated_vocabulary(Language.find(lang_code)))
    resp = flask.Response(js, status=200, mimetype='application/json')
    return resp




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
    from_lang = Language.find(from_lang)
    if not isinstance(to_lang, Language):
        to_lang = Language.find(to_lang)
    user = flask.g.user
    content = flask.request.form.get("text")
    if content is not None:
        text = Text.find(content, from_lang)
        user.read(text)
    else:
        text = None
    word = decode_word(term)
    rank = UserWord.find_rank(word, to_lang)
    user.searches.append(
        Search(user, UserWord.find(word, from_lang),
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

