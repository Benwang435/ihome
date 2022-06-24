# coding:utf-8
# 使用github第三库的支付宝sdk(软件开发包software developer's kit)
# pip install python-alipay-sdk
# 命令行生成密钥(在支付宝上复制的公钥在本地作为文件使用时，在首尾要加上---begin...---END...这样的标记)：
# openssl  现成的命令
# genrsa -out app_private_key.pem 2048  生成私钥，其中2048是使用rsa2
# rsa -in app_private_key.pem -pubout -out app_public_key.pem 导出公钥,复制在支付宝网站上
# 买家账号 msusvy4802@sandbox.com 登录支付宝沙箱环境去查询
"""
python3使用python-alipay-sdk对接支付宝的时候，可能会出现以下error
不支持RSA**格式,解决办法:把公钥和私钥的内容先读出来，然后再用读出来的内容去创建Alipay对象
"""
from ihome.api_1_0 import api
from ihome.utils.commons import login_required
from ihome.models import Order
from flask import g, current_app, jsonify, request
from ihome.utils.response_code import RET
from ihome import constants, db

from alipay import AliPayConfig, AliPay
import os

# app_private_key = open("ihome/api_1_0/keys/app_private_key_pem").read()  # 只放入生成的私钥，与放在支付宝上的公钥对应
# alipay_public_key = open("ihome/api_1_0/keys/alipay_public_key_pem").read()  # 这是支付宝网站上的支付宝公钥，复制下来加上begin,end

app_private_key = open(
    os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem")).read()  # 只放入生成的私钥，与放在支付宝上的公钥对应
alipay_public_key = open(
    os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem")).read()  # 这是支付宝网站上的支付宝公钥，复制下来加上begin,end


@api.route("/orders/<int:order_id>/payment/", methods=["POST"])
@login_required
def order_pay(order_id):
    """发起支付宝支付"""
    user_id = g.user_id
    # 判断订单状态
    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id,
                                   Order.status == "WAIT_PAYMENT").first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    if order is None:
        return jsonify(errno=RET.NODATA, errmsg="订单数据有误")
    # 创建支付宝sdk的工具对象
    alipay_client = AliPay(
        appid="2021000118611984",  # appid:2021000118611984
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key,  # 私钥
        alipay_public_key_string=alipay_public_key,  #
        # 上面的是支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type="RSA2",  # RSA 或者 RSA2,之前生成的是 2048是rsa2
        debug=True,  # 默认False
        verbose=True,  # 输出调试数据
        config=AliPayConfig(timeout=15)
    )
    """
    alipay = AliPay(
    appid="",
    app_notify_url=None,  # 默认回调 url
    app_private_key_string=app_private_key_string,
    # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
    alipay_public_key_string=alipay_public_key_string,
    sign_type="RSA",  # RSA 或者 RSA2
    debug=False,  # 默认 False
    verbose=False,  # 输出调试数据
    config=AliPayConfig(timeout=15)  # 可选，请求超时时间
)
    """

    # 手机网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
    order_string = alipay_client.api_alipay_trade_wap_pay(
        out_trade_no=order.id,  # 订单编号
        total_amount=str(order.amount / 100.0),  # 总金额
        subject="爱家租房 %s" % order.id,  # 订单标题
        return_url="http://127.0.0.1:5000/payComplete.html",  # 返回的连接地址
        notify_url=None  # 可选, 不填则使用默认notify url
    )
    print("order_string订单字符串**********：", order_string)
    # 构建让用户跳转的支付连接地址
    # pay_url = constants.ALIPAY_URL_PREFIX + order_string
    # print("返回的网址是：===================", pay_url)

    # 电脑网站支付，需要跳转到：https://openapi.alipay.com/gateway.do? + order_string
    # order_string = alipay_client.api_alipay_trade_page_pay(
    #     out_trade_no=order.id,
    #     total_amount=str(order.amount / 100.0),
    #     subject="爱家租房 %s" % order.id,
    #     return_url="http://127.0.0.1:5000/payComplete.html",
    #     notify_url=None  # 可选，不填则使用默认 notify url
    # )

    pay_url = constants.ALIPAY_URL_PREFIX + order_string

    return jsonify(errno=RET.OK, errmsg="OK", data={"pay_url": pay_url})


@api.route("/order/payment", methods=["PUT"])
def save_order_payment_result():
    """保存订单支付结果"""
    alipay_dict = request.form.to_dict()
    print('alipay_dict************', alipay_dict)

    # 对支付宝的传过来的数据进行分离  提取出支付宝的签名参数sign 和剩下的其他数据
    alipay_sign = alipay_dict.pop("sign")

    # 创建支付宝sdk的工具对象
    alipay_client = AliPay(
        appid="2021000118611984",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key,  # 私钥
        alipay_public_key_string=alipay_public_key,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True,  # 默认False
        verbose=True,  # 输出调试数据
        config=AliPayConfig(timeout=15)
    )

    # 借助工具验证参数的合法性
    # 如果确定参数是支付宝的，返回True，否则返回false
    result = alipay_client.verify(alipay_dict, alipay_sign)

    if result:
        # 修改数据库的订单状态信息
        order_id = alipay_dict.get("out_trade_no")
        trade_no = alipay_dict.get("trade_no")  # 支付宝的交易号
        try:
            Order.query.filter_by(id=order_id).update({"status": "WAIT_COMMENT", "trade_no": trade_no})
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()

    return jsonify(errno=RET.OK, errmsg="OK")