from flask import Blueprint

# from . import demo 这样的导入不能放在上面,要先创建蓝图之后 再导入，让蓝图知道有视图demo等py文件的存在
# 创建蓝图对象 取一个蓝图名称api_1_0,在ihome目录的初始化文件__init__.py里注册蓝图
# 如这样的：app.register_blueprint(api_1_0.api, url_prefix="/api/v1.0")

# 创建蓝图对象
api = Blueprint("api_1_0", __name__)

# 导入蓝图的视图
from ihome.api_1_0 import demo, houses, orders, passport, pay, profile, verify_code
