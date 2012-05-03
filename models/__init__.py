#!/usr/bin/python
# encoding: UTF-8

from .mail import *
from .group import *
from .account import *

def init_db(app):
    init_mail_db(app)
    init_group_db(app)
    init_account_db(app)

