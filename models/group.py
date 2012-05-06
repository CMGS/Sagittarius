#!/usr/local/bin/python2.7
#coding:utf-8

from datetime import datetime

from flaskext.sqlalchemy import SQLAlchemy

from sqlalchemy.sql.expression import desc
from sqlalchemy.schema import UniqueConstraint

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

    def is_finished(self):
        today = datetime.now().date()
        if self.start_date < today:
            self.finished = True
            db.session.add(self)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_event_page(page, per_page):
        today = datetime.now().date()
        page_obj = Topic.query.filter(Topic.start_date>=today).order_by(desc(Topic.create_time)).paginate(page, per_page=per_page)
        return page_obj

    @staticmethod
    def get_user_event_page(uid, page, per_page):
        page_obj = Topic.query.filter(Topic.from_uid==uid).order_by(desc(Topic.id)).paginate(page, per_page=per_page)
        return page_obj

    @staticmethod
    def count():
        today = datetime.now().date()
        return Topic.query.filter(Topic.start_date>=today).count()

class Reply(db.Model):
    __tablename__ = 'reply'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    topic_id = db.Column(db.Integer, index=True)
    from_uid = db.Column(db.Integer, index=True)
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, topic_id, content, from_uid, *args, **kwargs):
        self.topic_id = topic_id
        self.from_uid = from_uid
        self.content = content
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    @staticmethod
    def create(topic_id, from_uid, content):
        reply = Reply(topic_id = topic_id,
                      from_uid=from_uid,
                      content = content)
        db.session.add(reply)
        db.session.commit()

    @staticmethod
    def get_reply_page(topic_id, page, per_page):
        page_obj = Reply.query.filter(Reply.topic_id==topic_id).paginate(page, per_page=per_page)
        return page_obj

'''
1, interesting
2, choose
3, not allow, expire
'''
class Choice(db.Model):
    __tablename__ = 'choice'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    topic_id = db.Column(db.Integer, index=True)
    from_uid = db.Column(db.Integer, index=True)
    status = db.Column(db.Integer, index=True, default=1)

    def __init__(self, topic_id, from_uid, status):
        self.topic_id = topic_id
        self.from_uid = from_uid
        self.status = status

    @staticmethod
    def create_interest(tid, uid):
        try:
            c = Choice(tid, uid, 1)
            db.session.add(c)
            db.session.commit()
            return True
        except Exception, e:
            if getattr(e, 'orig') and e.orig[0] == 1062:
                db.session.rollback()
                return False
            raise e

    def cancel(self):
        db.session.delete(self)
        db.session.commit()

    def is_interest(self):
        if self.status == 1:
            return True
        return False

    def is_select(self):
        if self.status == 2:
            return True
        return False

    @staticmethod
    def select(choice):
        choice.status = 2
        db.session.add(choice)
        db.session.commit()

    @staticmethod
    def unselect(choice):
        choice.status = 1
        db.session.add(choice)
        db.session.commit()

    @staticmethod
    def get_user_events(uid, page, per_page):
        page_obj = Choice.query.filter_by(from_uid=uid).order_by(desc(Choice.id)).paginate(page, per_page=per_page)
        return page_obj

UniqueConstraint(Choice.topic_id, Choice.from_uid, name='uix_tid_uid')
