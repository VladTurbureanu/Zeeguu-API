# -*- coding: utf8 -*-
#
# Dispatching translation requests to the translation backend
# or loading some of the locally cached translations
#
# __author__ = 'mircea'
#
from zeeguu.translation.gslobe.gslobe_translator import get_translations_from_gslobe


def get_cached_translation_if_available(word, from_lang_code, to_lang_code):
    """get_cached_translation_if_available('Die', 'de', 'en') -> 'the'

    We want to be able to translate several words that are required in the
    test cases even when there is no available internet connection
    In the future we should move this to the DB.
    """

    cached_translations = [
        dict(fro="Die", lang="de", to_lang="en", to=["the"]),
        dict(fro="kleine", lang="de", to_lang="en", to=["small","tiny"])
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

    return get_translations_from_gslobe(word, from_lang_code, to_lang_code)









