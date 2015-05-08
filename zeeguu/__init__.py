#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
import os.path

import flask.ext.assets
import flask.ext.sqlalchemy

db = flask.ext.sqlalchemy.SQLAlchemy()

from zeeguu import app


app = app.app


if os.environ.get("ZEEGUU_TESTING") == "True":
    app.config.pop("SQLALCHEMY_DATABASE_URI", None)
    if os.uname()[0]=='Darwin':
        app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://zeeguu_test:zeeguu_test@localhost/zeeguu_test"
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://zeeguu_test:zeeguu_test@127.0.0.1/zeeguu_test"
    print "[ Using the test DB (" + app.config["SQLALCHEMY_DATABASE_URI"] + ") ]"
else:
    if not "SQLALCHEMY_DATABASE_URI" in app.config:
        print "seems like you have no config file..."
        exit()


env = flask.ext.assets.Environment(app)
env.cache = app.instance_path
env.directory = os.path.join(app.instance_path, "gen")
env.url = "/gen"
env.append_path(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "static"
), "/static")

db.init_app(app)
db.create_all(app=app)