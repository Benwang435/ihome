# coding: utf-8
from flask import Flask
from config import config_map
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_wtf import CSRFProtect
# 已经安装了mysqlclient不用导入下面的了
# import pymysql
# pymysql.install_as_MySQLdb()

import redis
from flask_mail import Mail

from ihome.utils.commons import ReConverter

db = SQLAlchemy()
csrf = CSRFProtect()

# 创建redis连接对象
redis_store = None


# 工厂模式
def create_app(config_name):
    """
    创建flask的应用对象
    :param config_name:  str  配置模式的名字  （"develop", "product"）
    :return: app
    """
    # 根据配置模式的名字获取模式的类
    app = Flask(__name__)
    config_class = config_map.get(config_name)  # 获取字典映射，即导入config 配置文件
    app.config.from_object(config_class)

    # 使用app初始化db
    db.init_app(app)

    # 初始化redis
    global redis_store
    # decode_responses=True加这句，用python取出来的不带b""字节码
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, decode_responses=True)

    # 利用flask-session，将session数据保存到redis中
    Session(app)

    # 为flask添加CSRF防护,已经在web_html.py文件里设置了cookie里的csrf,还要在请求体或请求头中设置csrf
    csrf.init_app(app)

    # 为flask添加自定义的转换器 正则表达式
    app.url_map.converters["re"] = ReConverter

    # 注册蓝图
    from ihome import api_1_0  # 不放在最上面，放在这里避免循环导包，比如在视图函数导入db模块
    app.register_blueprint(api_1_0.api, url_prefix="/api/v1.0")
    # app.register_blueprint(api_1_0.api)

    # 注册提供html静态文件的蓝图
    from ihome import web_html
    app.register_blueprint(web_html.html)

    # 返回app对象
    return app




import logging
from logging.handlers import RotatingFileHandler

# 设置日志的记录等级
# logging.error("aszxvewr")把错误记录下来，错误级别
# logging.warn("aszxvewr")警告级别
# logging.info("aszxvewr")把状态信息记录下来，消息提示级别
# logging.debug("aszxvewr")调试级别

logging.basicConfig(level=logging.DEBUG)  # 调试debug级
# 创建日志记录器，指明日志的保存路径，每个日志文件的最大大小，保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log.txt", maxBytes=1024 * 1024 * 100, backupCount=10)
# file_log_handler = RotatingFileHandler("logxxxxxx.txt", maxBytes=1024 * 1024 * 100, backupCount=10)
# 创建日志记录的格式如下:              等级      输入日志信息的文件名  行数     日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（current_app）添加日志记录器
logging.getLogger().addHandler(file_log_handler)
