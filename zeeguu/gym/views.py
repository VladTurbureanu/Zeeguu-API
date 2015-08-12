import json
from functools import wraps
import random

from datetime import timedelta, date
import flask
import decimal

from zeeguu import model
from zeeguu.model import UserWord, Bookmark, User, Text
import random
import datetime


gym = flask.Blueprint("gym", __name__)

class UserVisibleException (Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)



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
        flask.g.user = User.query.get(flask.session["user"])
    else:
        flask.g.user = None


@gym.route("/")
def home():
    if "user" in flask.session:
        return flask.redirect(flask.url_for("account.my_account"))
    return flask.render_template("index.html")


@gym.route("/prinz")
def prinz():
    return flask.render_template("prinz.html")


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
            user = User.authorize(email, password)
            if user is None:
                flask.flash("Invalid email and password combination")
            else:
                flask.session["user"] = user.id
                flask.session.permanent = True
                return flask.redirect(flask.request.args.get("next") or flask.url_for("account.my_account"))
    return flask.render_template("login.html")


@gym.route("/logout")
def logout():
    flask.session.pop("user", None)
    return flask.redirect(flask.url_for("gym.home"))

@gym.route("/logged_in")
def logged_in():
    if flask.session.get("user", None):
        return "YES"
    return "NO"


@gym.route("/bookmarks")
@login_first
def bookmarks():
    bookmarks,dates = flask.g.user.bookmarks_by_date()

    urls_by_date = {}
    bookmarks_by_url = {}
    for date in dates:
        for bookmark in bookmarks[date]:
            urls_by_date.setdefault(date, set()).add(bookmark.text.url)
            bookmarks_by_url.setdefault(bookmark.text.url,[]).append(bookmark)



    return flask.render_template("bookmarks.html",
                                 bookmarks_by_url=bookmarks_by_url,
                                 urls_by_date=urls_by_date,
                                 sorted_dates=dates,
                                 all_urls = flask.g.user.recommended_urls(),
                                 user = flask.g.user)



@gym.route("/gym/question/<from_lang>/<to_lang>")
@login_first
def question(from_lang, to_lang):
    # from_lang = model.Language.find(from_lang)
    # to_lang = model.Language.find(to_lang)

    bookmarks = (
        model.Bookmark
            .query.filter_by(user=flask.g.user)
            .join(UserWord, Bookmark.origin)
            .join(model.Language, UserWord.language)
            .filter(UserWord.language == flask.g.user.learned_language)

    ).all()


    tested_word = random.choice(bookmarks)

    # question = tested_word.origin
    answer = tested_word.translation()

    # if question.language != from_lang:
    #     question, answer = answer, question

    return json.dumps({
        "question": tested_word.origin.word,
        "example":tested_word.text.content,
        "url":tested_word.text.url.url,
        "answer": answer.word,
        "id": tested_word.id,
        "rank": tested_word.origin.importance_level(),
        "reason": "Random Word",
        "starred": False
    })



def question_new():
    bookmarks = (
        model.Bookmark
            .query.filter_by(user=flask.g.user)
            .join(UserWord, Bookmark.origin)
            .join(model.Language, UserWord.language)
            .join(Text, Bookmark.text)
            .filter(UserWord.language == flask.g.user.learned_language)
            .filter(Text.content != "")
    ).all()

    if len(bookmarks) == 0:
        raise UserVisibleException("It seems you have nothing to learn...")

    bookmark = random.choice(bookmarks)

    return {
        "question": bookmark.translations_rendered_as_text(),
        "example":bookmark.text.content,
        "url":bookmark.text.url.url,
        "answer": bookmark.origin.word,
        "bookmark_id": bookmark.id,
        "id": bookmark.id,
        "rank": bookmark.origin.importance_level(),
        "reason": "Random Word",
        "starred": False
    }

@gym.route("/recognize")
@login_first
def recognize():
    try:
        return flask.render_template(
                "recognize.html",
                user=flask.g.user,
                question = question_new())

    except UserVisibleException as e:
        return  flask.render_template(
                "message.html",
                message = e.value)

@gym.route("/m_recognize")
def m_recognize():
    if flask.g.user:
        try:
            return flask.render_template(
                    "recognize.html",
                    mobile=True,
                    user=flask.g.user,
                    question = question_new())
        except UserVisibleException as e:
            return  flask.render_template(
                    "message.html",
                    mobile=True,
                    message = e.value)
    else:
        return "not logged in..."

@gym.route ("/browser_home")
def browser_home():
    return  flask.render_template(
            "browser_home.html",
            mobile=True)


@gym.route("/study_before_play")
@login_first
def study_before_play():
    def get_domain_from_url(url):
        from urlparse import urlparse
        parsed_uri = urlparse(url)
        domain = '{uri.netloc}'.format(uri=parsed_uri)
        return domain

    url_to_redirect_to = flask.request.args.get('to','')


    try:
        new_question = question_new()
        return flask.render_template("recognize.html",
                                     question = new_question,
                                     user=flask.g.user,
                                     redirect_to_url=url_to_redirect_to,
                                     redirect_to_domain=get_domain_from_url(url_to_redirect_to))
    except:
        return flask.redirect(url_to_redirect_to)



def redisplay_card_simple(cards):
    cards.sort(key=lambda x: x.last_seen)
    card = cards[1]
    return card


def select_next_card_aware_of_days(cards):

    interesting_intervals = [1,2,7,31]
    interesting_dates = [date.today() - timedelta(days=x) for x in interesting_intervals]


    interesting_cards = [card for card in cards if card.last_seen.date() in interesting_dates]
    interesting_cards.sort(key=lambda card: card.bookmark.origin.importance_level())

    if interesting_cards:
        card = interesting_cards[0]
        card.set_reason("seen on: " + card.last_seen.strftime("%d/%m/%y"))
        return card

    cards_not_seen_today = [card for card in cards if card.last_seen.date() != date.today()]
    cards_not_seen_today.sort(key=lambda card: card.bookmark.origin.importance_level())

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






@gym.route("/gym/delete_bookmark/<bookmark_id>", methods=("POST",))
@login_first
def delete(bookmark_id):
    session = model.db.session
    bookmark = model.Bookmark.query.get(bookmark_id)
    if bookmark == None:
        return "Not found"

    text = model.Text.query.get(bookmark.text.id)
    url = text.url

    # delete the associated cards
    cards = model.Card.query.filter_by(bookmark_id=bookmark.id).all()
    for card in cards:
        session.delete(card)

    # contrib goes, and so does the associated text
    session.delete(bookmark)
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
        # correct(question_id, "Web::Recognize", model.ExerciseOutcome.find("Correct"), None)
        return "CORRECT"
    else:
        # wrong(question_id, "Web::Recognize", model.ExerciseOutcome.find("Wrong"), None)
        return "WRONG"


@gym.route("/gym/create_new_exercise/<exercise_outcome>/<exercise_source>/<exercise_solving_speed>/<bookmark_id>",
           methods=["POST"])
def create_new_exercise(exercise_outcome,exercise_source,exercise_solving_speed,bookmark_id):
    bookmark = model.Bookmark.query.filter_by(
        id=bookmark_id
    ).first()
    new_source = model.ExerciseSource.query.filter_by(
        source=exercise_source
    ).first()
    new_outcome=model.ExerciseOutcome.query.filter_by(
        outcome=exercise_outcome
    ).first()
    if new_source is None or new_outcome is None :
         return "FAIL"
    exercise = model.Exercise(new_outcome,new_source,exercise_solving_speed,datetime.datetime.now())
    bookmark.add_new_exercise(exercise)
    model.db.session.add(exercise)
    model.db.session.commit()
    bookmarks = model.Bookmark.find_all_by_user_and_word(flask.g.user,bookmark.origin)
    ex_prob = model.ExerciseBasedProbability.find(flask.g.user, bookmark.origin)
    total_prob = 0
    for b in bookmarks:
        ex_prob.know_bookmark_probability(b)
        total_prob +=float(ex_prob.probability)
    ex_prob.probability = total_prob/len(bookmarks)
    model.db.session.commit()
    if model.WordRank.exists(bookmark.origin.word,bookmark.origin.language):
        word_rank = model.WordRank.find(bookmark.origin.word, bookmark.origin.language)
        if model.EncounterBasedProbability.exists(flask.g.user,word_rank):
            enc_prob = model.EncounterBasedProbability.find(flask.g.user,word_rank)
            known_word_prob = model.KnownWordProbability.find(flask.g.user,bookmark.origin,word_rank)
            known_word_prob.probability = model.KnownWordProbability.calculateAggregatedProb(ex_prob.probability,enc_prob.probability)
        else:
            known_word_prob = model.KnownWordProbability.find(flask.g.user,bookmark.origin,word_rank)
            known_word_prob.probability = ex_prob.probability
    model.db.session.commit()
    return "OK"


@gym.route("/gym/exercise_outcome/<bookmark_id>/<exercise_source>/<exercise_outcome>/<exercise_solving_speed>", methods=("POST",))
def correct(bookmark_id, exercise_source, exercise_outcome, exercise_solving_speed):
    # bookmark = model.Bookmark.query.get(bookmark_id)
    # bookmark.add_exercise_outcome(exercise_source, exercise_outcome, exercise_solving_speed)
    # model.db.session.commit()
    return "OK"


@gym.route("/gym/wrong/<bookmark_id>/<exercise_source>/<exercise_outcome>/<exercise_solving_speed>", methods=("POST",))
def wrong(bookmark_id, exercise_source, exercise_outcome, exercise_solving_speed):
    # bookmark = model.Bookmark.query.get(bookmark_id)
    # bookmark.add_exercise_outcome(exercise_source, exercise_outcome, exercise_solving_speed)
    # model.db.session.commit()
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
    word = UserWord.query.get(word_id)
    user = User.find_by_id(user_id)
    user.star(word)
    model.db.session.commit()
    return "OK"

@gym.route("/gym/unstarred_word/<word_id>/<user_id>", methods=("POST",))
def unstarred_word(word_id,user_id):
    word = UserWord.query.get(word_id)
    user = User.find_by_id(user_id)
    user.starred_words.remove(word)
    model.db.session.commit()
    print word + " is now *unstarred* for user " + user.name
    return "OK"