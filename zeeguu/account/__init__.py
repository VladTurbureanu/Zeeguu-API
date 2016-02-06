# -*- coding: utf8 -*-

import flask

from zeeguu.api.model_core import User

# we define the blueprint here, and extended it in several files
acc = flask.Blueprint("account", __name__)

@acc.before_request
def setup():
    if "user" in flask.session:
        flask.g.user = User.query.get(flask.session["user"])
    else:
        flask.g.user = None

import create_and_show
import reset_pass

