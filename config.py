# -*- coding: utf-8 -*-

import redis
from config_secret import *


class Config:
    """基础配置信息"""
    SECRET_KEY = "js@dhfkjbkjfbsjdfg2ertyeyetyet"

    # 数据库 mysql
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # 数据库 redis
    REDIS_HOST = "192.168.1.111"
    REDIS_PORT = 6379
    # flask-session 配置  详细参见：https://pythonhosted.org/Flask-Session/
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 加上decode_responses=True即可解决 编码中的b'',如下：
    # redis_store = redis.StrictRedis(host='127.0.0.1', port=6379, decode_responses=True)
    # 这样就没有b的bytes了，注意 str(url, encoding='utf-8')
    SESSION_USE_SIGNER = True  # 对cookie中的session_id设置隐藏处理
    PERMANENT_SESSION_LIFETIME = 86400  # session数据的有效期，单位：秒

    """
    源码中需要的字段
    session_interface = RedisSessionInterface(
    config['SESSION_REDIS'], config['SESSION_KEY_PREFIX'],
    config['SESSION_USE_SIGNER'], config['SESSION_PERMANENT'])
    
    """


class DevelopmentConfig(Config):
    """开发者模式的配置信息"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境的配置信息"""
    pass


# 映射关系
config_map = {
    "develop": DevelopmentConfig,
    "product": ProductionConfig,
}
