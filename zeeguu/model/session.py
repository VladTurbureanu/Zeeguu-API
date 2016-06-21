import random
import datetime
from zeeguu import db


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

    @classmethod
    def find_for_id(cls, session_id):
        try:
            return cls.query.filter(cls.id == session_id).one()
        except:
            return None

    @classmethod
    def find_for_user(cls, user):
        return cls.query.filter(cls.user == user).first()