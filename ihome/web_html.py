# coding:utf-8
from flask import Blueprint, current_app, make_response
from flask_wtf import csrf
# 创建静态文件的蓝图对象
html = Blueprint("web_html", __name__)


# 127.0.0.:5000/
# 127.0.0.:5000/index.html
# 127.0.0.:5000/register.html
# 127.0.0.:5000/favicon.ico 网站标识 浏览器会自己请示这个资源

@html.route("/<re(r'.*'):html_file_name>")
def get_html(html_file_name):
    """提供html文件"""
    # 如果file_name为空，即“”，表示访问是路径是/  请求的是主页，html_file_name再和下面拼接起来。
    if not html_file_name:
        html_file_name = "index.html"
    # 如果资源名称不是favicon.ico，这个文件是在static目录下.
    if html_file_name != "favicon.ico":
        html_file_name = "html/" + html_file_name

    # 创建生成一个csrf_token值，在web_html.py中生成csrf的同时也保存一份到了session中，generate_csrf源码中可以看到.
    # 前端方面，只关心是不是post put delete，如果是这些就要带到csrf
    csrf_token = csrf.generate_csrf()
    """flask提供的返回静态文件的send_static_file方法"""
    resp = make_response(current_app.send_static_file(html_file_name))

    # 设置cookie值 没有设置有效期，关闭浏览器会自动失效
    resp.set_cookie("csrf_token", csrf_token)
    return resp
"""
csrf_token=ImVlN2VlODVjYjEyMzQwNzBlYTMwZGNjMTcyMzI2ZDZhYjQ1YjVmZDQi.YR9B3w.xaBUzL30Ca28nfwDCmq5IjxedoA; session=2d911226-823e-4153-aff2-e03b1419ce09.oOk7xoRmxAuA1X71v82LGfeYZkE
           ImVlN2VlODVjYjEyMzQwNzBlYTMwZGNjMTcyMzI2ZDZhYjQ1YjVmZDQi.YR9B3w.xaBUzL30Ca28nfwDCmq5IjxedoA
                                                                                                                2d911226-823e-4153-aff2-e03b1419ce09.oOk7xoRmxAuA1X71v82LGfeYZkE
"""