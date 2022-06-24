# coding:utf-8
from . import api
from ihome.utils.commons import login_required
from flask import g, current_app, jsonify, request, session

from .. import db, constants
from ..utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import User


@api.route("/user/avatar/", methods=["POST"])
@login_required
def set_user_avatar():
    """设置用户的头像,即上传图片
    参数：图片（以多媒体表单），用户的id(g.user_id)
    """
    # 从登录装饰器的逻辑中已经把user_id保存到了g对象中，这里可以直接读取
    user_id = g.user_id
    # 获取图片
    image_file = request.files.get("avatar")
    if image_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg="未上传图片")
    # image_data = image_file.read()  # 先注释掉

    # 调用image_storage.py上传图片, 返回文件名
    try:
        filename = storage(image_file)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片失败!")
    # 保存文件名到ih_user_profile数据表中
    try:
        User.query.filter_by(id=user_id).update({"avatar_url": filename})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片信息失败")
    # 保存成功 返回
    avatar_url = constants.IMG_URL_DOMAIN + filename
    return jsonify(errno=RET.OK, errmsg="保存图片成功", data={"avatar_url": avatar_url})


# 获取用户名,修改用户名
@api.route("/users/name/", methods=["PUT"])
@login_required
def change_user_name():
    """修改用户名"""
    # 使用了login_required装饰器后，可以从g对象中获取用户user_id
    user_id = g.user_id

    # 获取用户想要设置的用户名
    req_data = request.get_json()  # 没有提示，但是有这个get_json()方法
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    name = req_data.get("name")  # 用户想要设置的名字
    if not name:
        return jsonify(errno=RET.PARAMERR, errmsg="名字不能为空")

    # 保存用户昵称name，并同时判断name是否重复（利用数据库的唯一索引)
    try:
        User.query.filter_by(id=user_id).update({"name": name})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="设置用户名错误")

    # 修改session数据中的name字段
    session["name"] = name
    return jsonify(errno=RET.OK, errmsg="OK", data={"name": name})


# 在页面加载时 向后端查询用户的信息
@api.route("/user/", methods=["GET"])
@login_required
def get_user_profile():
    """获取个人信息"""

    user_id = g.user_id
    # 查询数据库获取个人信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="无效操作")

    return jsonify(errno=RET.OK, errmsg="OK", data=user.to_dict())


# 获取用户的实名认证信息
@api.route("/users/auth/", methods=["GET"])
@login_required
def get_user_auth():
    """获取用户的实名认证信息"""
    user_id = g.user_id

    # 在user数据库表中查询信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户实名信息失败")

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="无效操作")

    return jsonify(errno=RET.OK, errmsg="OK", data=user.auth_to_dict())


# 保存用户实名认证信息
@api.route("/users/auth/", methods=["POST"])
@login_required
def set_user_auth():
    """保存实名认证信息"""
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    real_name = req_data.get("real_name")  # 真实姓名
    id_card = req_data.get("id_card")  # 身份证号

    # 参数校验
    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 保存用户的姓名与身份证号
    try:
        User.query.filter_by(id=user_id, real_name=None, id_card=None) \
            .update({"real_name": real_name, "id_card": id_card})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户实名信息失败")

    return jsonify(errno=RET.OK, errmsg="OK")
