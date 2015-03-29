from datetime import timedelta, date
import json
from functools import wraps

import flask

from zeeguu import model
import sys
import random


gym = flask.Blueprint("gym", __name__)


def login_first(fun):
    """
    Makes sure that the user is logged_in.
    If not, appends the intended url to the login url,
    and redirects to login.
    """
    @wraps(fun)
    def decorated_function(*args, **kwargs):
        if flask.g.user:
            return fun(*args, **kwargs)
        else:
            next_url = flask.request.url
            login_url = '%s?next=%s' % (flask.url_for('gym.login'), next_url)
            return flask.redirect(login_url)
    return decorated_function


@gym.before_request
def setup():
    if "user" in flask.session:
        flask.g.user = model.User.query.get(flask.session["user"])
    else:
        flask.g.user = None


@gym.route("/")
def home():
    if "user" in flask.session:
        return flask.redirect(flask.url_for("gym.contributions"))
    return flask.render_template("index.html")


@gym.route("/test_german")
def test_german():
    return flask.render_template("test_german.html")


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
                flask.session.permanent = True
                return flask.redirect(flask.request.args.get("next") or flask.url_for("gym.contributions"))
    return flask.render_template("login.html")


@gym.route("/logout")
def logout():
    flask.session.pop("user", None)
    return flask.redirect(flask.url_for("gym.home"))


@gym.route("/history")
@login_first
def history():
    searches = model.Search.query.filter_by(user=flask.g.user).order_by(model.Search.id.desc()).all()
    return flask.render_template("history.html", searches=searches)


@gym.route("/contributions")
@login_first
def contributions():
    contribs,dates = flask.g.user.contribs_by_date()

    urls_by_date = {}
    contribs_by_url = {}
    for date in dates:
        for contrib in contribs[date]:
            urls_by_date.setdefault(date, set()).add(contrib.text.url)
            contribs_by_url.setdefault(contrib.text.url,[]).append(contrib)



    return flask.render_template("contributions.html",
                                 contribs_by_url=contribs_by_url,
                                 urls_by_date=urls_by_date,
                                 sorted_dates=dates,
                                 all_urls = flask.g.user.recommended_urls(),
                                 user = flask.g.user)

@gym.route("/recommended_texts")
@login_first
def recommended_texts():
    return flask.render_template("recommended_texts.html",
                                 # contribs_by_url=contribs_by_url,
                                 # urls_by_date=urls_by_date,
                                 # sorted_dates=dates,
                                 all_urls = flask.g.user.recommended_urls())




@gym.route("/translate_with_context")
@login_first
def translate_with_context():
    lang = model.Language.query.all()
    return flask.render_template("translate_with_context.html", languages=lang)


@gym.route("/recognize")
@login_first
def recognize():
    lang = model.Language.query.all()
    return flask.render_template("recognize.html", languages=lang)

@gym.route("/study_before_play")
@login_first
def study_before_play():
    def get_domain_from_url(url):
        from urlparse import urlparse
        parsed_uri = urlparse(url)
        domain = '{uri.netloc}'.format(uri=parsed_uri)
        return domain

    url_to_redirect_to = flask.request.args.get('to','')

    lang = model.Language.query.all()
    return flask.render_template("study_before_play.html",
                                 languages=lang,
                                 redirect_to_url=url_to_redirect_to,
                                 redirect_to_domain=get_domain_from_url(url_to_redirect_to))



def redisplay_card_simple(cards):
    cards.sort(key=lambda x: x.last_seen)
    card = cards[1]
    return card


def select_next_card_aware_of_days(cards):

    interesting_intervals = [1,2,7,31]
    interesting_dates = [date.today() - timedelta(days=x) for x in interesting_intervals]


    interesting_cards = [card for card in cards if card.last_seen.date() in interesting_dates]
    interesting_cards.sort(key=lambda card: card.contribution.origin.word_rank)

    if interesting_cards:
        card = interesting_cards[0]
        card.set_reason("seen on: " + card.last_seen.strftime("%d/%m/%y"))
        return card

    cards_not_seen_today = [card for card in cards if card.last_seen.date() != date.today()]
    cards_not_seen_today.sort(key=lambda card: card.contribution.origin.word_rank)

    if cards_not_seen_today:
        card = cards_not_seen_today[0]
        card.set_reason("seen on: " + card.last_seen.strftime("%d/%m/%y"))
        return card

    # All cards were seen today. Just return a random one
    if cards:
        card = random.choice(cards)
        card.set_reason("random word: all others are seen today.")
        return card

    return None


@gym.route("/gym/question_with_min_level/<level>/<from_lang>/<to_lang>")
@login_first
def question_with_min_level(level, from_lang, to_lang):
    card = None

    from_lang = model.Language.find(from_lang)
    to_lang = model.Language.find(to_lang)

    contributions = (
        model.Contribution.query.filter_by(user=flask.g.user)
                                .join(model.Word, model.Contribution.origin)
                                .join(model.WordAlias,
                                      model.Contribution.synoym_translations)
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

    # in this case we can not create cards... we can only look at cards that are at least
    # level 3
    if contributions.count() > 0:
        card = model.Card(
            contributions.join(model.Word, model.Contribution.origin).order_by(model.Word.word_rank, model.Contribution.time).first()
        )
        card.set_reason("First rehearsal. ")
        # return "\"NO CARDS\""
    else:
        cards = (
            model.Card.query.join(model.Contribution, model.Card.contribution)
                            .filter_by(user=flask.g.user)
                            .join(model.Word, model.Contribution.origin)
                            .join(model.WordAlias,
                                  model.Contribution.synoym_translations)
        )
        forward = cards.filter(
            model.Word.language == from_lang,
            model.WordAlias.language == to_lang
        )
        backward = cards.filter(
            model.Word.language == to_lang,
            model.WordAlias.language == from_lang
        )

        cards = forward.union(backward).filter(model.Card.position > level).filter(model.Card.position < 7).all()
        if not cards:
            cards = forward.union(backward).filter(model.Card.position < 7).all()
        card = select_next_card_aware_of_days(cards)

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
        "url":card.contribution.text.url.url,
        "answer": answer.word,
        "id": card.id,
        "position": card.position,
        "reason": card.reason,
        "rank":card.contribution.origin.word_rank,
        "starred": card.is_starred()
    })

@gym.route("/gym/question/<from_lang>/<to_lang>")
@login_first
def question(from_lang, to_lang):
    from_lang = model.Language.find(from_lang)
    to_lang = model.Language.find(to_lang)

    contributions = (
        model.Contribution.query.filter_by(user=flask.g.user)
                                .join(model.Word, model.Contribution.origin)
                                .join(model.WordAlias,
                                      model.Contribution.synoym_translations)
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
        card.set_reason("First rehearsal. ")
    else:
        cards = (
            model.Card.query.join(model.Contribution, model.Card.contribution)
                            .filter_by(user=flask.g.user)
                            .join(model.Word, model.Contribution.origin)
                            .join(model.WordAlias,
                                  model.Contribution.synoym_translations)
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
        card = select_next_card_aware_of_days(cards)



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
        "url":card.contribution.text.url.url,
        "answer": answer.word,
        "id": card.id,
        "position": card.position,
        "rank":card.contribution.origin.word_rank,
        "reason": card.reason,
        "starred": card.is_starred()
    })



@gym.route("/gym/delete_contribution/<contribution_id>", methods=("POST",))
@login_first
def delete(contribution_id):
    session = model.db.session
    contrib = model.Contribution.query.get(contribution_id)
    text = model.Text.query.get(contrib.text.id)
    url = text.url

    # delete the associated cards
    cards = model.Card.query.filter_by(contribution_id=contrib.id).all()
    for card in cards:
        session.delete(card)

    # contrib goes, and so does the associated text
    session.delete(contrib)
    session.delete(text)
    session.commit()

    # url only if there are no more texts for it
    if not url.texts:
        session.delete(url)
        session.commit()
    return "OK"


@gym.route("/gym/test_answer/<answer>/<expected>/<question_id>", methods=["POST"])
def submit_answer(answer, expected,question_id):
    if answer.lower() == expected.lower() \
            or (answer+".").lower() == expected.lower():
        correct(question_id)
        return "CORRECT"
    else:
        wrong(question_id)
        return "WRONG"


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

@gym.route("/gym/starred_card/<card_id>", methods=("POST",))
def starred(card_id):
    card = model.Card.query.get(card_id)
    card.star()
    model.db.session.commit()
    return "OK"

@gym.route("/gym/unstarred_card/<card_id>", methods=("POST",))
def unstarred(card_id):
    card = model.Card.query.get(card_id)
    card.unstar()
    model.db.session.commit()
    return "OK"

@gym.route("/gym/starred_word/<word_id>/<user_id>", methods=("POST",))
def starred_word(word_id,user_id):
    word = model.Word.query.get(word_id)
    user = model.User.find_by_id(user_id)
    user.star(word)
    model.db.session.commit()
    return "OK"

@gym.route("/gym/unstarred_word/<word_id>/<user_id>", methods=("POST",))
def unstarred_word(word_id,user_id):
    word = model.Word.query.get(word_id)
    user = model.User.find_by_id(user_id)
    user.starred_words.remove(word)
    model.db.session.commit()
    print word.word + " is now *unstarred* for user " + user.name
    return "OK"
