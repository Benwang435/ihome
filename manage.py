# -*- coding: utf-8 -*-
# 运行：
# python manage.py db migrate -m 'db tables
# python manage.py runserver -r -d
# from flask._compat import text_type出错，降低flask版本：pip3 install flask==1.1.2
"""
不用降低版本，修改flask_script 文件就可以
It happened because the python searched on Flask._compat directory and It isn't there, so I changed like on below : (on flask_script/__init__.py)
Where:
from ._compat import text_type on original flask-script file
to :
from flask_script._compat import text_type
"""
# ImportError: cannot import name 'MigrateCommand' from 'flask_migrate'
# 上面的 把flask_migrate降低一个版本 Flask-Migrate==1.2.0
"""
可以不降级flask_migrate  直接在执行python的命令行中输入   export FLASK_APP=manager.py
再执行flask db init 等操作

"""
from ihome import create_app, db
from flask_script import Manager
# from flask_migrate import Migrate, MigrateCommand  版本低了
from flask_migrate import Migrate
app = create_app("develop")
manager = Manager(app)
migrate = Migrate(app, db)

# manage.add_command("db", MigrateCommand)  # 原来版本低了
manager.add_command("db", Manager)  # 可以直接使用flask_script的Manager,原来的地方修改一下导入的类

if __name__ == '__main__':
    # app.run()
    manager.run()


# 1 分析需求
# 2 编写代码
# 3 编写单元测试
# 4 自测
# 5 编写接口文档（验证码接口文档为例）：
#   (1)接口名字，(2)功能描述，(3)url-/api/v1.0/image_codes/<image_code_id>,(4)请求方式-GET，（5）传入参数，（6）返回值
#
#   传入参数(格式-字符串、表单、json、xml），返回值
#   名字              类型      是否必须    说明
#   image_code_id   字符串      是        验证码图片的编号

#   返回值：格式：正常（图片） 异常（Json)
#   名字     类型      是否必传   说明
#   errno   字符串     否       错误代码
#   errmsg  字符串     否       错误代码
#
#   示例：
#   '{"errno":"4001","errmsg":"保存图片验证码失败"}'

# 6 提测代码

# 发送短信服务: 容联云  云通讯
