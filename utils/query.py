#!/usr/local/bin/python2.7
#coding:utf-8

from flask import g
from sheep.api.cache import cache
from werkzeug.exceptions import NotFound

from validators import check_domain
from helper import gen_list_page_obj

from config import PAGE_NUM
from models.mail import Mail
from models.group import Topic, Reply, Choice
from models.account import User, Forget, OAuth

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

@cache('mail:inbox:count:{to_uid}', 300)
def get_inbox_count(to_uid):
    return get_mail_by(to_uid=to_uid).count()

@cache('mail:outbox:count:{from_uid}', 300)
def get_outbox_count(from_uid):
    return get_mail_by(from_uid=from_uid).count()

@cache('mail:inbox:{uid}:{page}', 300)
def get_inbox_mail(uid, page):
    try:
        page = int(page)
        uid = int(uid)
        page_obj = Mail.get_inbox_page(uid, page, per_page=PAGE_NUM)
        list_page = gen_list_page_obj(page_obj)
        return list_page
    except NotFound, e:
        raise e
    except Exception, e:
        return None

@cache('mail:outbox:{uid}:{page}', 300)
def get_outbox_mail(uid, page):
    try:
        page = int(page)
        uid = int(uid)
        page_obj = Mail.get_outbox_mail(uid, page, per_page=PAGE_NUM)
        list_page = gen_list_page_obj(page_obj)
        return list_page
    except NotFound, e:
        raise e
    except Exception, e:
        return None

@cache('mail:view:{mid}', 300)
def get_mail(mid):
    try:
        mid = int(mid)
        return Mail.query.get(mid)
    except Exception, e:
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
    except NotFound, e:
        raise e
    except Exception, e:
        return None

@cache('event:list:{uid}:{page}', 100)
def get_user_event_page(uid, page):
    try:
        uid = int(uid)
        page_obj = Topic.get_user_event_page(uid, page, per_page=PAGE_NUM)
        list_page = gen_list_page_obj(page_obj)
        return list_page
    except NotFound, e:
        raise e
    except Exception, e:
        return None

@cache('event:interest:list:{uid}:{page}', 300)
def get_user_interest(uid, page):
    try:
        uid = int(uid)
        page_obj = Choice.get_user_events(uid, page, per_page=PAGE_NUM)
        list_page = gen_list_page_obj(page_obj)
        return list_page
    except NotFound, e:
        raise e
    except Exception, e:
        return None

@cache('event:{topic_id}:reply:{page}', 100)
def get_reply(topic_id, page):
    try:
        topic_id = int(topic_id)
        page_obj = Reply.get_reply_page(topic_id, page, PAGE_NUM)
        list_page = gen_list_page_obj(page_obj)
        return list_page
    except NotFound, e:
        raise e
    except Exception, e:
        return None

@cache('event:{topic_id}:reply:count', 300)
def get_reply_count(topic_id):
    try:
        topic_id = int(topic_id)
        return Reply.query.filter(Reply.topic_id==topic_id).count()
    except Exception, e:
        return 0

@cache('event:topic:count', 300)
def get_topic_count():
    return Topic.count()

@cache('event:topic:{uid}:count', 300)
def get_user_topic_count(uid):
    try:
        uid = int(uid)
        return Topic.query.filter(Topic.from_uid==uid).count()
    except Exception, e:
        return 0

@cache('event:topic:interest:{uid}:count', 300)
def get_user_interest_topic_count(uid):
    try:
        uid = int(uid)
        return Choice.query.filter(Choice.from_uid==uid).count()
    except Exception, e:
        return 0

@cache('event:interest:{tid}', 300)
def get_interest_users(tid):
    return get_choice_by(topic_id=tid, status=1).all()

@cache('event:select:{tid}', 300)
def get_select_users(tid):
    return get_choice_by(topic_id=tid, status=2).all()

@cache('event:{uid}:interest:{tid}', 300)
def get_is_interest(tid, uid):
    return get_choice_by(topic_id=tid, from_uid=uid).first()

def get_choice_by(**kw):
    return Choice.query.filter_by(**kw)

def get_mail_by(**kw):
    return Mail.query.filter_by(**kw)

def get_oauth_by(**kw):
    return OAuth.query.filter_by(**kw).first()

def get_user_by(**kw):
    return User.query.filter_by(**kw)

def get_current_user():
    if not g.session or not g.session.get('user_id') or not g.session.get('user_token'):
        return None
    user = get_user(g.session['user_id'])
    if g.session['user_token'] != user.token:
        return None
    return user

