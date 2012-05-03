#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from utils import *
from models.group import *
from sheep.api.cache import backend
from flask import render_template, redirect, \
    request, url_for, g, Blueprint, abort

logger = logging.getLogger(__name__)

event = Blueprint('event', __name__)

def gen_eventlist(events, key):
    event_list = []
    for event in events:
        from_user = get_user(getattr(event, key))
        e = Obj()
        setattr(e, key, from_user.name)
        setattr(e, key+'_url', from_user.domain or from_user.id)
        e.id = event.id
        e.title = event.title
        event_list.append(e)
    return event_list

def gen_replylist(reply, key):
    if not reply:
        return None
    reply = reply.items
    reply_list = []
    count = 1
    for r in reply:
        from_user = get_user(getattr(r, key))
        e = Obj()
        setattr(e, key, from_user.name)
        setattr(e, key+'_url', from_user.domain or from_user.id)
        e.num = count
        e.create_time = r.create_time
        e.content = r.content
        reply_list.append(e)
    return reply_list

def gen_event(topic):
    eobj = Obj()
    eobj.id = topic.id
    from_user = get_user(topic.from_uid)
    eobj.from_uid = from_user.name
    eobj.from_uid_url = from_user.domain or from_user.id
    eobj.title = topic.title
    eobj.content = topic.content
    eobj.start_date = topic.start_date
    return eobj

@event.route('/')
def index():
    return event_list(1)

@event.route('/list', defaults={'page': 1})
@event.route('/list/<int:page>')
def event_list(page):
    list_page = get_event_page(page)

    #cache items total num
    total_events_num = count_topic()
    if total_events_num != list_page.total:
        backend.delete('event:list:%d' % page)
        list_page = get_event_page(page)

    if not list_page:
        return 'No events'
    events = gen_eventlist(list_page.items, 'from_uid')
    return render_template('events.html', events = events, \
            list_page = list_page)

@event.route('/mine', defaults={'page': 1})
@event.route('/mine/list', defaults={'page': 1})
@event.route('/mine/list/<int:page>')
def my_event_list(page):
    user = get_current_user()
    if not user:
        return redirect(url_for('event.index'))

    list_page = get_mine_event_page(user.id, page)

    #cache items total num
    total_events_num = count_user_topic(user.id)
    if total_events_num != list_page.total:
        backend.delete('event:list:%d:%d' % (user.id, page))
        list_page = get_mine_event_page(user.id, page)

    if not list_page:
        return 'No events'
    events = gen_eventlist(list_page.items, 'from_uid')
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

@event.route('/view/<event_id>')
def view(event_id):
    user = get_current_user()
    topic = get_topic(event_id)
    reply_page = request.args.get('p', '1')

    if not topic or not reply_page.isdigit():
        raise abort(404)
    reply_page = int(reply_page)

    eobj = gen_event(topic)
    reply_list = get_reply(topic.id, reply_page)
    #clean cache when update
    if reply_list and count_reply(topic.id) != reply_list.total:
        backend.delete('event:%d:reply:%s' % (topic.id, reply_page))
        reply_list = get_reply(topic.id, reply_page)
    reply = gen_replylist(reply_list, 'from_uid')

    if user:
        return render_template('view_event.html', event = eobj, \
                visit_user_id = user.id, reply = reply, \
                list_page = reply_list)
    else:
        return render_template('view_event.html', event = eobj, \
                diable_reply = 1, reply = reply, list_page = reply_list)

@event.route('/reply/<int:event_id>', methods=['POST'])
def reply(event_id):
    user = get_current_user()
    if not user:
        return redirect(url_for(event.index))

    topic = get_topic(event_id)
    if not topic:
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
    backend.delete('event:%d:reply:1' % topic.id)
    backend.delete('event:%d:reply:count' % topic.id)

    return redirect(url_for('event.view', event_id=event_id))

