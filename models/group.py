#!/usr/local/bin/python2.7
#coding:utf-8

from datetime import datetime

from sqlalchemy.sql.expression import desc
from flaskext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()
def init_group_db(app):
    db.init_app(app)
    db.app = app
    db.create_all()

class Topic(db.Model):
    __tablename__ = 'topic'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    from_uid = db.Column(db.Integer, index=True)
    title = db.Column(db.String(45), nullable=False)
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    start_date = db.Column(db.Date, nullable=False)
    finished = db.Column(db.Integer, default=False, index=True)

    def __init__(self, from_uid, title, content, *args, **kwargs):
        self.from_uid = from_uid
        self.title = title
        self.content = content
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    @staticmethod
    def create(from_uid, title, content, start_date):
        topic = Topic(from_uid=from_uid,
                      title = title,
                      content = content,
                      start_date = start_date)
        db.session.add(topic)
        db.session.commit()

    @staticmethod
    def mark_as_finished(topic):
        topic.finished = True
        db.session.add(topic)
        db.session.commit()

    @staticmethod
    def get_event_page(page, per_page):
        today = datetime.now().date()
        page_obj = Topic.query.filter(Topic.start_date>=today).order_by(desc(Topic.id)).paginate(page, per_page=per_page)
        return page_obj

class Reply(db.Model):
    __tablename__ = 'reply'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    topic_id = db.Column(db.Integer, index=True)
    from_uid = db.Column(db.Integer, index=True)
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, from_uid, content, *args, **kwargs):
        self.from_uid = from_uid
        self.content = content
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    @staticmethod
    def create(from_uid, content):
        reply = Reply(from_uid=from_uid,
                      content = content)
        db.session.add(topic)
        db.session.commit()

class Choice(db.Model):
    __tablename__ = 'choice'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    topic_id = db.Column(db.Integer, index=True)
    choice_uid = db.Column(db.Integer, index=True)

    def __init__(self, topic_id, choice_uid):
        self.topic_id = topic_id
        self.choice_uid = choice_uid

    @staticmethod
    def choice(tid, uid):
        c = Choice(tid, uid)
        db.session.add(c)
        db.session.commit()

