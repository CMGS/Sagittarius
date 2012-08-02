#!/usr/bin/python
# encoding: UTF-8

import os
import time
import config
import logging

from utils import *
from models import *

from views.api import api
from views.mail import mail
from views.oauth import oauth
from views.event import event
from views.people import people
from views.account import account

from sheep.api.statics import static_files
from sheep.api.sessions import SessionMiddleware, \
    FilesystemSessionStore

from flaskext.csrf import csrf
from flask import Flask, render_template, \
        request, url_for, g, redirect

app = Flask(__name__)
app.debug = config.DEBUG
app.secret_key = config.SECRET_KEY
app.jinja_env.filters['s_files'] = static_files
app.jinja_env.globals['get_current_user'] = get_current_user
app.jinja_env.globals['get_unread_mail_count'] = get_unread_mail_count

app.config.update(
    SQLALCHEMY_DATABASE_URI = config.DATABASE_URI,
    SQLALCHEMY_POOL_SIZE = 100,
    SQLALCHEMY_POOL_TIMEOUT = 10,
    SQLALCHEMY_POOL_RECYCLE = 3600,
    SESSION_COOKIE_DOMAIN = config.SESSION_COOKIE_DOMAIN,
)

oauth.register_blueprints(app)
app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(people, url_prefix='/people')
app.register_blueprint(event, url_prefix='/event')
app.register_blueprint(mail, url_prefix='/mail')
app.register_blueprint(api, url_prefix='/api')

logger = logging.getLogger(__name__)

init_db(app)
csrf(app)
app.wsgi_app = SessionMiddleware(app.wsgi_app, \
        FilesystemSessionStore(), \
        cookie_name=config.SESSION_KEY, cookie_path='/', \
        cookie_domain=config.SESSION_COOKIE_DOMAIN)

@app.route('/')
def index():
    return render_template('index.html')

@app.before_request
def before_request():
    g.session = request.environ['xiaomen.session']

