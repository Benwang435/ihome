# coding:utf-8
import re

from flask import request, jsonify, current_app, session
from ihome.api_1_0 import api
from ihome import redis_store, db, constants
from ihome.models import User
from ihome.utils.response_code import RET
from sqlalchemy.exc import IntegrityError


@api.route("/users/", methods=["POST"])
def register():
    """用户注册
    获取请求的参数：邮箱号，短信验证码，密码，确认密码

    """
    # 获取请求的json数据，get_json返回的是字典
    req_dict = request.get_json()
    email = req_dict.get("email")
    sms_code = req_dict.get("sms_code")
    password = req_dict.get("password")
    password2 = req_dict.get("password2")  # 后端校验密码的话，再获取这个

    # 校验参数
    if not all([email, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断邮箱号的格式
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
        # 表示格式不对
        return jsonify(errno=RET.PWDERR, errmsg="邮箱号格式错误啦")

    # 判断两次密码是否一致
    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg="两次密码不致")

    # 业务逻辑处理：
    # 从redis取出邮箱验证码
    try:
        # real_sms_code = redis_store.get("sms_code_%s" % email).decode("utf-8")
        real_sms_code = redis_store.get("sms_code_%s" % email)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="读取redis真实验证码错误！")

    # 判断取出来的邮箱验证码是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg="邮箱验证码失效!")

    # 删除redis中的邮箱验证码，防止重复使用校验
    try:
        redis_store.delete("sms_code_%s" % email)
    except Exception as e:
        current_app.logger.error(e)

    # 判断用户填写的邮箱验证码是否正确
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="邮箱验证码错误!!")

    # 保存用户的注册数据到数据库中
    user = User(name=email, email=email)
    # user.generate_password_hash(password)  # 通过下面的属性方式设置值
    user.password = password  # 设置属性值，在models.py里已经设置了@password.setter

    try:
        db.session.add(user)
        db.session.commit()
    # IntegrityError 表示插入的邮箱号出现了重复，就是邮箱号已注册过
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg="邮箱号已经破碎")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库异常")

    # 保存登录状态到session中去
    session["name"] = email
    session["email"] = email
    session["user_id"] = user.id

    # 返回结果
    return jsonify(errno=RET.OK, errmsg="注册成功")


@api.route("/sessions/", methods=["POST"])
def login():
    """
    功能：用户登录

    """
    # 获取参数,get_json()获取前端的json数据
    req_dict = request.get_json()
    email = req_dict.get("email")
    password = req_dict.get("password")

    # 校验参数---
    # 完整性校验参数
    if not all([email, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断邮箱号的格式
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
        return jsonify(errno=RET.PARAMERR, errmsg="邮箱格式错误")

    # 判断错误次数是否超过限制，超过的话则返回登录错误次数过多
    # redis记录存取格式：“access_nums_请求的ip”：次数
    user_ip = request.remote_addr  # 用户的ip地址
    try:
        access_nums = redis_store.get("access_nums_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_nums is not None and int(access_nums) >= constants.LOGIN_ERROR_MAX_TIMES:
            return jsonify(errno=RET.REQERR, errmsg="登录错误次数过多，请稍后重试")

    # 逻辑处理：
    # 从数据库中通过邮箱号查询用户是否存在
    try:
        user = User.query.filter_by(email=email).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    # 用数据库的密码与用户填写的密码对比判断是不是错误,再判断密码是不是错误
    if user is None or not user.check_password(password):
        # 如果验证失败(用户是空的或者密码不对)，记录错误次数，返回信息
        try:
            redis_store.incr("access_nums_%s" % user_ip)
            redis_store.expire("access_nums_%s" % user_ip, constants.LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="用户名或密码错误")

    # 如果获取到user并且密码对比成功，在session中保存登录状态
    session["name"] = user.name
    session["email"] = user.email
    session["user_id"] = user.id

    return jsonify(errno=RET.OK, errmsg="登录成功！")


# 登录后的页面,与下面使用相同的路由名称，因为请求方式不一样
@api.route("/session/", methods=["GET"])
def check_login():
    """检查登录状态"""
    # 试着从session中获取登录用户的名称
    name = session.get("name")
    # 如果用户的名字存在就表示已经登录，否则表示没有
    if name is not None:
        return jsonify(errno=RET.OK, errmsg="true", data={"name": name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg="false")


# 退出
@api.route("/session/", methods=["DELETE"])
def logout():
    """退出登录"""
    # 在web_html.py中生成csrf的同时也保存一份到了session中
    # csrf_token = session.get("csrf_token")
    session.clear()  # 在redis里一次性把数据删除。删除session数据.
    # session["csrf_token"] = csrf_token  # 把csrf再还给session，现在再去获取的不是在redis里?
    return jsonify(errno=RET.OK, errmsg="退出OK")
