#!/usr/local/bin/python2.7
#coding:utf-8

import os
import logging

from utils import *
from models.group import *
from sheep.api.cache import backend
from flask import render_template, redirect, \
    request, url_for, g, Blueprint, abort

logger = logging.getLogger(__name__)

event = Blueprint('event', __name__)

def gen_eventlist(events, key, pos=0):
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

@event.route('/')
def index():
    return event_list(1)

@event.route('/list', defaults={'page': 1})
@event.route('/list/<int:page>')
def event_list(page):
    list_page = get_event_page(page)
    #cache items total num
    #TODO ugly
    print list_page.total
    if not os.environ.get('TOTAL_EVENTS_NUM'):
        os.environ['TOTAL_EVENTS_NUM'] = str(list_page.total)
    elif int(os.environ['TOTAL_EVENTS_NUM']) != list_page.total:
        print os.environ.get('TOTAL_EVENTS_NUM')
        backend.delete('event:list:%d' % page)
        list_page = get_event_page(page)
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
    if os.environ.get('TOTAL_EVENTS_NUM'):
        os.environ['TOTAL_EVENTS_NUM'] = str(int(os.environ['TOTAL_EVENTS_NUM']) + 1)
    backend.delete('event:list:1')

    return redirect(url_for('event.index'))
