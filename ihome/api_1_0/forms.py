#!/usr/bin/env python3
# coding:utf-8
from flask_wtf import FlaskForm

import wtforms
from wtforms.validators import DataRequired, Email, InputRequired, Length, EqualTo, NumberRange, Regexp, URL, UUID


class RegistForm(FlaskForm):
    """ 注册参数验证 """
    # form表单中参数的name属性值常用如下：
    # username = StringField(validators=[Length(3, 10, message='用户名长度为3~10位')])
    email_s = wtforms.StringField(validators=[Email(message='非邮箱格式!')])
    # password = wtforms.StringField(validators=[InputRequired(message='密码必传'), Length(6, 10, message='密码长度为6~10位')])
    # check_password = wtforms.StringField(validators=[Length(6, 10, message='密码长度为6~10位'), EqualTo('password', message='两次密码不一致')])
    # age = wtforms.IntegerField(validators=[NumberRange(18, 50, message='年龄需为18~50岁')])
    # phone = wtforms.StringField(validators=[Regexp(r'1[34578]\d{9}', message='手机号格式错误')])
    # home_page = wtforms.StringField(validators=[URL(message='home_page必须为url格式')])
    # uuid = wtforms.StringField(validators=[UUID(message='uuid格式错误')])


class LoginForm(FlaskForm):
    email_s = wtforms.EmailField(validators=[DataRequired(), Email(message='邮箱格式错误!')])


"""
示例：
@app.route('/regist/', methods=['GET', 'POST'])
def regist():
    form = RegistForm(request.form)
    if request.method == 'POST':
        if form.validate():
            return '验证通过'
        else:
            print(form.errors)
            return form.errors
    return render_template('regist.html')
"""
