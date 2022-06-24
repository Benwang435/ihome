# coding:utf-8
from flask import session, jsonify, current_app, g
from werkzeug.routing import BaseConverter
from ihome.utils.response_code import RET
import functools


# 定义正则转换器
class ReConverter(BaseConverter):
    def __init__(self, url_map, regex):
        # 调用父类的初始化方法
        super(ReConverter, self).__init__(url_map)
        self.regex = regex


# 定义登录装饰器
def login_required(view_func):
    # 在内层函数中再加上一个装饰器functools.wraps(view_func),
    # 视图函数中使用__name_（或使用__doc__获取函数说明文档时）获取视图函数名称时，不会使用这个装饰器函数的名称
    @functools.wraps(view_func)  # 这个要加上，否则会出现endpoint重名
    def wrapper(*args, **kwargs):
        # 判断用户的登录状态
        user_id = session.get("user_id")
        g.user_id = user_id  # 使用g对象 可以之后的被装饰视图函数中使用g对象获取
        if user_id is not None:
            # 如果用户是登录的，执行视图函数
            return view_func(*args, **kwargs)
        else:
            # 如果用户没有登录，返回未登录状态
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    return wrapper

# 视图函数，给一个视图函数加装饰器,即调用上面的装饰器
# @login_required
# def set_user_avatar():
#     user_id = g.user_id  # 使用上面装饰器函数保存在g对象中的user_id
#     return "xxx"

# set_user_avatar() --> wrapper()
