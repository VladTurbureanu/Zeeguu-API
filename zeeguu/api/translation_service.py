from urllib2 import urlopen
from urllib import quote_plus, unquote_plus
import zeeguu
import json


def get_cached_translation_if_available(word, from_lang_code, to_lang_code):
    # We want to be able to translate several words that are required in the
    # test cases even when there is no available internet connection
    # In the future we should move this to the DB...

    testing_translations = [
        dict(fro="Die", lang="de", to_lang="en", to="the"),
        dict(fro="kleine", lang="de", to_lang="en", to="small")
    ]

    print "to translate->    " + word
    for test_translation in testing_translations:
        if test_translation["fro"] == word and \
                test_translation["lang"] == from_lang_code and \
                test_translation["to_lang"] == to_lang_code:
            return True, test_translation["to"]
    return False, None


def translate_from_to(word, from_lang_code, to_lang_code):

    available, translation = get_cached_translation_if_available(word, from_lang_code, to_lang_code)
    if available:
        return translation

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

    result = json.loads(urlopen(url).read())
    translation = result['data']['translations'][0]['translatedText']
    return translation