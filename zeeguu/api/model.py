# -*- coding: utf8 -*-
import re
import random
import datetime

import sqlalchemy.orm.exc
import sys

from zeeguu import db
from zeeguu import util
import zeeguu


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    password = db.Column(db.LargeBinary(255))
    password_salt = db.Column(db.LargeBinary(255))
    preferred_language_id = db.Column(
        db.String(2),
        db.ForeignKey("language.id")
    )
    preferred_language = sqlalchemy.orm.relationship("Language")

    def __init__(self, email, name, password, preferred_language=None):
        self.email = email
        self.name = name
        self.update_password(password)
        self.preferred_language = preferred_language or Language.default()

    def __repr__(self):
        return '<User %r>' % (self.email)

    def read(self, text):
        if (Impression.query.filter(Impression.user == self)
                            .filter(Impression.text == text).count()) > 0:
            return
        for word in text.words():
            self.impressions.append(Impression(self, word, text))

    @classmethod
    def find(cls, email):
        return User.query.filter(User.email == email).one()

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
	
    def contribs_chronologically(self):
	    return Contribution.query.filter_by(user_id=self.id).order_by(Contribution.time.desc()).all()

    def all_contributions(self):
        return Contribution.query.filter_by(user_id=self.id).order_by(Contribution.time.desc()).all()

    def contribs_by_date(self):
	def extract_day_from_date(contrib):
		return (contrib, contrib.time.replace(contrib.time.year, contrib.time.month, contrib.time.day,0,0,0,0))

	contribs = self.all_contributions()
	contribs_by_date = dict()
				                                        
	for elem in map(extract_day_from_date, contribs):
		contribs_by_date.setdefault(elem[1],[]).append(elem[0])

	sorted_dates = contribs_by_date.keys()
	sorted_dates.sort(reverse=True)
	return contribs_by_date, sorted_dates

    def unique_urls(self):
        urls = set()
        for c in self.all_contributions():
            urls.add(c.text.url)
        return urls

    def recommended_urls(self):
        urls_to_words = {}
        for contrib in self.all_contributions():
            if contrib.text.url.url != "undefined":
                urls_to_words.setdefault(contrib.text.url,0)
                urls_to_words [contrib.text.url] += contrib.origin.importance_level()
        return sorted(urls_to_words, key=urls_to_words.get, reverse=True)



class Session(db.Model):
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
    id = db.Column(db.String(2), primary_key=True)
    name = db.Column(db.String(255), unique=True)

    def __init__(self, id, name):
        self.name = name
        self.id = id

    def __repr__(self):
        return '<Language %r>' % (self.id)

    @classmethod
    def default(cls):
        return cls.find("de")

    @classmethod
    def find(cls, id_):
        return cls.query.filter(Language.id == id_).one()


class Word(db.Model, util.JSONSerializable):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(255))
    language_id = db.Column(db.String(2), db.ForeignKey("language.id"))
    language = db.relationship("Language")
    word_rank = db.Column(db.Integer)
    starred = db.Column(db.BOOLEAN)

    IMPORTANCE_LEVEL_STEP = 1000
    IMPOSSIBLE_RANK = 1000000
    IMPOSSIBLE_IMPORTANCE_LEVEL = IMPOSSIBLE_RANK / IMPORTANCE_LEVEL_STEP

    def __init__(self, word, language, starred):
        self.word = word
        self.language = language
        self.word_rank = self.get_rank_from_file()
        self.starred = starred

    def __repr__(self):
        return '<Word %r>' % (self.word)

    def serialize(self):
        return self.word

    # if the word is not found, we assume a rank of 1000000
    def get_rank_from_file(self):
        import codecs
        try:
            f=codecs.open(zeeguu.app.config.get("LANGUAGES_FOLDER").decode('utf-8')+self.language.id+".txt", encoding="iso-8859-1")

            all_words = f.readlines()
            all_words_without_space = []
            for each_word in all_words:
                each_word_without_space = each_word[:-1]
                all_words_without_space.append(each_word_without_space)

            def importance_range(the_word, frequency_list):
                if the_word in frequency_list:
                    position = frequency_list.index(the_word)
                    return position
                else:
                    return Word.IMPOSSIBLE_RANK
            return importance_range(self.word, all_words_without_space)
        except:
            return Word.IMPOSSIBLE_RANK

    def rank(self):
        if self.word_rank == None:
            self.word_rank = self.get_rank_from_file()
            session = sqlalchemy.orm.object_session(self)
            session.commit()
        return self.word_rank

    # returns a number between
    def importance_level(self):
        return 10 - self.rank() / Word.IMPORTANCE_LEVEL_STEP

    # we use this in the contributions.html to show the rank.
    # for words in which there is no rank info, we don't display anything
    def importance_level_string(self):
        if self.rank() == Word.IMPOSSIBLE_RANK:
            return "|||"
        b = "|"
        return b * self.importance_level()

    @classmethod
    def find(cls, word, language):
        try:
            return (cls.query.filter(cls.word == word)
                             .filter(cls.language == language)
                             .one())
        except sqlalchemy.orm.exc.NoResultFound:
            return cls(word, language, False)

    @classmethod
    def translate(cls, from_lang, term, to_lang):
        return (cls.query.join(WordAlias, cls.translation_of)
                         .filter(WordAlias.word == term.lower())
                         .filter(cls.language == to_lang)
                         .filter(WordAlias.language == from_lang)
                         .all())


WordAlias = db.aliased(Word, name="translated_word")

class Url(db.Model):
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

class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    origin_id = db.Column(db.Integer, db.ForeignKey('word.id'))
    origin = db.relationship("Word", primaryjoin=origin_id == Word.id,
                             backref="translations")
    translation_id = db.Column(db.Integer, db.ForeignKey('word.id'))
    translation = db.relationship("Word",
                                  primaryjoin=translation_id == Word.id)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship("User", backref="contributions")

    text_id = db.Column(db.Integer, db.ForeignKey('text.id'))
    text = db.relationship("Text", backref="contributions")

    time = db.Column(db.DateTime)

    # def __init__(self, origin, translation, user):
    #     self.origin = origin
    #     self.translation = translation
    #     self.user = user
    #     self.time = datetime.datetime.now()
    #
    # def __init__(self, origin, translation, user, time):
    #     self.origin = origin
    #     self.translation = translation
    #     self.user = user
    #     self.time = time

    def __init__(self, origin, translation, user, text, time):
        self.origin = origin
        self.translation = translation
        self.user = user
        self.time = time
        self.text = text


class Text(db.Model):
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
            yield Word.find(word, self.language)


    def shorten_word_context(self, given_word, max_word_count):
        # shorter_text = ""
        limited_words=[]

        words = self.content.split() # ==> gives me a list of the words ["these", "types", ",", "the"]
        word_count = len(words)

        if word_count <= max_word_count:
            return self.content.capitalize()

        for i in range(0, max_word_count):
            limited_words.append(words[i]) # lista cu primele max_length cuvinte
        shorter_text = ' '.join(limited_words) # string cu primele 'max_word_count' cuv

        # sometimes the given_word does not exist in the text.
        # in that case return a text containing max_length words
        if given_word not in words:
            return shorter_text.capitalize()

        if words.index(given_word) <= max_word_count:
            return shorter_text.capitalize()

        for i in range(max_word_count + 1,  words.index(given_word) + 1):
            limited_words.append(words[i])
        shorter_text = ' '.join(limited_words)

        return shorter_text.capitalize()

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
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref="searches")
    word_id = db.Column(db.Integer, db.ForeignKey("word.id"))
    word = db.relationship("Word")
    language_id = db.Column(db.String(2), db.ForeignKey("language.id"))
    language = db.relationship("Language")
    text_id = db.Column(db.Integer, db.ForeignKey("text.id"))
    text = db.relationship("Text")
    contribution_id = db.Column(db.Integer, db.ForeignKey("contribution.id"))
    contribution = db.relationship("Contribution", backref="search")

    def __init__(self, user, word, language, text=None):
        self.user = user
        self.word = word
        self.language = language
        self.text = text

    def __repr__(self):
        return '<Search %r>' % (self.word.word)


class Impression(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref="impressions")
    word_id = db.Column(db.Integer, db.ForeignKey("word.id"))
    word = db.relationship("Word")
    text_id = db.Column(db.Integer, db.ForeignKey("text.id"))
    text = db.relationship("Text")
    count = db.Column(db.Integer)
    last_search_id = db.Column(db.Integer, db.ForeignKey("search.id"))
    last_search = db.relationship("Search")

    def __init__(self, user, word, text=None):
        self.user = user
        self.word = word
        self.text = text

    def __repr__(self):
        return '<Impression %r>' % (self.word.word)
