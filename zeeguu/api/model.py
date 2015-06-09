# -*- coding: utf8 -*-
import re
import random
import datetime
import codecs
import flask
from sqlalchemy import Column, Table, ForeignKey, Integer

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
        return [cls.find("en")]

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
    def exists(cls, word, language_id):
        try:
            (cls.query.filter(cls.word == word)
                             .filter(cls.language == language_id)
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


WordAlias = db.aliased(UserWord, name="translated_word")

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
    def find_all_filtered_by_user(cls):
        return cls.query.filter_by(
            user= flask.g.user
        ).all()

    @classmethod
    def find(cls, b_id):
        return cls.query.filter_by(
            id= b_id
        ).first()



    @classmethod
    def is_sorted_exercise_log_after_date_outcome(cls,outcome, bookmark):
        sorted_exercise_log_after_date=sorted(bookmark.exercise_log, key=lambda x: x.time, reverse=True)
        if sorted_exercise_log_after_date:
            if sorted_exercise_log_after_date[0].outcome.outcome == outcome:
                return True
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

    def __init__(self,outcome):
        self.outcome = outcome


    @classmethod
    def find(cls, outcome):
        try:
            return cls.query.filter_by(
                outcome = outcome
            ).first()
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

