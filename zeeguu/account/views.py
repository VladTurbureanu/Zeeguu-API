# -*- coding: utf8 -*-
__author__ = 'mir.lu'

import functools
import flask
import zeeguu
import sqlalchemy.exc
from zeeguu import model

# the main object we are exporting from this module
account = flask.Blueprint("account", __name__)


@account.before_request
def setup():
    if "user" in flask.session:
        flask.g.user = model.User.query.get(flask.session["user"])
    else:
        flask.g.user = None


@account.route("/reset_pass", methods=("GET", "POST"))
def reset_password():
    form = flask.request.form
    if flask.request.method == "POST":
        print "POST request"

    if flask.request.method == "POST" and form.get("reset_pass", False):
        try:
            password = form.get("password", None)
            email = form.get("email", None)
            if len(password) < 4:
                flask.flash("Password must be at least 4 characters long")
                return flask.render_template("reset_pass.html",flashed_messages=flask.get_flashed_messages())
            user = model.User.find(email)
            user.update_password(password)
            zeeguu.db.session.commit()
            return flask.redirect(flask.url_for("account.my_account"))
        except:
            flask.flash("Could not update your password.")
            return flask.render_template("reset_pass.html",flashed_messages=flask.get_flashed_messages())
    return flask.render_template("reset_pass.html")


@account.route("/my_account", methods=["GET"])
def my_account():
    if not flask.g.user:
        return flask.redirect(flask.url_for("gym.login"))

    return flask.render_template("my_account.html",
                                    user=flask.g.user)


@account.route("/create_account", methods=("GET", "POST"))
def create_account():

    if flask.request.method == "GET":
        return flask.render_template("create_account.html",
                                     languages=model.Language.all(),
                                     native_languages = model.Language.native_languages(),
                                     flashed_messages=flask.get_flashed_messages())

    form = flask.request.form
    if flask.request.method == "POST" and form.get("create_account", False):
        password = form.get("password", None)
        email = form.get("email", None)
        name = form.get("name", None)
        code = form.get("code", None)
        language = model.Language.find(form.get("language", None))
        native_language = model.Language.find(form.get("native_language", None))

        if not (code == "Kairo" or code == "unibe" or code == "klubschule"):
            flask.flash("Invitation code is not recognized. Please contact us.")
        elif password is None or email is None or name is None:
            flask.flash("Please enter your name, email address, and password")
        else:
            try:
                zeeguu.db.session.add(model.User(email, name, password, language, native_language))
                zeeguu.db.session.commit()
            except ValueError:
                flask.flash("The username could not be created. Please contact us.")
                return flask.render_template("create_account.html",
                                                flashed_messages=flask.get_flashed_messages(),
                                                languages=model.Language.all(),
                                                native_languages = model.Language.native_languages())
            except sqlalchemy.exc.IntegrityError:
                print "integrity error"
                flask.flash(email + " is already in use. Please select a different email.")
                return flask.render_template("create_account.html",
                                                flashed_messages=flask.get_flashed_messages(),
                                                languages=model.Language.all(),
                                                native_languages = model.Language.native_languages())

            print "looking for the user"
            user = model.User.authorize(email, password)
            flask.session["user"] = user.id
            return flask.redirect(flask.url_for("account.my_account"))


    return flask.render_template("create_account.html",
                                    flashed_messages=flask.get_flashed_messages(),
                                    languages=model.Language.all(),
                                    native_languages = model.Language.native_languages())
