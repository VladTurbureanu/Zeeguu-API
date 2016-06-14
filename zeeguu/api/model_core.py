# -*- coding: utf8 -*-


from zeeguu import db


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


