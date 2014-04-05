# -*- coding: utf8 -*-
import json

import flask

from zeeguu import model
import sys
import zeeguu


gym = flask.Blueprint("gym", __name__)


@gym.before_request
def setup():
    if "user" in flask.session:
        flask.g.user = model.User.query.get(flask.session["user"])
    else:
        flask.g.user = None


@gym.route("/")
def home():
    return flask.render_template("index.html")

@gym.route("/install")
def install():
    return flask.render_template("install.html")


@gym.route("/login", methods=("GET", "POST"))
def login():
    form = flask.request.form
    if flask.request.method == "POST" and form.get("login", False):
        password = form.get("password", None)
        email = form.get("email", None)
        if password is None or email is None:
            flask.flash("Please enter your email address and password")
        else:
            user = model.User.authorize(email, password)
            if user is None:
                flask.flash("Invalid email and password combination")
            else:
                flask.session["user"] = user.id
                return flask.redirect(flask.url_for("gym.contributions"))
    return flask.render_template("login.html")


@gym.route("/logout")
def logout():
    flask.session.pop("user", None)
    return flask.redirect(flask.url_for("gym.home"))


@gym.route("/history")
def history():
    if not flask.g.user:
        return flask.redirect(flask.url_for("gym.login"))
    searches = model.Search.query.filter_by(user=flask.g.user).order_by(model.Search.id.desc()).all()
    return flask.render_template("history.html", searches=searches)


@gym.route("/contributions")
def contributions():
    if not flask.g.user:
        return flask.redirect(flask.url_for("gym.login"))

    contribs,dates = flask.g.user.contribs_by_date()
    urls_by_date = {}
    contribs_by_url = {}
    for date in dates:
        sys.stderr.write(str(date)+"\n")
        for contrib in contribs[date]:
            urls_by_date.setdefault(date, set()).add(contrib.text.url)
            contribs_by_url.setdefault(contrib.text.url,[]).append(contrib)
    sys.stderr.write(str(urls_by_date)+"\n")
    sys.stderr.write(str(contribs_by_url)+"\n")



    return flask.render_template("contributions.html",
                                 contribs_by_url=contribs_by_url,
                                 urls_by_date=urls_by_date,
                                 sorted_dates=dates,
                                 all_urls = flask.g.user.recommended_urls())

@gym.route("/recommended_texts")
def recommended_texts():
    if not flask.g.user:
        return flask.redirect(flask.url_for("gym.login"))

    return flask.render_template("recommended_texts.html",
                                 # contribs_by_url=contribs_by_url,
                                 # urls_by_date=urls_by_date,
                                 # sorted_dates=dates,
                                 all_urls = flask.g.user.recommended_urls())


@gym.route("/flash_cards")
def flash_cards():
    if not flask.g.user:
        return flask.redirect(flask.url_for("gym.login"))
    languages = model.Language.query.all()
    return flask.render_template("flash_cards.html", languages=languages)



def get_next_card(user, from_lang, to_lang):
    if not flask.g.user:
        return flask.abort(401)

    from_lang = model.Language.find(from_lang)
    to_lang = model.Language.find(to_lang)

    contributions_never_tested = (
        model.Contribution.query.filter_by(user=flask.g.user)
                                .join(model.Word, model.Contribution.origin)
                                .join(model.WordAlias,
                                      model.Contribution.translation)
    )
    forward = contributions_never_tested.filter(
        model.Word.language == from_lang,
        model.WordAlias.language == to_lang
    )
    backward = contributions_never_tested.filter(
        model.Word.language == to_lang,
        model.WordAlias.language == from_lang
    )
    # zeeguu.app.logger.debug(forward)
    # zeeguu.app.logger.debug(backward)
    # contributions_never_tested = contributions_never_tested.filter_by(card=None)

    contributions_never_tested = forward.union(backward).filter_by(card=None)
    zeeguu.app.logger.debug(contributions_never_tested)

    if contributions_never_tested.count() > 0:
        card = model.Card(
            contributions_never_tested.
                join(model.Word, model.Contribution.origin).
                order_by(model.Word.word_rank,model.Contribution.time).first()
        )
        card . set_reason("never shown before"
                + str(card.contribution.origin.word_rank)
                + " card position: " + str(card.position))

    else:
        cards = (
            model.Card.query.join(model.Contribution, model.Card.contribution)
                            .filter_by(user=flask.g.user)
                            .join(model.Word, model.Contribution.origin)
                            .join(model.WordAlias,
                                  model.Contribution.translation)
        )
        forward = cards.filter(
            model.Word.language == from_lang,
            model.WordAlias.language == to_lang
        )
        backward = cards.filter(
            model.Word.language == to_lang,
            model.WordAlias.language == from_lang
        )
        cards = forward.union(backward).filter(model.Card.position < 5)
        card = cards.order_by(model.Card.last_seen).first()
        card . set_reason("all were shown before. rank: "
                          + str(card.contribution.origin.word_rank)
                          + " card position: " + str(card.position)
        )
    return card


@gym.route("/gym/question/<from_lang>/<to_lang>")
def question(from_lang, to_lang):
    if not flask.g.user:
        return flask.abort(401)

    card = get_next_card(flask.g.user, from_lang, to_lang)

    if card is None:
        return "\"NO CARDS\""

    card.seen()

    model.db.session.commit()

    question = card.contribution.origin
    answer = card.contribution.translation

    if question.language != from_lang:
        question, answer = answer, question

    return json.dumps({
        "question": question.word,
        "example":card.contribution.text.content,
        "answer": answer.word,
        "id": card.id,
        "reason":card.reason,
        "position": card.position
    })


@gym.route("/gym/correct/<card_id>", methods=("POST",))
def correct(card_id):
    card = model.Card.query.get(card_id)
    card.position += 1
    model.db.session.commit()
    return "OK"


@gym.route("/gym/wrong/<card_id>", methods=("POST",))
def wrong(card_id):
    card = model.Card.query.get(card_id)
    if card.position > 0:
        card.position -= 1
        model.db.session.commit()
    return "OK"
