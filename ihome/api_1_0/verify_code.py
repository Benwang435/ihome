# coding:utf-8
import random

from . import api
# 导入别人写好的图片验证码包
from ihome.utils.captcha.captcha_get import captcha
from ihome import redis_store
from ihome import constants
from flask import current_app, jsonify, make_response, request
from ihome.models import User
from ihome.libs.get_email_captcha import get_captcha
# restful是一种后端接口如果定义的规范REST:representational state transfer
# 如增删改查商品 goods:,/get_goods,/add_goods,/update_goods,/delete_goods
# 可只定义一个路径：/goods,可利用HTTP请求方式：get,post,put,delete
# 前端访问GET 127.0.0.1/api/v1.0/image_codes/<image_code_id>  image_code_id是图片验证码的编号
from ihome.utils.response_code import RET
from ihome.api_1_0.forms import RegistForm
"""
获取图片和邮箱验证码
"""

@api.route("/image_codes/<image_code_id>")
def get_image_code(image_code_id):
    """
    功能：获取图片验证码
    :param image_code_id： 图片验证码编号
    :return: 正常：会返回验证码图片， 异常：返回json
    """
    # 视图函数一般流程：
    #   获取参数 已经有了image_code_id
    #   检验参数 也已经有要传的参数
    #   业务逻辑处理 ：生成验证码图片(借助工具)，把验证码和编号保存到redis
    #   返回值,即返回图片

    # 生成验证码图片:名字，真实文本，image_data是图片数据
    name, text, image_data = captcha.gen_captcha()
    # 将验证码真实值和编号保存到redis(建立在字符串的基础上)中,设置有效期

    # 单条维护记录，使用字符串最合适
    # "image_code_编号1":"真实值"
    # "image_code_编号2":"真实值"

    # redis_store.set("image_code_%s" % image_code_id, text)
    # redis_store.expire("image_code_%s" % image_code_id, IMAGE_CODE_REDIS_EXPIRES)  # 180是秒
    # 上面的可以用下面的一句代替：
    try:
        redis_store.setex("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 记录到日志中
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片验证码信息失败")

    # 返回图片直接这样是没有类型的image_data,需要加上Content-Type
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp


# 获取邮箱验证码，改写成post请求
@api.route("/sms_codes/", methods=['GET', 'POST'])
def get_sms_code():
    """
    功能：获取邮箱验证码

    1 获取各参数
    2 校验参数是否正常
    3 业务逻辑处理----------
    """
    # 获取前台ajax请求的参数
    req_dict = request.get_json()
    email = req_dict.get("email_s")
    f = RegistForm()
    if not f.validate_on_submit():
        errors = f.errors
        print('邮箱格式返回的错误:', errors)
        return jsonify(errno=RET.DATAERR, errmsg=f.errors.get('email'))
        # return jsonify(errno=RET.DATAERR, errmsg="邮箱格式不正确！")

    # ---------获取短信验证码的操作流程--------------
    # 获取前端填写的参数,先获取图片验证码image_code 和 图片验证码的编号image_code_id
    image_code = req_dict.get("image_code")
    image_code_id = req_dict.get("image_code_id") # 使用编号获取redis里的验证码

    # 校验图片验证码编号和图片验证码是否正常
    if not all([image_code_id, image_code]):
        # 表示参数不完整
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    """业务逻辑处理"""
    # 校验图片验证码，先尝试从redis中取出真实的图片验证码
    try:
        # 注意：一般在网络编程中，服务器和浏览器只认bytes类型数据,这里返回的是bytes，如果有必要，就decode一下
        # real_image_code = redis_store.get("image_code_%s" % image_code_id).decode("utf-8")
        real_image_code = redis_store.get("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="redis数据库异常")

    # 判断图片验证码是否过期，如果是None表示验证码没有或者已经过期
    if real_image_code is None:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码失效")

    # 删除redis中的图片验证码。防止用户使用同一个图片验证码验证多次邮箱，这样就会通过不断的判断邮箱号来确认是否注册，会有暴露邮箱号的风险
    try:
        redis_store.delete("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        # 这一行就不用再加上退出了

    # 用redis数据库的图片验证码real_image_code与用户填写的由前端传过来的验证码image_code进行比较，不相等表示用户填写错误
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误啦！")

    #  判断邮箱号是否已经存在于redis数据库中，在60秒内有没有操作过，能获取到的话，就是认为用户操作频繁
    try:
        # send_flag = redis_store.get("send_sms_code_%s" % email)
        send_flag = redis_store.get("send_sms_code_%s" % email)
    except Exception as e:
        current_app.logger.error(e)
    else:  # else语句的作用是：当try的代码块中，没有出现异常时执行else。出现异常时，不执行else
        # 表示在60秒内有发送过的记录
        if send_flag is not None:
            return jsonify(errno=RET.REQERR, errmsg="请求过于频繁，请60秒后再重试哦")

    # 判断邮箱号是否已经存在于mysql数据库中,就是是否已经注册，查询到有值或为空值，就执行else语句。如果有值退出，没有值继续执行下面。
    try:
        user = User.query.filter_by(email=email).first()
    except Exception as e:
        current_app.logger.error(e)
        # 这里就不写return,不退出，假设查询是出错了，假定没有注册过，到提交时再去验证邮箱是否已经存在
    else:
        if user is not None:
            # 表示邮箱号已经存在
            return jsonify(errno=RET.DATAEXIST, errmsg="邮箱号已经存在")

    # 如果上面判断的邮箱号不存在,即是None或出错，去保存短信验证
    sms_code = "%06d" % random.randint(0, 999999)
    print("sms_code邮箱验证码:",sms_code)
    # 保存真实的邮箱验证码，后面进行提交时的比较
    try:
        # 保存 "sms_code_%s" % email，邮箱验证码的保存时间300秒
        redis_store.setex("sms_code_%s" % email, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存发送短信验证码历史记录信息，60秒后才可以重新发送,1是随意设置的值
        redis_store.setex("send_sms_code_%s" % email, constants.SEND_SMS_CODE_INTERVAL, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存邮箱验证码的redis数据库异常")

    # 发送邮箱验证码，不等待
    get_captcha.send_email(email, sms_code)
    return jsonify(errno=RET.OK, errmsg="发送成功")
