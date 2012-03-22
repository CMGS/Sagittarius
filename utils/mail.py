#!/usr/local/bin/python2.7
#coding:utf-8

import email
import config
import smtplib

def send_email(to_add, subject, html, from_add=config.SMTP_USER):
    if isinstance(to_add, list):
        to_add = ','.join(to_add)

    msg_root = email.MIMEMultipart.MIMEMultipart('related')
    msg_root['Subject'] = subject
    msg_root['From'] = from_add
    msg_root['To'] = to_add
    msg_root.preamble = 'Xiaomen.co account service'

    msg_alternative = email.MIMEMultipart.MIMEMultipart('alternative')
    msg_root.attach(msg_alternative)
    msg_html = email.MIMEText.MIMEText(html, 'html', 'utf-8')
    msg_alternative.attach(msg_html)

    smtp = smtplib.SMTP()
    smtp.set_debuglevel(1)
    smtp.connect(config.SMTP_SERVER)
    smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
    smtp.sendmail(from_add, to_add, msg_root.as_string())
    smtp.quit()

if __name__ == '__main__':
    send_email('ilskdw@126.com', 'xiaomenco account service', '<p>hello world</p>')
