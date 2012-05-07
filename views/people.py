#!/usr/local/bin/python2.7
#coding:utf-8

import logging
from utils import *
from flask import g, request, render_template, \
        abort, Blueprint

logger = logging.getLogger(__name__)

people = Blueprint('people', __name__)

@people.route('/<username>/')
def show(username):
    current_user = get_current_user()
    visit_user = get_user(username)
    if not visit_user:
        raise abort(404)
    return render_template('people.show.html', \
            current_user = current_user, \
            visit_user = visit_user)
