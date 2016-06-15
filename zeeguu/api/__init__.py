import flask
api = flask.Blueprint("api", __name__)
# These files have to be here.
# They require the api object
from zeeguu.api.endpoints import download_content_from_url
from zeeguu.api.endpoints import endpoints
from zeeguu.api.endpoints import exercises
from zeeguu.api.endpoints import feeds
from zeeguu.api.endpoints import sessions
from zeeguu.api.endpoints import smartwatch
from zeeguu.api.endpoints import system_languages
from zeeguu.api.endpoints import text_analysis
from zeeguu.api.endpoints import translate_and_bookmark
from zeeguu.api.endpoints import user_data
from zeeguu.api.endpoints import user_settings
from zeeguu.api.endpoints import user_statistics
