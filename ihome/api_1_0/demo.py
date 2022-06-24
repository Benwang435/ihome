# -*- coding: utf-8 -*-

# import redis
# email = "555@qq.com"
# redis_store = redis.Redis(host='192.168.1.111',port=6379)
# real_sms_code = redis_store.get("sms_code_%s" % email)
# print(real_sms_code)
from ihome.api_1_0 import api

from . import api
from flask import Response
import json
@api.route('/demo')
def demo():
    res = json.dumps({'content':'这是demo文件'})
    return res, 200, {'Content-Type':"application/json"}