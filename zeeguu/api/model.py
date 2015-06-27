# -*- coding: utf8 -*-
import re
import random
import datetime
import codecs
import math
import flask
from sqlalchemy import Column, Table, ForeignKey, Integer, DECIMAL

import sqlalchemy.orm.exc

from zeeguu import db
from zeeguu import util
import zeeguu
from sqlalchemy.orm import relationship
red_words_association_table = Table('starred_words_association', db.Model.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('starred_word_id', Integer, ForeignKey('user_words.id'))
)



class User(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    password = db.Column(db.LargeBinary(255))
    password_salt = db.Column(db.LargeBinary(255))
    learned_language_id = db.Column(
        db.String(2),
        db.ForeignKey("language.id")
    )
    learned_language = sqlalchemy.orm.relationship("Language", foreign_keys=[learned_language_id])
    starred_words = relationship("UserWord", secondary="starred_words_association")

    native_language_id = db.Column(
        db.String (2),
        db.ForeignKey("language.id")
    )
    native_language = sqlalchemy.orm.relationship("Language", foreign_keys=[native_language_id])

    def __init__(self, email, username, password, learned_language=None, native_language = None):
        self.email = email
        self.name = username
        self.update_password(password)
        self.learned_language = learned_language or Language.default_learned()
        self.native_language = native_language or Language.default_native_language()

    def __repr__(self):
        return '<User %r>' % (self.email)

    def has_starred(self,word):
        return word in self.starred_words

    def star(self, word):
        self.starred_words.append(word)
        print word.word + " is now starred for user " + self.name
        # TODO: Does this work without a commit here? To double check.


    def set_learned_language(self, code):
        self.learned_language = Language.find(code)

    def set_native_language(self, code):
        self.native_language = Language.find(code)

    @classmethod
    def find_all(cls):
        return User.query.all()


    @classmethod
    def find(cls, email):
        return User.query.filter(User.email == email).one()

    @classmethod
    def find_by_id(cls, id):
        return User.query.filter(User.id == id).one()


    @sqlalchemy.orm.validates("email")
    def validate_email(self, col, email):
        if "@" not in email:
            raise ValueError("Invalid email address")
        return email

    @sqlalchemy.orm.validates("password")
    def validate_password(self, col, password):
        if password is None or len(password) == 0:
            raise ValueError("Invalid password")
        return password

    @sqlalchemy.orm.validates("name")
    def validate_name(self, col, name):
        if name is None or len(name) == 0:
            raise ValueError("Invalid username")
        return name

    def update_password(self, password):
        self.password_salt = "".join(
            chr(random.randint(0, 255)) for i in range(32)
        )
        self.password = util.password_hash(password, self.password_salt)

    @classmethod
    def authorize(cls, email, password):
        try:
            user = cls.query.filter(cls.email == email).one()
            if user.password == util.password_hash(password,
                                                   user.password_salt):
                return user
        except sqlalchemy.orm.exc.NoResultFound:
            return None
	
    def bookmarks_chronologically(self):
	    return Bookmark.query.filter_by(user_id=self.id).order_by(Bookmark.time.desc()).all()

    def user_words(self):
        return map((lambda x: x.origin.word), self.all_bookmarks())

    def all_bookmarks(self):
        return Bookmark.query.filter_by(user_id=self.id).order_by(Bookmark.time.desc()).all()

    def bookmark_count(self):
        return len(self.all_bookmarks())

    def word_count(self):
        return len(self.user_words())

    def bookmarks_by_date(self):
	def extract_day_from_date(bookmark):
		return (bookmark, bookmark.time.replace(bookmark.time.year, bookmark.time.month, bookmark.time.day,0,0,0,0))

	bookmarks = self.all_bookmarks()
	bookmarks_by_date = dict()
				                                        
	for elem in map(extract_day_from_date, bookmarks):
		bookmarks_by_date.setdefault(elem[1],[]).append(elem[0])

	sorted_dates = bookmarks_by_date.keys()
	sorted_dates.sort(reverse=True)
	return bookmarks_by_date, sorted_dates

    def unique_urls(self):
        urls = set()
        for b in self.all_bookmarks():
            urls.add(b.text.url)
        return urls

    def recommended_urls(self):
        urls_to_words = {}
        for bookmark in self.all_bookmarks():
            if bookmark.text.url.url != "undefined":
                urls_to_words.setdefault(bookmark.text.url,0)
                urls_to_words [bookmark.text.url] += bookmark.origin.importance_level()
        return sorted(urls_to_words, key=urls_to_words.get, reverse=True)

    def get_known_bookmarks(self):
        bookmarks = Bookmark.find_all_filtered_by_user()
        i_know_bookmarks=[]
        for bookmark in bookmarks:
            if Bookmark.is_sorted_exercise_log_after_date_outcome(ExerciseOutcome.IKNOW, bookmark):
                    i_know_bookmark_dict = {}
                    i_know_bookmark_dict['id'] = bookmark.id
                    i_know_bookmark_dict['origin'] = bookmark.origin.word
                    i_know_bookmark_dict['text']= bookmark.text.content
                    i_know_bookmark_dict['time']=bookmark.time.strftime('%m/%d/%Y')
                    i_know_bookmarks.append(i_know_bookmark_dict.copy())
        return i_know_bookmarks

    def get_known_bookmarks_count(self):
        return len(self.get_known_bookmarks())

    def filter_bookmark_context(self, bookmark, words_of_all_bookmarks_content):
        bookmark_content_words = re.sub("[^\w]", " ",  bookmark.text.content).split()
        words_of_all_bookmarks_content.extend(bookmark_content_words)
        return words_of_all_bookmarks_content



    def filter_bookmark_context_by_rank(self, words_known_from_user, lang):
        filtered_words_known_from_user = []
        for word_known in words_known_from_user:
            if WordRank.exists(word_known.lower(), lang):
                filtered_words_known_from_user.append(word_known)
        return filtered_words_known_from_user


    def get_estimated_vocabulary(self, lang):

        filtered_words_known_from_user_dict_list =[]
        enc_probs = EncounterBasedProbability.find_all_by_user(flask.g.user)
        for enc_prob in enc_probs:
            filtered_word_known_from_user_dict = {}
            filtered_word_known_from_user_dict['word'] = enc_prob.word_ranks.word
            filtered_words_known_from_user_dict_list.append(filtered_word_known_from_user_dict.copy())
        return filtered_words_known_from_user_dict_list

    def get_estimated_vocabulary_for_learned_language(self):
        return self.get_estimated_vocabulary(self.learned_language)


    def get_estimated_vocabulary_count(self):
        return len(self.get_estimated_vocabulary_for_learned_language())

    def get_probable_known_words(self):
        high_agg_prob_of_user = AggregatedProbability.get_probable_known_words(flask.g.user)
        probable_known_words_dict_list = []
        for agg_prob in high_agg_prob_of_user:
            probable_known_word_dict = {}
            if agg_prob.word_ranks is not None:
                probable_known_word_dict['word'] = agg_prob.word_ranks.word
            elif agg_prob.user_words is not None:
                probable_known_word_dict['word'] = agg_prob.user_words.word
            probable_known_words_dict_list.append(probable_known_word_dict.copy())
        return probable_known_words_dict_list

    def get_probable_known_words_count(self):
        return len(self.get_probable_known_words())



class Session(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")
    last_use = db.Column(db.DateTime)

    def __init__(self, user, id_):
        self.id = id_
        self.user = user
        self.update_use_date()

    def update_use_date(self):
        self.last_use = datetime.datetime.now()

    @classmethod
    def for_user(cls, user):
        while True:
            id_ = random.randint(0, 1 << 31)
            if cls.query.get(id_) is None:
                break
        return cls(user, id_)


class Language(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = db.Column(db.String(2), primary_key=True)
    name = db.Column(db.String(255), unique=True)

    def __init__(self, id, name):
        self.name = name
        self.id = id

    def __repr__(self):
        return '<Language %r>' % (self.id)

    @classmethod
    def default_learned(cls):
        return cls.find("de")

    @classmethod
    def default_native_language(cls):
        return cls.find("en")

    @classmethod
    def native_languages(cls):
        return [cls.find("en"), cls.find("de"), cls.find("pt"), cls.find("es")]

    @classmethod
    def available_languages(cls):
        return cls.all()

    @classmethod
    def find(cls, id_):
        return cls.query.filter(Language.id == id_).one()

    @classmethod
    def all(cls):
        return cls.query.filter().all()



class WordRank(db.Model, util.JSONSerializable):
    __tablename__ = 'word_ranks'
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(255), nullable =False, unique = True, index = True)

    language_id = db.Column(db.String(2), db.ForeignKey("language.id"))
    language = db.relationship("Language")
    rank = db.Column(db.Integer)
    db.UniqueConstraint(word, language_id)


    def __init__(self, word, language, rank):
        self.word = word
        self.language = language
        self.rank = rank


    @classmethod
    def find(cls, word, language):
        try:
            return (cls.query.filter(cls.word == word)
                             .filter(cls.language == language)
                             .one())
            return w
        except sqlalchemy.orm.exc.NoResultFound:
            return None

    @classmethod
    def find_all(cls,language):
        return cls.query.filter(cls.language == language
        ).all()

    @classmethod
    def exists(cls, word, language):
        try:
            (cls.query.filter(cls.word == word)
                             .filter(cls.language == language)
                             .one())
            return True
        except sqlalchemy.orm.exc.NoResultFound:
            return False


    @classmethod
    def words_list(cls):
        words_list = []
        for word in cls.find_all():
             words_list.append(word.word)
        return words_list

class UserWord(db.Model, util.JSONSerializable):
    __tablename__ = 'user_words'
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(255), nullable =False, unique = True)
    language_id = db.Column(db.String(2), db.ForeignKey("language.id"))
    language = db.relationship("Language")
    rank_id = db.Column(db.Integer, db.ForeignKey("word_ranks.id"), nullable=True)
    rank = db.relationship("WordRank")
    db.UniqueConstraint(word, language_id)

    IMPORTANCE_LEVEL_STEP = 1000
    IMPOSSIBLE_RANK = 1000000
    IMPOSSIBLE_IMPORTANCE_LEVEL = IMPOSSIBLE_RANK / IMPORTANCE_LEVEL_STEP

    def __init__(self, word, language, rank = None):
        self.word = word
        self.language = language
        self.rank = rank

    def __repr__(self):
        return '<UserWord %r>' % (self.word)

    def serialize(self):
        return self.word

    # returns a number between
    def importance_level(self):
        if self.rank is not None:
            return max((10 - self.rank.rank / UserWord.IMPORTANCE_LEVEL_STEP), 0)
        else:
            return  0

    # we use this in the bookmarks.html to show the rank.
    # for words in which there is no rank info, we don't display anything
    def importance_level_string(self):
        if self.rank == None:
            return ""
        b = "|"
        return b * self.importance_level()

    @classmethod
    def find(cls, word, language,rank = None):
        try:
            return (cls.query.filter(cls.word == word)
                             .filter(cls.language == language)
                             .one())
        except sqlalchemy.orm.exc.NoResultFound:
            return cls(word, language,rank)


    @classmethod
    def find_rank(cls, word, language):
        return WordRank.find(word, language)

    @classmethod
    def find_all(cls):
        return cls.query.all()

    @classmethod
    def find_by_language(cls, language):
        return (cls.query.filter(cls.language == language)
                         .all())

    @classmethod
    def exists(cls, word, language):
         try:
            cls.query.filter_by(
                language = language,
                word = word
            ).one()
            return True
         except  sqlalchemy.orm.exc.NoResultFound:
            return False


WordAlias = db.aliased(UserWord, name="translated_word")

class ExerciseBasedProbability(db.Model):

    __tablename__ = 'exercise_based_probability'
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    user = db.relationship("User")
    user_words_id = db.Column(db.Integer, db.ForeignKey('user_words.id'), nullable = False)
    user_words = db.relationship("UserWord")
    probability = db.Column(db.DECIMAL(10,9), nullable = False)
    db.UniqueConstraint(user_id, user_words_id)
    db.CheckConstraint('probability>=0', 'probability<=1')

    DEFAULT_MIN_PROBABILITY = 0.1
    DEFAULT_MAX_PROBABILITY = 1.0

    def __init__(self, user, user_words, probability):
        self.user = user
        self.user_words =user_words
        self.probability = probability

    @classmethod
    def find(cls, user, user_words):
        try:
            return cls.query.filter_by(
                user = user,
                user_words = user_words
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return cls(user, user_words, 0.1)

    @classmethod
    def exists(cls, user, user_words):
        try:
            cls.query.filter_by(
                user = user,
                user_words = user_words
            ).one()
            return True

        except sqlalchemy.orm.exc.NoResultFound:
            return False


    @classmethod
    def find_all(cls):
        return cls.query.all()

    def wrong_formula(self, count_wrong, count_wrong_after_another, weight):
        print 'prob wrong ' + str(self.probability)
        self.probability=(float(self.probability) - (self.DEFAULT_MIN_PROBABILITY * count_wrong)* count_wrong_after_another)** 1/weight
        if self.probability<0.1:
           self.probability = 0.1

    def correct_formula(self, count_correct, count_correct_after_another, weight):
        print 'prob correct ' + str(self.probability)
        self.probability=(float(self.probability) + (self.DEFAULT_MIN_PROBABILITY * count_correct)* count_correct_after_another)** 1/weight
        if self.probability>1.0:
            self.probability = 1.0




    def calculate_bookmark_probability(self,bookmark):
        count_correct_after_another = 0
        count_wrong_after_another = 0
        count_not_know_after_another = 0
        count_correct = 0
        count_wrong = 0
        count_not_know = 0
        weight = 1
        sorted_exercise_log_after_date=sorted(bookmark.exercise_log, key=lambda x: x.time, reverse=False)
        for exercise in sorted_exercise_log_after_date:
            if exercise.outcome.outcome == ExerciseOutcome.IKNOW:
                self.probability = 1.0
                count_wrong = count_wrong/2
            elif exercise.outcome.outcome == ExerciseOutcome.NOT_KNOW:
                if self.probability is not 0.1:
                    self.probability /=2
                if self.probability < 0.1:
                    self.probability = 0.1
                count_correct = count_correct/2
                count_correct_after_another =0
                count_not_know_after_another+=1
                count_not_know +=1
            elif exercise.outcome.outcome == ExerciseOutcome.CORRECT:
                count_correct+=1
                count_correct_after_another +=1
                count_wrong_after_another =0
                count_not_know_after_another = 0
                if self.probability is not 1.0:
                    self.correct_formula(count_correct, count_correct_after_another, weight)

            elif exercise.outcome.outcome == ExerciseOutcome.WRONG:
                 count_wrong+=1
                 count_wrong_after_another += 1
                 count_correct_after_another =0
                 if self.probability is not 0.1:
                    self.wrong_formula(count_wrong, count_wrong_after_another, weight)
            weight +=1

    def halfProbability(self):
        self.probability /=2








class EncounterBasedProbability(db.Model):
    __tablename__ = 'encounter_based_probability'
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    DEFAULT_PROBABILITY = 0.5

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    user = db.relationship("User")
    word_ranks_id = db.Column(db.Integer, db.ForeignKey("word_ranks.id"), nullable=False)
    word_ranks = db.relationship("WordRank")
    count_not_looked_up = db.Column(db.Integer,nullable = False)
    probability = db.Column(db.DECIMAL(10,9), nullable = False)
    db.UniqueConstraint(user_id, word_ranks_id)
    db.CheckConstraint('probability>=0', 'probability<=1')

    def __init__(self, user, word_ranks, count_not_looked_up, probability):
        self.user = user
        self.word_ranks = word_ranks
        self.count_not_looked_up = count_not_looked_up
        self.probability = probability

    @classmethod
    def find(cls, user, word_ranks, default_probability):
         try:
            return cls.query.filter_by(
                user = user,
                word_ranks = word_ranks
            ).one()
         except  sqlalchemy.orm.exc.NoResultFound:
            return cls(user, word_ranks, 1, default_probability)





    @classmethod
    def find_all(cls):
        return cls.query.all()

    @classmethod
    def find_all_by_user(cls, user):
        return cls.query.filter_by(
            user = user
        ).all()

    @classmethod
    def exists(cls, user, word_ranks):
         try:
            cls.query.filter_by(
                user = user,
                word_ranks = word_ranks
            ).one()
            return True
         except  sqlalchemy.orm.exc.NoResultFound:
            return False

    def reset_prob (self):
        self.probability = 0.5



class AggregatedProbability(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}
    __tablename__ = 'aggregated_probability'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    user = db.relationship("User")
    user_words_id = db.Column(db.Integer, db.ForeignKey('user_words.id'), nullable = True)
    user_words = db.relationship("UserWord")
    word_ranks_id = db.Column(db.Integer, db.ForeignKey("word_ranks.id"), nullable=True)
    word_ranks = db.relationship("WordRank")
    probability = db.Column(db.DECIMAL(10,9), nullable = False)
    db.CheckConstraint('probability>=0', 'probability<=1')

    def __init__(self, user, user_words, word_ranks,probability):
        self.user = user
        self.user_words = user_words
        self.word_ranks = word_ranks
        self.probability = probability

    @classmethod
    def calculateAggregatedProb(cls,exerciseProb, encounterProb):
        return 0.6 * float(exerciseProb) + 0.4 * float(encounterProb)

    @classmethod
    def find(cls, user, user_words, word_ranks, probability=None):
        try:
            return cls.query.filter_by(
                user = user,
                user_words = user_words,
                word_ranks = word_ranks
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return cls(user, user_words, word_ranks, probability)

    @classmethod
    def exists(cls, user, user_words, word_ranks):
        try:
            cls.query.filter_by(
                user = user,
                user_words = user_words,
                word_ranks = word_ranks
            ).one()
            return True
        except sqlalchemy.orm.exc.NoResultFound:
            return False

    @classmethod
    def get_probable_known_words(cls, user):
        return cls.query.filter(
            cls.user == user).filter(cls.probability >=0.9).all()


class Url(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2083))
    title = db.Column(db.String(2083))

    def __init__(self, url, title):
        self.url= url
        self.title = title

    def title_if_available(self):
        if self.title != "":
            return self.title
        return self.url

    @classmethod
    def find(cls, url, title):
        try:
            return (cls.query.filter(cls.url == url)
                             .one())
        except sqlalchemy.orm.exc.NoResultFound:
            return cls(url, title)

    def render_link(self, link_text):
        if self.url != "":
            return '<a href="'+self.url+'">'+link_text+'</a>'
        else:
            return ""



class Bookmark(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = db.Column(db.Integer, primary_key=True)
    origin_id = db.Column(db.Integer, db.ForeignKey('user_words.id'))
    origin = db.relationship("UserWord", primaryjoin=origin_id == UserWord.id,
                             backref="translations")
    translations_list = relationship("UserWord", secondary="bookmark_translation_mapping")

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship("User", backref="bookmarks")

    text_id = db.Column(db.Integer, db.ForeignKey('text.id'))
    text = db.relationship("Text", backref="bookmarks")

    time = db.Column(db.DateTime)

    exercise_log = relationship("Exercise", secondary="bookmark_exercise_mapping")

    def __init__(self, origin, translation, user, text, time):
        self.origin = origin
        self.translations_list.append(translation)
        self.user = user
        self.time = time
        self.text = text

    def add_new_exercise(self, exercise):
        self.exercise_log.append(exercise)

    def translation(self):
        return self.translations_list[0]

    def translations_rendered_as_text(self):
        return ", ".join(self.translation_words_list())

    def translation_words_list(self):
        translation_words=[]
        for translation in self.translations_list:
            translation_words.append(translation.word)
        return translation_words

    def add_new_translation(self, translation):
        self.translations_list.append(translation)

    def remove_translation(self,translation):
        if translation in self.translations_list:
            self.translations_list.remove(translation)

    def add_exercise_outcome(self, exercise_source, exercise_outcome, exercise_solving_speed):
        new_source = ExerciseSource.query.filter_by(
        source = exercise_source
    ).first()
        new_outcome=ExerciseOutcome.query.filter_by(
        outcome=exercise_outcome
    ).first()
        exercise = Exercise(new_outcome,new_source,exercise_solving_speed,datetime.datetime.now())
        self.add_new_exercise(exercise)
        db.session.add(exercise)


    @classmethod
    def find_by_specific_user(cls, user):
        return cls.query.filter_by(
            user= user
        ).all()
    @classmethod
    def find_all_filtered_by_user(cls):
        return cls.query.filter_by(
            user= flask.g.user
        ).all()

    @classmethod
    def find_all(cls):
        return cls.query.filter().all()

    @classmethod
    def find(cls, b_id):
        return cls.query.filter_by(
            id= b_id
        ).first()

    @classmethod
    def find_all_by_user_and_word(cls, user, word):
        return cls.query.filter_by(
            user = user,
            origin = word
        ).all()



    # @classmethod
    # def is_sorted_exercise_log_after_date_outcome(cls,outcome, bookmark):
    #     sorted_exercise_log_after_date=sorted(bookmark.exercise_log, key=lambda x: x.time, reverse=True)
    #     if sorted_exercise_log_after_date:
    #         if sorted_exercise_log_after_date[0].outcome.outcome == outcome:
    #             return True
    #     return False

    @classmethod
    def is_sorted_exercise_log_after_date_outcome(cls,outcome, bookmark):
        sorted_exercise_log_after_date=sorted(bookmark.exercise_log, key=lambda x: x.time, reverse=True)
        for exercise in sorted_exercise_log_after_date:
            if exercise.outcome.outcome == outcome:
                return True
            elif exercise.outcome.outcome == 'Do not know' or exercise.outcome.outcome == 'Wrong':
                return False
        return False




bookmark_translation_mapping = Table('bookmark_translation_mapping', db.Model.metadata,
    Column('bookmark_id', Integer, ForeignKey('bookmark.id')),
    Column('translation_id', Integer, ForeignKey('user_words.id'))
)



class Exercise(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}
    __tablename__ = 'exercise'

    id = db.Column(db.Integer, primary_key=True)
    outcome_id=db.Column(db.Integer,db.ForeignKey('exercise_outcome.id'),nullable=False)
    outcome = db.relationship ("ExerciseOutcome", backref="exercise")
    source_id=db.Column(db.Integer,db.ForeignKey('exercise_source.id'), nullable=False)
    source = db.relationship ("ExerciseSource", backref="exercise")
    solving_speed=db.Column(db.Integer)
    time=db.Column(db.DateTime, nullable=False)

    def __init__(self,outcome,source,solving_speed,time):
        self.outcome = outcome
        self.source = source
        self.solving_speed = solving_speed
        self.time = time


class ExerciseOutcome(db.Model):
    __tablename__ = 'exercise_outcome'
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = db.Column(db.Integer, primary_key=True)
    outcome=db.Column(db.String(255),nullable=False)

    IKNOW = 'I know'
    NOT_KNOW = 'Do not know'
    CORRECT = 'Correct'
    WRONG = 'Wrong'

    def __init__(self,outcome):
        self.outcome = outcome


    @classmethod
    def find(cls, outcome):
        try:
            return cls.query.filter_by(
                outcome = outcome
            ).one()
        except  sqlalchemy.orm.exc.NoResultFound:
            return cls(outcome)




class ExerciseSource(db.Model):
    __tablename__ = 'exercise_source'
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = db.Column(db.Integer, primary_key=True)
    source=db.Column(db.String(255), nullable=False)

    def __init__(self,source):
        self.source = source


bookmark_exercise_mapping = Table('bookmark_exercise_mapping', db.Model.metadata,
    Column('bookmark_id', Integer, ForeignKey('bookmark.id')),
    Column('exercise_id', Integer, ForeignKey('exercise.id'))
)




class Text(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(10000))

    content_hash = db.Column(db.LargeBinary(32))
    language_id = db.Column(db.String(2), db.ForeignKey("language.id"))
    language = db.relationship("Language")

    url_id = db.Column(db.Integer, db.ForeignKey('url.id'))
    url = db.relationship("Url", backref="texts")


    def __init__(self, content, language, url):
        self.content = content
        self.language = language
        self.url = url
        self.content_hash = util.text_hash(content)

    def __repr__(self):
        return '<Text %r>' % (self.language.short)

    def words(self):
        for word in re.split(re.compile(u"[^\\w]+", re.U), self.content):
            yield UserWord.find(word, self.language)


    def shorten_word_context(self, given_word, max_word_count):
        # shorter_text = ""
        limited_words=[]

        words = self.content.split() # ==> gives me a list of the words ["these", "types", ",", "the"]
        word_count = len(words)

        if word_count <= max_word_count:
            return self.content

        for i in range(0, max_word_count):
            limited_words.append(words[i]) # lista cu primele max_length cuvinte
        shorter_text = ' '.join(limited_words) # string cu primele 'max_word_count' cuv

        # sometimes the given_word does not exist in the text.
        # in that case return a text containing max_length words
        if given_word not in words:
            return shorter_text

        if words.index(given_word) <= max_word_count:
            return shorter_text

        for i in range(max_word_count + 1,  words.index(given_word) + 1):
            limited_words.append(words[i])
        shorter_text = ' '.join(limited_words)

        return shorter_text

    @classmethod
    def find(cls, text, language):
        try:
            query = (
                cls.query.filter(cls.language == language)
                         .filter(cls.content_hash == util.text_hash(text))
            )
            if query.count() > 0:
                query = query.filter(cls.content == text)
                try:
                    return query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    pass
            return cls(text, language)
        except:
            import traceback
            traceback.print_exc()


class Search(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref="searches")
    word_id = db.Column(db.Integer, db.ForeignKey("user_words.id"))
    word = db.relationship("UserWord")
    language_id = db.Column(db.String(2), db.ForeignKey("language.id"))
    language = db.relationship("Language")
    text_id = db.Column(db.Integer, db.ForeignKey("text.id"))
    text = db.relationship("Text")
    bookmark_id = db.Column(db.Integer, db.ForeignKey("bookmark.id"))
    bookmark = db.relationship("Bookmark", backref="search")

    def __init__(self, user, word, language, text=None):
        self.user = user
        self.user_word = word
        self.language = language
        self.text = text

    def __repr__(self):
        return '<Search %r>' % (self.user_word.word)

