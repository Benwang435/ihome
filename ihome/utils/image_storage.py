# -*- coding: utf-8 -*-
import io

from PIL import Image
import pypinyin
from werkzeug.utils import secure_filename
import os
from ihome.utils.strUtil import Pic_str

UPLOAD_FOLDER = '../static/upload/'  # 设置保存上传文件的目录
basedir = os.path.abspath(os.path.dirname(__file__))  # image_storage.py文件所在的目录
ALLOWED_EXTENSIONS = {'png', 'jpg', 'JPG', 'PNG', 'gif', 'GIF', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def storage(file_name):  # 改成在本地保存的图片文件
    """保存图片的函数"""
    file_dir = os.path.join(basedir, UPLOAD_FOLDER)  # 保存图片所在的目录
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    # 判断文件名是否为空并且文件名的后缀是否在允许的列表内
    if file_name and allowed_file(file_name.filename):
        # fname = secure_filename(f.filename)  # 使用secure_filename来验证文件名的安全性,对中文不能验证,因此使用下面方式
        # 使用secure_filename并使用pingyi把汉字转换成拼音
        fname = secure_filename(''.join(pypinyin.lazy_pinyin(file_name.filename)))
        # 以点分割，最多分割一次,取后面扩展名
        ext = fname.rsplit('.', 1)[1]
        # 拼接成新的文件名
        new_filename = Pic_str().create_uuid() + '.' + ext
        file_name.save(os.path.join(file_dir, new_filename))
        return new_filename  # 返回文件名称
    else:
        # return jsonify({"error": 1001, "msg": "图片上传失败"})
        return "image_storage.py这个文件在图片上传时，失败！"

