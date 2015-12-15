# -*- coding: utf8 -*-
import flask
# We need to define the bluepring here, because all the files containing controllers use it
gym = flask.Blueprint("gym", __name__)
import views
import reset_pass


