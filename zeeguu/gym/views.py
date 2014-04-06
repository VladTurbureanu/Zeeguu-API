from datetime import datetime, timedelta, date
import json

import flask

from zeeguu import model
import sys


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
    # contribs_by_url = {}
    # for contrib in contribs:
    #     contribs_by_url.setdefault(contrib.text.url, []).append(contrib)

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

    # contribs,dates = flask.g.user.contribs_by_date()
    # contribs_by_url = {}
    # for contrib in contribs:
    #     contribs_by_url.setdefault(contrib.text.url, []).append(contrib)

    # urls_by_date = {}
    # contribs_by_url = {}
    # for date in dates:
    #     sys.stderr.write(str(date)+"\n")
    #     for contrib in contribs[date]:
    #         urls_by_date.setdefault(date, set()).add(contrib.text.url)
    #         contribs_by_url.setdefault(contrib.text.url,[]).append(contrib)
    # sys.stderr.write(str(urls_by_date)+"\n")
    # sys.stderr.write(str(contribs_by_url)+"\n")



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


def redisplay_card_simple(cards):
    cards.sort(key=lambda x: x.last_seen)
    card = cards[1]
    return card


def redisplay_card_aware_of_days(cards):

    interesting_intervals = [1,2,7,31]
    interesting_dates = [date.today() - timedelta(days=x) for x in interesting_intervals]


    interesting_cards = [card for card in cards if card.last_seen.date() in interesting_dates]
    interesting_cards.sort(key=lambda card: card.contribution.origin.word_rank)

    if interesting_cards:
        card = interesting_cards[0]
        card.set_reason("seen on: " + card.last_seen.strftime("%d/%m/%y") + " rank: " + str(card.contribution.origin.word_rank))
        return card

    cards_not_seen_today = [card for card in cards if card.last_seen.date() != date.today()]
    cards_not_seen_today.sort(key=lambda card: card.contribution.origin.word_rank)

    if cards_not_seen_today:
        card = cards_not_seen_today[0]
        card.set_reason("seen on: " + card.last_seen.strftime("%d/%m/%y") + " rank: " + str(card.contribution.origin.word_rank))
        return card

    return None




@gym.route("/gym/question/<from_lang>/<to_lang>")
def question(from_lang, to_lang):
    if not flask.g.user:
        return flask.abort(401)

    from_lang = model.Language.find(from_lang)
    to_lang = model.Language.find(to_lang)

    contributions = (
        model.Contribution.query.filter_by(user=flask.g.user)
                                .join(model.Word, model.Contribution.origin)
                                .join(model.WordAlias,
                                      model.Contribution.translation)
    )
    forward = contributions.filter(
        model.Word.language == from_lang,
        model.WordAlias.language == to_lang
    )
    backward = contributions.filter(
        model.Word.language == to_lang,
        model.WordAlias.language == from_lang
    )
    contributions = forward.union(backward).filter_by(card=None)
    if contributions.count() > 0:
        card = model.Card(
            contributions.join(model.Word, model.Contribution.origin).order_by(model.Word.word_rank, model.Contribution.time).first()
        )
        card.set_reason("never seen before. " + " rank: " + str(card.contribution.origin.word_rank))
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


        cards = forward.union(backward).filter(model.Card.position < 5).all()
        card = redisplay_card_aware_of_days(cards)



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
        "position": card.position,
        "reason": card.reason
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