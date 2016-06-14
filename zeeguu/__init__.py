#!/usr/bin/env python
# -*- coding: utf8 -*-
import platform
import os.path

import flask.ext.assets
import flask.ext.sqlalchemy

db = flask.ext.sqlalchemy.SQLAlchemy()

from zeeguu import app
app = app.app


def platform_is_osx():
    """
    :return:
    """
    return platform.uname()[0]=='Darwin'


def get_platform_specific_mysql_hostname():
    """
    the hostname for the mysql connection string has to be named differently on different platforms!
    :return:
    """
    if platform_is_osx():
        mysql_hostname = "localhost"
    else:
        mysql_hostname = "127.0.0.1"
    return mysql_hostname


def setup_db_connection():
    """

    :return: does not return anything.
     pure side effects :)
    """

    mysql_hostname = get_platform_specific_mysql_hostname()

    db_connection_string = "mysql://zeeguu_test:zeeguu_test@"

    if os.environ.get("ZEEGUU_TESTING"):
        db_name = "zeeguu_test"
        if os.environ.get("ZEEGUU_PERFORMANCE_TESTING"):
            db_name = "zeeguu_performance_test"
        db_connection_string += mysql_hostname+"/"+db_name
        # db_connection_string = "mysql://travis:@127.0.0.1/"+db_name

        app.config["SQLALCHEMY_DATABASE_URI"] = db_connection_string
    else:
        #  Ooops: we are not testing, and we don't have a DB configured!
        if not "SQLALCHEMY_DATABASE_URI" in app.config:
            print ("No db configured. You probably have no config file...")
            exit()

    print ("->>  DB Connection String: " + app.config["SQLALCHEMY_DATABASE_URI"])

    # getting rid of a warning in new version of SQLAlchemy
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


setup_db_connection()
env = flask.ext.assets.Environment(app)
env.cache = app.instance_path
env.directory = os.path.join(app.instance_path, "gen")
env.url = "/gen"
env.append_path(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "static"
), "/static")

db.init_app(app)
db.create_all(app=app)

from zeeguu.model.ranked_word import RankedWord

with app.app_context():
    RankedWord.cache_ranked_words()
