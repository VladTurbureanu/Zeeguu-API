from urllib2 import urlopen
from urllib import quote_plus, unquote_plus
import zeeguu
import json

def translate_from_to(word, from_lang_code, to_lang_code):
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
    # print url
    result = json.loads(urlopen(url).read())
    translation = result['data']['translations'][0]['translatedText']
    return translation
