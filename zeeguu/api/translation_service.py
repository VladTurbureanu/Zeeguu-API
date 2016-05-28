# -*- coding: utf8 -*-
#
# Dispatching translation requests to the Google Translate backend
# or loading some of the locally cached translations
#
# __author__ = 'mircea'
#

import json
import zeeguu
from urllib import quote_plus
from urllib2 import urlopen


def get_cached_translation_if_available(word, from_lang_code, to_lang_code):
    """get_cached_translation_if_available('Die', 'de', 'en') -> 'the'

    We want to be able to translate several words that are required in the
    test cases even when there is no available internet connection
    In the future we should move this to the DB.
    """

    cached_translations = [
        dict(fro="Die", lang="de", to_lang="en", to="the"),
        dict(fro="kleine", lang="de", to_lang="en", to="small")
    ]

    for test_translation in cached_translations:
        if test_translation["fro"] == word and \
                test_translation["lang"] == from_lang_code and \
                test_translation["to_lang"] == to_lang_code:
            return True, test_translation["to"]
    return False, None


def translate_from_to(word, from_lang_code, to_lang_code):
    """ translate_from_to('Der', 'de', 'en') -> 'the'
    :param word: expected to be an unicode string
    :param from_lang_code:
    :param to_lang_code:
    :return:
    """

    available, translation = get_cached_translation_if_available(word, from_lang_code, to_lang_code)
    if available:
        return translation

    translate_url = "https://www.googleapis.com/language/translate/v2"
    api_key = zeeguu.app.config.get("TRANSLATE_API_KEY")

    # quote replaces the unicode codes in \x notation with %20 notation.
    # quote_plus replaces spaces with +
    # The Google API prefers quote_plus,
    # This seems to be the (general) convention for info submitted
    # from forms with the GET method
    url = translate_url + \
        "?q=" + quote_plus(word.encode('utf8')) + \
        "&target=" + to_lang_code.encode('utf8') + \
        "&format=text".encode('utf8') + \
        "&source=" + from_lang_code.encode('utf8') + \
        "&key=" + api_key

    result = json.loads(urlopen(url).read())
    translation = result['data']['translations'][0]['translatedText']
    return translation


def translate_using_collins_dictionary(word):
    from zeeguu.libs.collins_api import API
    api = API(baseUrl="https://api.collinsdictionary.com"+'/api/v1/', accessKey=zeeguu.app.config.get("COLLINS_API_KEY"))
    data = json.loads(api.searchFirst("german-english", word, "html"), "utf-8")

    import xml.etree.ElementTree
    e = xml.etree.ElementTree.fromstring(data["entryContent"].encode('utf-8'))

    for atype in e.findall(".//*[@class='quote']"):
        try:
            print "-" + str(atype.text)
        except:
            pass

    return e





