# -*- coding: utf8 -*-
import re
import random
import datetime
import string
import decimal
import flask
from sqlalchemy import Column, Table, ForeignKey, Integer, DECIMAL
from re import compile as _Re

import sqlalchemy.orm.exc

from zeeguu import db
from zeeguu import util
import zeeguu
from sqlalchemy.orm import relationship
red_words_association_table = Table('starred_words_association', db.Model.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('starred_word_id', Integer, ForeignKey('user_word.id'))
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

    def user_word(self):
        return map((lambda x: x.origin.word), self.all_bookmarks())

    def all_bookmarks(self):
        return Bookmark.query.filter_by(user_id=self.id).order_by(Bookmark.time.desc()).all()

    def bookmark_count(self):
        return len(self.all_bookmarks())

    def word_count(self):
        return len(self.user_word())

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

    def get_known_bookmarks(self,lang):
        bookmarks = Bookmark.find_all_filtered_by_user()
        known_bookmarks=[]
        for bookmark in bookmarks:
            if Bookmark.sort_exercise_log_by_latest_and_check_is_latest_outcome_too_easy(ExerciseOutcome.TOO_EASY, bookmark) and lang ==bookmark.origin.language:
                    known_bookmark_dict = {}
                    known_bookmark_dict['id'] = bookmark.id
                    known_bookmark_dict['origin'] = bookmark.origin.word
                    known_bookmark_dict['text']= bookmark.text.content
                    known_bookmark_dict['time']=bookmark.time.strftime('%m/%d/%Y')
                    known_bookmarks.append(known_bookmark_dict.copy())
        return known_bookmarks

    def get_known_bookmarks_count(self):
        return len(self.get_known_bookmarks(self.learned_language))


    def get_not_looked_up_words(self, lang):

        filtered_words_known_from_user_dict_list =[]
        enc_probs = EncounterBasedProbability.find_all_by_user(flask.g.user)
        for enc_prob in enc_probs:
            if enc_prob.word_rank.language == lang:
                filtered_word_known_from_user_dict = {}
                filtered_word_known_from_user_dict['word'] = enc_prob.word_rank.word
                filtered_words_known_from_user_dict_list.append(filtered_word_known_from_user_dict.copy())
        return filtered_words_known_from_user_dict_list

    def get_not_looked_up_words_for_learned_language(self):
        return self.get_not_looked_up_words(self.learned_language)


    def get_not_looked_up_words_count(self):
        return len(self.get_not_looked_up_words_for_learned_language())

    def get_probably_known_words(self, lang):
        high_agg_prob_of_user = AggregatedProbability.get_probably_known_words(flask.g.user)
        probable_known_words_dict_list = []
        for agg_prob in high_agg_prob_of_user:
            probable_known_word_dict = {}
            if agg_prob.word_rank is not None and agg_prob.word_rank.language == lang:
                probable_known_word_dict['word'] = agg_prob.word_rank.word
            elif agg_prob.user_word is not None and agg_prob.user_word.language == lang:
                probable_known_word_dict['word'] = agg_prob.user_word.word
            probable_known_words_dict_list.append(probable_known_word_dict.copy())
        return probable_known_words_dict_list

    def get_probably_known_words_count(self):
        return len(self.get_probably_known_words(self.learned_language))

    def get_percentage_of_language_known(self):
        high_agg_prob_of_user = AggregatedProbability.get_probably_known_words(self)
        count_high_agg_prob_of_user_ranked = 0
        for prob in high_agg_prob_of_user:
            if prob.word_rank is not None and prob.word_rank.rank <=3000:
                count_high_agg_prob_of_user_ranked +=1
        return round(float(count_high_agg_prob_of_user_ranked)/3000*100,2)

    def get_percentage_of_known_bookmarked_words(self):
        high_agg_prob_of_user = AggregatedProbability.get_probably_known_words(self)
        find_all_agg_prob_of_user = AggregatedProbability.find_all_by_user(self)
        count_user_word_of_user = 0
        count_high_agg_prob_of_user =0
        for prob in find_all_agg_prob_of_user:
            if prob.user_word is not None:
                count_user_word_of_user+=1
        for prob in high_agg_prob_of_user:
            if prob.user_word is not None:
                count_high_agg_prob_of_user +=1
        if count_user_word_of_user <> 0:
            return round(float(count_high_agg_prob_of_user)/count_user_word_of_user*100,2)
        else:
            return 0










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
    __tablename__ = 'word_rank'
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
        word = word.lower()
        try:
            return (cls.query.filter(cls.word == word)
                             .filter(cls.language == language)
                             .one())
        except sqlalchemy.orm.exc.NoResultFound:
            return None

    @classmethod
    def find_all(cls,language):
        return cls.query.filter(cls.language == language
        ).all()

    @classmethod
    def exists(cls, word, language):
        word = word.lower()
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
    __tablename__ = 'user_word'
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(255), nullable =False, unique = True)
    language_id = db.Column(db.String(2), db.ForeignKey("language.id"))
    language = db.relationship("Language")
    rank_id = db.Column(db.Integer, db.ForeignKey("word_rank.id"), nullable=True)
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
    def find(cls, word, language):
        try:
            return (cls.query.filter(cls.word == word)
                             .filter(cls.language == language)
                             .one())
        except sqlalchemy.orm.exc.NoResultFound:
            rank = UserWord.find_rank(word.lower(),language)
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
    user_word_id = db.Column(db.Integer, db.ForeignKey('user_word.id'), nullable = False)
    user_word = db.relationship("UserWord")
    probability = db.Column(db.DECIMAL(10,9), nullable = False)
    db.UniqueConstraint(user_id, user_word_id)
    db.CheckConstraint('probability>=0', 'probability<=1')

    DEFAULT_MIN_PROBABILITY = 0.1
    DEFAULT_MAX_PROBABILITY = 1.0

    def __init__(self, user, user_word, probability):
        self.user = user
        self.user_word =user_word
        self.probability = probability

    @classmethod
    def find(cls, user, user_word):
        try:
            return cls.query.filter_by(
                user = user,
                user_word = user_word
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return cls(user, user_word, 0.1)

    @classmethod
    def exists(cls, user, user_word):
        try:
            cls.query.filter_by(
                user = user,
                user_word = user_word
            ).one()
            return True

        except sqlalchemy.orm.exc.NoResultFound:
            return False


    @classmethod
    def find_all(cls):
        return cls.query.all()

    def wrong_formula(self, count_wrong_after_another):
        if self.DEFAULT_MIN_PROBABILITY * count_wrong_after_another >= float(self.probability):
           self.probability = decimal.Decimal('0.1')
        else:
            self.probability=(float(self.probability) - self.DEFAULT_MIN_PROBABILITY * count_wrong_after_another)

    def correct_formula(self, count_correct_after_another):
        if  float(self.probability) +  self.DEFAULT_MIN_PROBABILITY * count_correct_after_another >= 1.0 :
           self.probability = decimal.Decimal('1.0')
        else:
             self.probability=(float(self.probability) + self.DEFAULT_MIN_PROBABILITY * count_correct_after_another)






    def know_bookmark_probability(self,bookmark):
        count_correct_after_another = 0
        count_wrong_after_another = 0
        sorted_exercise_log_after_date=sorted(bookmark.exercise_log, key=lambda x: x.time, reverse=False)
        for exercise in sorted_exercise_log_after_date:
            if exercise.outcome.outcome == ExerciseOutcome.TOO_EASY:
                self.probability = decimal.Decimal('1.0')
                count_wrong_after_another =0
            elif exercise.outcome.outcome == ExerciseOutcome.SHOW_SOLUTION:
                self.probability //=2
                if float(self.probability) < 0.1:
                    self.probability = decimal.Decimal('0.1')
                count_correct_after_another =0
            elif exercise.outcome.outcome == ExerciseOutcome.CORRECT:
                count_correct_after_another +=1
                count_wrong_after_another = 0
                if float(self.probability) < 1.0:
                    self.correct_formula(count_correct_after_another)
                else: self.probability = decimal.Decimal('1.0')
            elif exercise.outcome.outcome == ExerciseOutcome.WRONG:
                 count_wrong_after_another += 1
                 count_correct_after_another = 0
                 if float(self.probability) > 0.1:
                    self.wrong_formula(count_wrong_after_another)
                 else: self.probability = decimal.Decimal('0.1')

    def halfProbability(self):
        self.probability /=2
        if float(self.probability)<0.1:
            self.probability = decimal.Decimal('0.1')








class EncounterBasedProbability(db.Model):
    __tablename__ = 'encounter_based_probability'
    __table_args__ = {'mysql_collate': 'utf8_bin'}

    DEFAULT_PROBABILITY = 0.5

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    user = db.relationship("User")
    word_rank_id = db.Column(db.Integer, db.ForeignKey("word_rank.id"), nullable=False)
    word_rank = db.relationship("WordRank")
    count_not_looked_up = db.Column(db.Integer,nullable = False)
    probability = db.Column(db.DECIMAL(10,9), nullable = False)
    db.UniqueConstraint(user_id, word_rank_id)
    db.CheckConstraint('probability>=0', 'probability<=1')

    def __init__(self, user, word_rank, count_not_looked_up, probability):
        self.user = user
        self.word_rank = word_rank
        self.count_not_looked_up = count_not_looked_up
        self.probability = probability

    @classmethod
    def find(cls, user, word_rank, default_probability=None):
         try:
            return cls.query.filter_by(
                user = user,
                word_rank = word_rank
            ).one()
         except  sqlalchemy.orm.exc.NoResultFound:
            return cls(user, word_rank, 1, default_probability)





    @classmethod
    def find_all(cls):
        return cls.query.all()

    @classmethod
    def find_all_by_user(cls, user):
        return cls.query.filter_by(
            user = user
        ).all()

    @classmethod
    def exists(cls, user, word_rank):
         try:
            cls.query.filter_by(
                user = user,
                word_rank = word_rank
            ).one()
            return True
         except  sqlalchemy.orm.exc.NoResultFound:
            return False

    @classmethod
    def find_or_create(cls, word, user):
        word_rank = WordRank.find(word, user.learned_language)
        if EncounterBasedProbability.exists(user, word_rank):
            enc_prob = EncounterBasedProbability.find(user,word_rank)
            enc_prob.count_not_looked_up +=1
            enc_prob.boost_prob()
        else:
            enc_prob = EncounterBasedProbability.find(user,word_rank, EncounterBasedProbability.DEFAULT_PROBABILITY)
        return enc_prob


    def reset_prob (self):
        self.probability = 0.5

#         This function controls if prob is already 1.0, else it adds 0.1. It maximum adds 0.1, therefore cannot exceed 1
    def boost_prob(self):
        if float(self.probability) <> 1.0:
            self.probability = float(self.probability) + 0.1






class AggregatedProbability(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}
    __tablename__ = 'aggregated_probability'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    user = db.relationship("User")
    user_word_id = db.Column(db.Integer, db.ForeignKey('user_word.id'), nullable = True)
    user_word = db.relationship("UserWord")
    word_rank_id = db.Column(db.Integer, db.ForeignKey("word_rank.id"), nullable=True)
    word_rank = db.relationship("WordRank")
    probability = db.Column(db.DECIMAL(10,9), nullable = False)
    db.CheckConstraint('probability>=0', 'probability<=1')

    def __init__(self, user, user_word, word_rank,probability):
        self.user = user
        self.user_word = user_word
        self.word_rank = word_rank
        self.probability = probability

    @classmethod
    def calculateAggregatedProb(cls,exerciseProb, encounterProb):
        return 0.6 * float(exerciseProb) + 0.4 * float(encounterProb)

    @classmethod
    def find(cls, user, user_word, word_rank, probability=None):
        try:
            return cls.query.filter_by(
                user = user,
                user_word = user_word,
                word_rank = word_rank
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return cls(user, user_word, word_rank, probability)

    @classmethod
    def find_all_by_user(cls,user):
        return cls.query.filter_by(
            user = user
        ).all()

    @classmethod
    def exists(cls, user, user_word, word_rank):
        try:
            cls.query.filter_by(
                user = user,
                user_word = user_word,
                word_rank = word_rank
            ).one()
            return True
        except sqlalchemy.orm.exc.NoResultFound:
            return False

    @classmethod
    def get_probably_known_words(cls, user):
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
    origin_id = db.Column(db.Integer, db.ForeignKey('user_word.id'))
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

    def split_words_from_context(self):
        words_of_bookmark_content = []
        # bookmark_content_words = re.sub("[^\w]", " ",  self.text.content).split()
        # bookmark_content_words = re.compile(r'[%s\s]+' % re.escape(string.punctuation)).split(self.text.content)
        bookmark_content_words = re.findall(r'(?u)\w+', self.text.content)
        words_of_bookmark_content.extend(bookmark_content_words)
        return words_of_bookmark_content



    def context_words_with_rank(self):
        ranked_context_words = self.split_words_from_context()
        while self.origin.word in ranked_context_words: ranked_context_words.remove(self.origin.word)
        filtered_words_known_from_user = []
        for word_known in ranked_context_words:
            if WordRank.exists(word_known.lower(), self.origin.language):
                filtered_words_known_from_user.append(word_known)
        return filtered_words_known_from_user

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
    def sort_exercise_log_by_latest_and_check_is_latest_outcome_too_easy(cls,outcome, bookmark):
        sorted_exercise_log_by_latest=sorted(bookmark.exercise_log, key=lambda x: x.time, reverse=True)
        for exercise in sorted_exercise_log_by_latest:
            if exercise.outcome.outcome == outcome:
                return True
            elif exercise.outcome.outcome == ExerciseOutcome.SHOW_SOLUTION or exercise.outcome.outcome == ExerciseOutcome.WRONG:
                return False
        return False




bookmark_translation_mapping = Table('bookmark_translation_mapping', db.Model.metadata,
    Column('bookmark_id', Integer, ForeignKey('bookmark.id')),
    Column('translation_id', Integer, ForeignKey('user_word.id'))
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

    TOO_EASY = 'Too easy'
    SHOW_SOLUTION = 'Show solution'
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
    word_id = db.Column(db.Integer, db.ForeignKey("user_word.id"))
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

