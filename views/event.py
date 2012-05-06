#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from utils import *
from models.group import *
from config import PAGE_NUM
from sheep.api.cache import backend
from flask import render_template, redirect, \
    request, url_for, g, Blueprint, abort

logger = logging.getLogger(__name__)

event = Blueprint('event', __name__)

def gen_eventlist(events, key):
    if not events:
        return
    for event in events.items:
        from_user = get_user(getattr(event, key))
        e = Obj()
        setattr(e, key, from_user.name)
        setattr(e, key+'_url', from_user.domain or from_user.id)
        e.id = event.id
        e.title = event.title
        e.create_time = event.create_time
        yield e

def gen_replylist(reply, key):
    if not reply:
        return
    count = 1
    for r in reply.items:
        from_user = get_user(getattr(r, key))
        e = Obj()
        setattr(e, key, from_user.name)
        setattr(e, key+'_url', from_user.domain or from_user.id)
        e.num = count
        e.create_time = r.create_time
        e.content = r.content
        yield e

def gen_userlist(orig_list):
    if not orig_list:
        return
    for choice in orig_list:
        u = Obj()
        user = get_user(choice.from_uid)
        u.name = user.name
        u.from_uid_url = user.domain or user.id
        u.id = user.id
        yield u

def gen_event(topic):
    eobj = Obj()
    eobj.id = topic.id
    from_user = get_user(topic.from_uid)
    eobj.from_uid = from_user.name
    eobj.from_uid_url = from_user.domain or from_user.id
    eobj.title = topic.title
    eobj.content = topic.content
    eobj.start_date = topic.start_date
    is_finished = topic.is_finished()
    if is_finished:
        backend.delete('event:view:%d' % eobj.id)
    eobj.finished = topic.finished
    return eobj

@event.route('/')
def index():
    return event_list()

@event.route('/list/')
def event_list():
    page = request.args.get('p', '1')
    if not page.isdigit():
        raise abort(404)

    list_page = get_event_page(page)

    #cache items total num
    total_events_num = get_topic_count()
    if total_events_num != list_page.total:
        backend.delete('event:list:%d' % page)
        list_page = get_event_page(page)

    events = gen_eventlist(list_page, 'from_uid')
    return render_template('events.html', events = events, \
            list_page = list_page)

@event.route('/mine/')
@event.route('/mine/list/')
def my_event_list():
    page = request.args.get('p', '1')
    if not page.isdigit():
        raise abort(404)

    user = get_current_user()
    if not user:
        return redirect(url_for('event.index'))

    list_page = get_mine_event_page(user.id, page)

    #cache items total num
    total_events_num = get_user_topic_count(user.id)
    if total_events_num != list_page.total:
        backend.delete('event:list:%d:%d' % (user.id, page))
        list_page = get_mine_event_page(user.id, page)

    events = gen_eventlist(list_page, 'from_uid')
    return render_template('events.html', events = events, \
            list_page = list_page)

@event.route('/write', methods=['GET', 'POST'])
def write():
    user = get_current_user()
    if not user:
        return redirect(url_for('account.login'))

    if request.method == 'GET':
        return render_template('new_event.html')

    title = request.form.get('title')
    content = request.form.get('content')
    start_date = request.form.get('start_date')

    error = check_new_event(title, content, start_date)
    if error is not None:
        return render_template('new_event.html', \
                content = content, error=error, \
                title = title, start_date = start_date)

    Topic.create(from_uid = user.id,
                 title = title,
                 content = content,
                 start_date = start_date)

    #clean cache
    backend.delete('event:list:1')
    backend.delete('event:topic:count')
    backend.delete('event:topic:%d:count' % user.id)

    return redirect(url_for('event.index'))

@event.route('/view/<int:tid>/')
def view(tid):
    topic = get_topic(tid)
    page = request.args.get('p', '1')

    if not topic or not page.isdigit():
        raise abort(404)
    page = int(page)

    eobj = gen_event(topic)
    reply_list = get_reply(topic.id, page)
    reply = gen_replylist(reply_list, 'from_uid')
    user = get_current_user()
    host = get_user(topic.from_uid)

    interest = request.args.get('interest', None)
    if interest and not user:
        return redirect(url_for('account.login')+\
                '?redirect=%s' % url_for('event.view', tid=eobj.id)+'?interest=%s' % interest)

    is_interest = get_is_interest(topic.id, user.id)
    if _user_control_interest(interest, eobj, user, is_interest):
        is_interest = get_is_interest(topic.id, user.id)

    interest = get_interest_users(eobj.id)
    select = get_select_users(eobj.id)
    interest_list = None
    if not eobj.finished:
        interest_list = gen_userlist(interest)
    select_list = gen_userlist(select)

    return render_template('view_event.html', event = eobj, \
            visit_user = user, reply = reply, finished = eobj.finished, \
            list_page = reply_list, select = select, interest = interest, \
            select_list = select_list, interest_list = interest_list, \
            is_host = user.id == host.id, is_interest = is_interest)

@event.route('/select/<int:tid>/<int:uid>/')
def select(tid, uid):
    _host_control_user('select', tid, uid)
    return redirect(url_for('event.view', tid=tid))

@event.route('/unselect/<int:tid>/<int:uid>/')
def unselect(tid, uid):
    _host_control_user('unselect', tid, uid)
    return redirect(url_for('event.view', tid=tid))

@event.route('/reply/<int:tid>', methods=['POST'])
def reply(tid):
    user = get_current_user()
    if not user:
        return redirect(url_for(event.index))

    topic = get_topic(tid)
    if not topic or topic.finished:
        raise abort(404)

    content = request.form.get('content')
    visit_user_id = request.form.get('_visit_user')
    error = check_new_reply(content, visit_user_id)
    visit_user = get_user(visit_user_id)

    if not visit_user:
        error = u'查无此人'

    if error is not None:
        eobj = gen_event(topic)
        return render_template('view_event.html', \
                content = content, error=error, event=eobj)

    Reply.create(topic_id = topic.id,
                 content = content,
                 from_uid = visit_user.id)

    #clean cache
    backend.delete('event:%d:reply:count' % topic.id)
    mod = get_reply_count(topic.id) % PAGE_NUM
    last_page = get_reply_count(topic.id) / PAGE_NUM + int(bool(mod))
    backend.delete('event:%d:reply:%d' % (topic.id, last_page))
    if mod:
        backend.delete('event:%d:reply:%d' % (topic.id, last_page - 1))

    return redirect(url_for('event.view', tid=tid) + '?p=%d' % last_page)

def _user_control_interest(interest, topic, user, is_interest):
    if topic.finished:
        return False
    if interest == 'want' and user and not is_interest:
        Choice.create_interest(topic.id, user.id)
    elif interest == 'cancel' and user and is_interest:
        is_interest.cancel()
    else:
        return False
    backend.delete('event:user:interest:%d' % user.id)
    backend.delete('event:choice:interest:%d' % topic.id)
    return True

def _host_control_user(method, tid, uid):
    check = _check_host(tid, uid)
    if check and not check[0].finished:
        topic ,is_interest = check
        _mark_status(method, topic.id, is_interest)

def _mark_status(method, tid, cobj):
    if method == 'select' and cobj.status == 1:
        Choice.select(cobj)
    elif method == 'unselect' and cobj.status == 2:
        Choice.unselect(cobj)
    else:
        raise abort(404)
    backend.delete('event:choice:select:%d' % tid)
    backend.delete('event:choice:interest:%d' % tid)
    backend.delete('event:user:interest:%d' % cobj.from_uid)

def _check_host(tid, uid):
    topic = get_topic(tid)
    user = get_current_user()
    applicant = get_user(uid)
    is_interest = get_is_interest(topic.id, user.id)
    if user and topic and applicant and is_interest and \
            user.id == topic.from_uid:
        return topic, is_interest
    return False

