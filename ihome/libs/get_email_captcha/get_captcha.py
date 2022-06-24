#!/usr/bin/env python3
# coding:utf-8

from config_secret import *
from flask import Flask, render_template
from flask_mail import Mail, Message
#  异步发送邮件
from threading import Thread

app2 = Flask(__name__)


app2.config.update(
    MAIL_SERVER='smtp.qq.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,  # 启动/禁用安全套接字层加密
    MAIL_USERNAME="550815548@qq.com",  # 发送方邮箱
    MAIL_PASSWORD=MAIL_PASSWORD  # QQ邮箱的授权码
)
mail = Mail(app2)


def send_async_email(app2, msg):
    with app2.app_context():
        mail.send(msg)


def send_email(email, sms_code):
    """发送邮箱信息"""
    try:
        msg = Message("验证码", sender=app2.config['MAIL_USERNAME'], recipients=[email])
        msg.body = "您的邮箱验证码内容是：%s ," % sms_code + "5分钟内有效"
        t = Thread(target=send_async_email, args=(app2, msg))  # 创建线程
        t.start()
        print("线程.............", t)
        return 0
    except Exception as e:
        print("发送邮件的错误信息：", e)
        return -1
