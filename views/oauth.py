#!/usr/bin/python
# encoding: UTF-8

import urllib
import logging
from models import db, OAuth
from flask import Blueprint, g, \
        request, redirect, url_for

import config
from lib.qq import qq
from lib.weibo import weibo
from lib.douban import douban
from lib.renren import renren

logger = logging.getLogger(__name__)

class Base_OAuth_Login(object):
    def __init__(self, name, oauth_obj, uid_str='uid', token_str='access_token'):
        self.name = name
        self.oauth_obj = oauth_obj
        self.uid_str = uid_str
        self.token_str = token_str

    def get_token(self):
        if g.user:
            oauth_info = g.oauth(self.name)
            if not oauth_info:
                return
            return oauth_info.oauth_token

    def login(self):
        next_url = url_for('account.register')
        if g.user:
            if g.oauth(self.name):
                return redirect(request.referrer or url_for('index'))
            next_url = url_for('account.bind')
        callback = 'http://%s%s' % (config.OAUTH_REDIRECT_DOMAIN, url_for('%s_oauth.authorized' % self.name))
        return self.oauth_obj.authorize(callback, next_url)

    def authorized(self, resp):
        csrf = g.session.pop('%s_oauthcsrf' % self.name, None)
        state = request.args.get('state')
        if state and urllib.unquote(state) !=  csrf:
            return redirect(url_for('index'))
        next_url = g.session.pop('%s_oauthnext' % self.name) or url_for('index')
        logger.info(resp)
        if not resp or not uid or not token:
            return redirect(next_url)
        uid = resp.get(self.uid_str, None)
        token = resp.get(self.token_str, None)

        oauth = OAuth.query.filter_by(oauth_uid=resp[self.uid_str]).first()
        if oauth is None:
            oauth = OAuth(None, resp[self.uid_str], self.name)

        old_token = oauth.oauth_token
        oauth.oauth_token = resp[self.token_str]
        if not g.user and oauth.uid:
            g.session['user_id'] = oauth.uid
            if old_token != oauth.oauth_token:
                logger.info(old_token)
                logger.info(oauth.oauth_token)
                self.update_token(oauth)
            return redirect(url_for('index'))
        g.session['from_oauth'] = oauth
        return redirect(next_url)

    def update_token(self, oauth):
        db.session.add(oauth)
        db.session.commit()

qq_oauth_login = Base_OAuth_Login('qq', qq, 'openid')
weibo_oauth_login = Base_OAuth_Login('weibo', weibo, 'uid')
douban_oauth_login = Base_OAuth_Login('douban', douban, 'douban_user_id')
renren_oauth_login = Base_OAuth_Login('renren', renren, 'renren_uid')

class OAuth_views(object):
    def __init__(self):
        self.views = {}

    def add(self, oauth_name, login_obj, oauth_obj):
        self.views[oauth_name] = Blueprint('%s_oauth' % oauth_name, __name__)
        self._init_tokengetter(login_obj, oauth_obj)
        self._init_url_rule(oauth_name, login_obj, oauth_obj)

    def _init_url_rule(self, oauth_name, login_obj, oauth_obj):
        blueprint = self.views.get(oauth_name, None)
        if not blueprint:
            return
        blueprint.add_url_rule('/login', view_func=getattr(login_obj, 'login'))
        blueprint.add_url_rule('/authorized', view_func=\
            getattr(oauth_obj, 'authorized_handler')(getattr(login_obj, 'authorized'))
        )

    def _init_tokengetter(self, login_obj, oauth_obj):
        getattr(oauth_obj, 'tokengetter')(getattr(login_obj, 'get_token'))

    def register_blueprints(self, app):
        for name, blueprint in self.views.iteritems():
            url_prefix = '/%s' % name
            app.register_blueprint(blueprint, url_prefix=url_prefix)

oauth = OAuth_views()
oauth.add('qq', qq_oauth_login, qq)
oauth.add('weibo', weibo_oauth_login, weibo)
oauth.add('douban', douban_oauth_login, douban)
oauth.add('renren', renren_oauth_login, renren)
