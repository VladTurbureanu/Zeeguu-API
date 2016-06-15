from zeeguu import db

class WatchInteractionEvent(db.Model):
    __tablename__ = 'device_event'
    __table_args__ = dict(mysql_collate='utf8_bin')

    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)



