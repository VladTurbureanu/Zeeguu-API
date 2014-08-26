# -*- coding: utf8 -*-
import datetime

from zeeguu import db


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer)
    contribution_id = db.Column(db.Integer, db.ForeignKey('contribution.id'))
    contribution = db.relationship("Contribution", backref="card")
    last_seen = db.Column(db.DateTime)

    def __init__(self, contribution):
        self.contribution = contribution
        self.position = 0
        self.reason = ""
        self.seen()

    def seen(self):
        self.last_seen = datetime.datetime.now()

    def set_reason(self, reason):
        self.reason = reason

    def reason(self):
        return self.reason

    def is_starred(self):
        return self.contribution.user.has_starred(self.contribution.origin)

    def star(self):
        word = self.contribution.origin
        self.contribution.user.starred_words.append(word)
        print "starred the hell out of... " + self.contribution.origin.word

    def unstar(self):
        word = self.contribution.origin
        self.contribution.user.starred_words.remove(word)
        print "just unstarred ..." + self.contribution.origin.word


