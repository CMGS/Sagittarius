#!/usr/bin/python
# encoding: UTF-8

import config
import logging
from models import *
from lib.weibo import weibo, GET
from views.weibo import weibo_oauth
from sheep.api.statics import static_files
from flask import Flask, render_template, redirect, \
    request, session, url_for, g

app = Flask(__name__)
app.debug = config.DEBUG
app.secret_key = config.SECRET_KEY
app.jinja_env.filters['s_files'] = static_files
app.register_blueprint(weibo_oauth, url_prefix='/Weibo')

logger = logging.getLogger(__name__)

init_db()

@app.route('/')
def index():
    if g.user is None:
        return render_template('index.html')
    else:
        logout = '<a href="/Logout">Logout</a>'
        oauth_info = g.oauth('weibo')
        if oauth_info:
            user_info = GET("/users/show/", oauth_info.oauth_uid)
            logger.info(user_info.data)
        return render_template('index.html', logout=logout)

@app.route('/Logout')
def logout():
    session.pop('user_id', None)
    return redirect(request.referrer or url_for('index'))

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])
        g.oauth = lambda otype: OAuth.query.filter_by(oauth_type=otype, uid=g.user.id).first()

@app.after_request
def after_request(response):
    db_session.remove()
    return response

