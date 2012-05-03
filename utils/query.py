#!/usr/local/bin/python2.7
#coding:utf-8

from flask import g
from helper import Obj
from redistore import redistore
from sheep.api.cache import cache
from validators import check_domain

from config import PAGE_NUM
from models.mail import Mail
from models.group import Topic, Reply, Choice
from models.account import User, Forget, OAuth

def get_current_user():
    if not g.session or not g.session.get('user_id') or not g.session.get('user_token'):
        return None
    token = redistore.get('account|uid-%s|token' % g.session['user_id'])
    if not token or g.session['user_token'] != token:
        return None
    return get_user(g.session['user_id'])

@cache('account:{username}', 300)
def get_user(username):
    try:
        username = int(username)
        if username <= 0:
            return None
        return User.query.get(username)
    except:
        if check_domain(username):
            return None
        return get_user_by_domain(domain=username)

@cache('account:{domain}', 300)
def get_user_by_domain(domain):
    return get_user_by(domain=domain).first()

@cache('account:{email}', 300)
def get_user_by_email(email):
    return get_user_by(email=email).first()

@cache('account:{stub}', 100)
def get_forget_by_stub(stub):
    return Forget.query.filter_by(stub=stub).first()

@cache('mail:unread:{to_uid}', 300)
def get_unread_mail_count(to_uid):
    return get_mail_by(to_uid=to_uid, is_read=0).count()

@cache('mail:inbox:{uid}', 300)
def get_mail_inbox_all(uid):
    return get_mail_by(to_uid=uid).all()

@cache('mail:outbox:{uid}', 300)
def get_mail_outbox_all(uid):
    return get_mail_by(from_uid=uid).all()

@cache('mail:view:{mid}', 300)
def get_mail(mid):
    try:
        mid = int(mid)
        return mail.query.get(mid)
    except:
        return None

@cache('event:view:{tid}', 300)
def get_topic(tid):
    try:
        tid = int(tid)
        return Topic.query.get(tid)
    except:
        return None

@cache('event:list:{page}', 300)
def get_event_page(page):
    try:
        page = int(page)
        page_obj = Topic.get_event_page(page, per_page=PAGE_NUM)
        list_page = gen_list_page_obj(page_obj)
        return list_page
    except Exception, e:
        return None

@cache('event:list:{user_id}:{page}', 100)
def get_mine_event_page(user_id, page):
    try:
        user_id = int(user_id)
        page_obj = Topic.get_user_event_page(user_id, page, per_page=PAGE_NUM)
        list_page = gen_list_page_obj(page_obj)
        return list_page
    except Exception, e:
        return None

def gen_list_page_obj(page_obj):
    list_page = Obj()
    list_page.items = page_obj.items
    list_page.has_next = page_obj.has_next
    list_page.has_prev = page_obj.has_prev
    list_page.next_num = page_obj.next_num
    list_page.page = page_obj.page
    list_page.pages = page_obj.pages
    list_page.total = page_obj.total
    list_page.iter_pages = xrange(1, page_obj.pages+1)
    return list_page

def get_mail_by(**kw):
    return Mail.query.filter_by(**kw)

def get_oauth_by(**kw):
    return OAuth.query.filter_by(**kw).first()

def get_user_by(**kw):
    return User.query.filter_by(**kw)

