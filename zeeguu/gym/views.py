import json
import flask
import zeeguu

from zeeguu.api.model_core import UserWord, Bookmark, User, Text, ExerciseSource, ExerciseOutcome, Exercise, ExerciseBasedProbability, RankedWord, EncounterBasedProbability, KnownWordProbability
from zeeguu.gym.model import Card
from zeeguu.api.model_core import db
import datetime

from zeeguu.gym import gym

from question_selection_strategies import new_random_question
from user_message import UserVisibleException

from views_utils import login_first

from knowledge_estimator import update_probabilities_for_word
from zeeguu.the_librarian.website_recommender import recent_domains_with_times, frequent_domains, recommendations


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
    # Note, that there is also an API endpoint for logout called logout_session
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
    bookmarks_list,dates = flask.g.user.bookmarks_by_date()

    urls_by_date = {}
    bookmarks_by_url = {}
    for date in dates:
        for bookmark in bookmarks_list[date]:
            urls_by_date.setdefault(date, set()).add(bookmark.text.url)
            bookmarks_by_url.setdefault(bookmark.text.url,[]).append(bookmark)

    return flask.render_template("bookmarks.html",
                                 bookmarks_by_url=bookmarks_by_url,
                                 urls_by_date=urls_by_date,
                                 sorted_dates=dates,
                                 user=flask.g.user)


@gym.route("/gym/question/<from_lang>/<to_lang>")
@login_first
def question(from_lang, to_lang):
    return json.dumps(new_random_question())


@gym.route("/recognize")
@login_first
def recognize():
    try:
        return flask.render_template(
                "recognize.html",
                user=flask.g.user,
                question = new_random_question())

    except UserVisibleException as e:
        return flask.render_template("message.html",message = e.value)

@gym.route("/m_recognize")
def m_recognize():
    if flask.g.user:
        try:
            return flask.render_template(
                    "recognize.html",
                    mobile=True,
                    user=flask.g.user,
                    question = new_random_question())
        except UserVisibleException as e:
            return flask.render_template("message.html",mobile=True, message=e.value)
    else:
        return "not logged in..."


@gym.route ("/browser_home/expanded/")
def browser_home_expand():
    return browser_home(42)


@gym.route ("/browser_home/")
def browser_home(item_count = 3):
    return flask.render_template(
            "browser_home.html",
            recent_domains_and_times = recent_domains_with_times(flask.g.user),
            # recent_domains_and_times = [],
            recent_domains_and_times_count = len(recent_domains_with_times(flask.g.user)),
            # recent_domains_and_times_count = 0,

            domain_and_frequency_map = frequent_domains(flask.g.user),
            # domain_and_frequency_map = [],
            domain_and_frequency_map_size = len(frequent_domains(flask.g.user)),
            # domain_and_frequency_map_size = 0,

            recommendations = recommendations(flask.g.user),
            item_count = item_count,
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
        new_question = new_random_question()
        return flask.render_template("recognize.html",
                                     question = new_question,
                                     user=flask.g.user,
                                     redirect_to_url=url_to_redirect_to,
                                     redirect_to_domain=get_domain_from_url(url_to_redirect_to))
    except:
        return flask.redirect(url_to_redirect_to)


@gym.route("/gym/delete_bookmark/<bookmark_id>", methods=("POST",))
@login_first
def delete(bookmark_id):

    # Beware, the there is another delete_bookmark in the zeeguu API!!!
    bookmark = Bookmark.query.get(bookmark_id)
    if not bookmark:
        return "Not found"

    text = Text.query.get(bookmark.text.id)

    # delete the associated cards
    cards = Card.query.filter_by(bookmark_id=bookmark.id).all()
    for card in cards:
        zeeguu.db.session.delete(card)

    # bookmark goes
    zeeguu.db.session.delete(bookmark)
    zeeguu.db.session.commit()

    # If no more bookmarks point to the text, text goes too
    if not (text.all_bookmarks()):
        zeeguu.db.session.delete(text)
        zeeguu.db.session.commit()

    # url = text.url
    # if not url.texts:
    #     session.delete(url)
    #     session.commit()
    return "OK"


@gym.route("/gym/test_answer/<answer>/<expected>/<question_id>", methods=["POST"])
def submit_answer(answer, expected,question_id):
    if answer.lower() == expected.lower() \
            or (answer+".").lower() == expected.lower():
        # correct(question_id, "Web::Recognize", ExerciseOutcome.find("Correct"), None)
        return "CORRECT"
    else:
        # wrong(question_id, "Web::Recognize", ExerciseOutcome.find("Wrong"), None)
        return "WRONG"


@gym.route("/gym/create_new_exercise/<exercise_outcome>/<exercise_source>/<exercise_solving_speed>/<bookmark_id>",
           methods=["POST"])
def create_new_exercise(exercise_outcome,exercise_source,exercise_solving_speed,bookmark_id):
    """
    In the model parlance, an exercise is an entry in a table that
    logs the performance of an exercise. Every such performance, has a source, and an outcome.

    :param exercise_outcome:
    :param exercise_source:
    :param exercise_solving_speed:
    :param bookmark_id:
    :return:
    """

    try:
        bookmark = Bookmark.find(bookmark_id)
        new_source = ExerciseSource.find_by_source(exercise_source)
        new_outcome = ExerciseOutcome.find(exercise_outcome)

        if not new_source or not new_outcome:
            return "FAIL"

        exercise = Exercise(new_outcome,new_source,exercise_solving_speed,datetime.datetime.now())
        bookmark.add_new_exercise(exercise)
        zeeguu.db.session.add(exercise)
        zeeguu.db.session.commit()

        update_probabilities_for_word(bookmark.origin)
        return "OK"
    except:
        return "FAIL"



@gym.route("/gym/exercise_outcome/<bookmark_id>/<exercise_source>/<exercise_outcome>/<exercise_solving_speed>", methods=("POST",))
def correct(bookmark_id, exercise_source, exercise_outcome, exercise_solving_speed):
    # bookmark = Bookmark.query.get(bookmark_id)
    # bookmark.add_exercise_outcome(exercise_source, exercise_outcome, exercise_solving_speed)
    # db.session.commit()
    return "OK"


@gym.route("/gym/wrong/<bookmark_id>/<exercise_source>/<exercise_outcome>/<exercise_solving_speed>", methods=("POST",))
def wrong(bookmark_id, exercise_source, exercise_outcome, exercise_solving_speed):
    # bookmark = Bookmark.query.get(bookmark_id)
    # bookmark.add_exercise_outcome(exercise_source, exercise_outcome, exercise_solving_speed)
    # db.session.commit()
    return "OK"

@gym.route("/gym/starred_card/<card_id>", methods=("POST",))
def starred(card_id):
    card = Card.query.get(card_id)
    card.star()
    zeeguu.db.session.commit()
    return "OK"

@gym.route("/gym/unstarred_card/<card_id>", methods=("POST",))
def unstarred(card_id):
    card = Card.query.get(card_id)
    card.unstar()
    zeeguu.db.session.commit()
    return "OK"

@gym.route("/gym/starred_word/<word_id>/<user_id>", methods=("POST",))
def starred_word(word_id,user_id):
    word = UserWord.query.get(word_id)
    user = User.find_by_id(user_id)
    user.star(word)
    zeeguu.db.session.commit()
    return "OK"

@gym.route("/gym/unstarred_word/<word_id>/<user_id>", methods=("POST",))
def unstarred_word(word_id,user_id):
    word = UserWord.query.get(word_id)
    user = User.find_by_id(user_id)
    user.starred_words.remove(word)
    zeeguu.db.session.commit()
    print word + " is now *unstarred* for user " + user.name
    return "OK"


