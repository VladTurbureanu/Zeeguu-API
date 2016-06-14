# -*- coding: utf8 -*-
import random

import datetime
from sqlalchemy import Column, Table, ForeignKey, Integer

from zeeguu import db
from zeeguu.model.user_word import UserWord

starred_words_association_table = Table('starred_words_association', db.Model.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('starred_word_id', Integer, ForeignKey('user_word.id'))
)


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


WordAlias = db.aliased(UserWord, name="translated_word")


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


