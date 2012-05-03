#!/usr/local/bin/python2.7
#coding:utf-8

from flaskext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()
def init_account_db(app):
    db.init_app(app)
    db.app = app
    db.create_all()

class Topic(db.Model):
    pass

class Reply(db.Model):
    pass
