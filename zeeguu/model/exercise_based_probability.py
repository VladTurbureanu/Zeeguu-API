import decimal

import sqlalchemy.orm

from zeeguu import db
from zeeguu.model.exercise_outcome import ExerciseOutcome


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

    def update_probability_after_adding_bookmark_with_same_word(self, bookmark, user):
        from zeeguu.model.bookmark import Bookmark
        count_bookmarks_with_same_word = len(Bookmark.find_all_by_user_and_word(user, bookmark.origin))
        self.probability = (float(self.probability * count_bookmarks_with_same_word) + 0.1)/(count_bookmarks_with_same_word+1)# compute avg probability of all bookmarks with same word





    #calculates the probability of knowing a certain bookmark after a exercise_outcome.
    def calculate_known_bookmark_probability(self,bookmark):
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