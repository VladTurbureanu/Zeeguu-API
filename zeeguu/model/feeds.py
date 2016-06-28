# -*- coding: utf8 -*-
import time

from zeeguu import db
from sqlalchemy.orm import relationship
import sqlalchemy.orm.exc
import feedparser


class RSSFeed(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}
    __tablename__ = 'rss_feed'

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(2083))
    description = db.Column(db.String(2083))

    language_id = db.Column(db.String(2), db.ForeignKey("language.id"))
    language = db.relationship("Language")

    url_id = db.Column(db.Integer, db.ForeignKey("url.id"))
    url = db.relationship("Url", foreign_keys='RSSFeed.url_id')

    image_url_id = db.Column(db.Integer, db.ForeignKey("url.id"))
    image_url = db.relationship("Url", foreign_keys='RSSFeed.image_url_id')

    def __init__(self, url, title, description, image_url = None, language = None):
        self.url = url
        self.image_url = image_url
        self.title = title
        self.language = language
        self.description = description

    def as_dictionary(self):
        image_url = ""
        if self.image_url:
            image_url = self.image_url.as_string()

        return dict(
                id = self.id,
                title = self.title,
                url = self.url.as_string(),
                description = self.description,
                language = self.language.id,
                image_url = image_url
        )

    def feed_items(self):
        feed_data = feedparser.parse(self.url.as_string())
        feed_items = [
            dict(
                    title=item.get("title",""),
                    url=item.get("link",""),
                    content=item.get("content",""),
                    summary=item.get("summary",""),
                    published=time.strftime("%Y-%m-%dT%H:%M:%S%z", item.published_parsed)
            )
            for item in feed_data.entries]

        return feed_items

    @classmethod
    def find_by_url(cls, url):
        try:
            result = (cls.query.filter(cls.url == url).one())
            # print "found an existing RSSFeed object"
            return result
        except:
            return None


    @classmethod
    def find_or_create(cls, url, title, description, image_url, language):
        try:
            result = (cls.query.filter(cls.url == url)
                                .filter(cls.title == title)
                                .filter(cls.language == language)
                                # .filter(cls.image_url == image_url)
                                .filter(cls.description == description)
                                .one())
            # print "found an existing RSSFeed object"
            return result
        except sqlalchemy.orm.exc.NoResultFound:
            # print "creating new feed object for " + title
            return cls(url, title, description, image_url, language)

    @classmethod
    def find_for_language_id(cls, language_id):
        return cls.query.filter(cls.language_id == language_id).group_by(cls.title).all()


class RSSFeedRegistration(db.Model):
    __table_args__ = {'mysql_collate': 'utf8_bin'}
    __tablename__ = 'rss_feed_registration'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")

    rss_feed_id = db.Column(db.Integer, db.ForeignKey("rss_feed.id"))
    rss_feed = relationship("RSSFeed")

    def __init__(self, user, feed):
        self.user = user
        self.rss_feed = feed


    @classmethod
    def find_or_create(cls, user, feed):
        try:
            return (cls.query.filter(cls.user == user)
                                .filter(cls.rss_feed == feed)
                                .one())
        except sqlalchemy.orm.exc.NoResultFound:
            return cls(user, feed)

    @classmethod
    def feeds_for_user(cls, user):
        """
        would have been nicer to define a method on the User class get feeds,
        but that would pollute the user model, and it's not nice.
        :param user:
        :return:
        """
        return (cls.query.filter(cls.user == user))

    @classmethod
    def with_id(cls, id):
        return (cls.query.filter(cls.id == id)).one()

    @classmethod
    def with_feed_id(cls, id, user):
        return (cls.query.filter(cls.rss_feed_id == id))\
                        .filter(cls.user_id == user.id).one()
