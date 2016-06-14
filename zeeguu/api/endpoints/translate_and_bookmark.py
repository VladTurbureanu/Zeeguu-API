from datetime import datetime
from urllib import unquote_plus

import flask
from flask import request

import zeeguu
from zeeguu.api import api
from zeeguu.api.route_wrappers import cross_domain, with_session
from zeeguu.api.json_result import json_result
from zeeguu.model.bookmark import Bookmark
from zeeguu.model.language import Language
from zeeguu.model.text import Text
from zeeguu.model.url import Url
from zeeguu.model.user_word import UserWord


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
    translation_str, alternative_translations = zeeguu.api.translation_service.translate_from_to(word_str, from_lang_code, to_lang_code)
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
    #     TODO: Think about updating the date of this bookmark, or maybe creating a duplicate
    #       otherwise, in the history this translation will not be visible!

    except Exception:
        bookmark = Bookmark(user_word, translation, flask.g.user, context, datetime.now())
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
