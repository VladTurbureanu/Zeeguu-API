import sqlalchemy.orm

from zeeguu import db
from zeeguu.model.user import User


class KnownWordProbability(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}
    __tablename__ = 'known_word_probability'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    user = db.relationship("User")
    user_word_id = db.Column(db.Integer, db.ForeignKey('user_word.id'), nullable = True)
    user_word = db.relationship("UserWord")
    ranked_word_id = db.Column(db.Integer, db.ForeignKey("ranked_word.id"), nullable=True)
    ranked_word = db.relationship("RankedWord")
    probability = db.Column(db.DECIMAL(10,9), nullable = False)
    db.CheckConstraint('probability>=0', 'probability<=1')

    def __init__(self, user, user_word, ranked_word,probability):
        self.user = user
        self.user_word = user_word
        self.ranked_word = ranked_word
        self.probability = probability

    def word_has_just_beek_bookmarked(self):
        self.probability /= 2

    @classmethod
    def calculateKnownWordProb(cls,exerciseProb, encounterProb):
        return 0.8 * float(exerciseProb) + 0.2 * float(encounterProb)

    @classmethod
    def find(cls, user, user_word, ranked_word, probability=None):
        try:
            return cls.query.filter_by(
                user = user,
                user_word = user_word,
                ranked_word = ranked_word
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return cls(user, user_word, ranked_word, probability)

    @classmethod
    def find_all_by_user(cls, user):
        return cls.query.filter_by(
            user = user
        ).all()

    @classmethod
    def find_all_by_user_cached(cls, user):
        known_probabilities_cache = {}
        known_probabilities = cls.find_all_by_user(user)
        for known_probability in known_probabilities:
            user_word = known_probability.user_word
            # TODO: Why are there many KnownWordProbabilities with no user word in the database?
            if user_word is not None:
                known_probabilities_cache[user_word.word] = known_probability.probability
        return known_probabilities_cache

    @classmethod
    def find_all_by_user_with_rank(cls, user):
        known_probs = cls.query.filter_by(
            user = user
        ).all()
        for p in known_probs:
            if p.ranked_word is None:
                known_probs.remove(p)
        return known_probs

    @classmethod
    def exists(cls, user, user_word, ranked_word):
        try:
            cls.query.filter_by(
                user = user,
                user_word = user_word,
                ranked_word = ranked_word
            ).one()
            return True
        except sqlalchemy.orm.exc.NoResultFound:
            return False

    @classmethod
    def get_probably_known_words(cls, user):
        return cls.query.filter(
            cls.user == user).filter(cls.probability >=0.9).all()