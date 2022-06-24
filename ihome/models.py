# coding:utf-8
from datetime import datetime

from flask import current_app

from ihome import db
from werkzeug.security import generate_password_hash, check_password_hash
from ihome import constants
import jwt  # pip install pyjwt


# # 在这个models.py里创建类并映射到数据库中去,为数据库创建表
# from flask_sqlalchemy import SQLAlchemy
# # 如果已经安装了mysqlclient不用导入下面已经注释的两条语句了
# import pymysql
#
# pymysql.install_as_MySQLdb()
#
# from flask import Flask
#
# app = Flask(__name__)
#
#
# class Config:
#     SQLALCHEMY_DATABASE_URI = 'mysql://root:root1002@127.0.0.1:3307/ihome'
#     # 指定让SQLAlchemy 自动追踪程序的修改，会占用很多内存，建议不写。设置成 True (是默认情况)
#     SQLALCHEMY_TRACK_MODIFICATIONS = True  # 也可用db.session.flush()在下面添加.查询和提交会自动执行刷新(flush())
#     # 可以让程序不再使用db.session.commit()来提交，最好不用自动提交，设置为False，已经废弃！
#     # SQLALCHEMY_COMMIT_ON_TEARDOWN = True
#     # 查询时，会显示原始的sql语句，在终端。
#     SQLALCHEMY_ECHO = True
#
#
# app.config.from_object(Config)
# db = SQLAlchemy(app)


class BaseModel(object):
    """模型基类，为每个模型补充创建时间与更新时间"""

    create_time = db.Column(db.DateTime, default=datetime.now)  # 记录的创建时间
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 记录的更新时间


class User(BaseModel, db.Model):
    """用户"""
    __tablename__ = "ih_user_profile"  # 数据库前缀作为表名的前缘
    id = db.Column(db.Integer, primary_key=True)  # 用户编号，默认是自增的
    name = db.Column(db.String(32), unique=True, nullable=False)  # 用户暱称
    password_hash = db.Column(db.String(128), nullable=False)  # 加密的密码
    email = db.Column(db.String(32), unique=True, nullable=False)  # 原来是手机号String(11)的
    real_name = db.Column(db.String(32))  # 真实姓名
    id_card = db.Column(db.String(20))  # 身份证号码
    avatar_url = db.Column(db.String(128))  # 用户头像路径
    houses = db.relationship("House", backref="user", lazy='dynamic')  # 反向引用用户发布的房屋表
    orders = db.relationship("Order", backref="user", lazy='dynamic')  # 反向引用用户下的订单表

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.name

    # def generate_reset_password_token(self):
    #     data = jwt.encode({id: self.id}, current_app.config["SECRET_KEY"], algorithm='H256')
    #     return data
    #
    # def check_reset_password(self, token):
    #     try:
    #         data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithm='H256')
    #         return User.query.filter_by(id=data['id']).first()
    #     except Exception as e:
    #         print(e)
    #         return

    # 加上property装饰器后，会把函数变为属性，属性名即为函数名
    @property
    def password(self):
        """读取属性的函数行为"""
        # print(user.password)  # 读取属性时被调用
        # 函数的返回值会作为属性值
        # return "xxxx"
        raise AttributeError("这个属性只能设置，不能读取")

    # 使用这个装饰器, 对应设置属性操作,把密码加密
    @password.setter
    def password(self, value):
        """
        设置属性  user.passord = "xxxxx"
        :param value: 设置属性时的数据 value就是"xxxxx", 原始的明文密码
        :return:
        """
        self.password_hash = generate_password_hash(value)

    # def generate_password_hash(self, origin_password):
    #     """对密码进行加密"""
    #     self.password_hash = generate_password_hash(origin_password)

    def check_password(self, passwd):
        """
        检验密码的正确性
        :param passwd:  用户登录时填写的原始密码
        :return: 如果正确，返回True， 否则返回False
        """
        return check_password_hash(self.password_hash, passwd)

    def to_dict(self):
        """将对象转换为字典数据"""
        user_dict = {
            "user_id": self.id,
            "name": self.name,
            "email": self.email,
            "avatar": constants.IMG_URL_DOMAIN + self.avatar_url if self.avatar_url else "",
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        return user_dict

    def auth_to_dict(self):
        """将实名信息转换为字典数据"""
        auth_dict = {
            "user_id": self.id,
            "real_name": self.real_name,
            "id_card": self.id_card
        }
        return auth_dict


class Area(BaseModel, db.Model):
    """城区"""
    __tablename__ = "ih_area_info"
    id = db.Column(db.Integer, primary_key=True)  # 区域编号
    name = db.Column(db.String(32), nullable=False)  # 区域名字
    houses = db.relationship("House", backref="area", lazy='dynamic')  # 区域的房屋

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        """将对象转换为字典"""
        d = {
            "aid": self.id,
            "aname": self.name
        }
        return d


# 房屋设施表,第三张表，建立下面 房屋House与设施Facility 的多对多关系, 第三张表不需要通过模型类的方式创建，因为基础上操作不到第三张表，
# 可以直接使用最低层的方式,即通过sqlalchemy来构建表，如下 db.Table，并且下面的两个字段都设置为主键，即联合主键。
house_facility = db.Table(
    "ih_house_facility",
    db.Column("house_id", db.Integer, db.ForeignKey("ih_house_info.id"), primary_key=True),  # 房屋编号
    db.Column("facility_id", db.Integer, db.ForeignKey("ih_facility_info.id"), primary_key=True)  # 设施编号
)


class House(BaseModel, db.Model):
    """房屋信息"""

    __tablename__ = "ih_house_info"

    id = db.Column(db.Integer, primary_key=True)  # 房屋编号
    user_id = db.Column(db.Integer, db.ForeignKey("ih_user_profile.id"), nullable=False)  # 房屋主人的用户编号
    area_id = db.Column(db.Integer, db.ForeignKey("ih_area_info.id"), nullable=False)  # 归属地的区域编号
    title = db.Column(db.String(64), nullable=False)  # 标题
    price = db.Column(db.Integer, default=0)  # 单价，单位：分
    address = db.Column(db.String(512), default="")  # 地址
    room_count = db.Column(db.Integer, default=1)  # 房间数目
    acreage = db.Column(db.Integer, default=0)  # 房屋面积
    unit = db.Column(db.String(32), default="")  # 房屋单元， 如几室几厅
    capacity = db.Column(db.Integer, default=1)  # 房屋容纳的人数
    beds = db.Column(db.String(64), default="")  # 房屋床铺的配置
    deposit = db.Column(db.Integer, default=0)  # 房屋押金
    min_days = db.Column(db.Integer, default=1)  # 最少入住天数
    max_days = db.Column(db.Integer, default=0)  # 最多入住天数，0表示不限制
    order_count = db.Column(db.Integer, default=0)  # 预订完成的该房屋的订单数
    index_image_url = db.Column(db.String(256), default="")  # 房屋主图片的路径,在首页显示的图片
    # facilities = db.relationship("Facility", secondary=house_facility)  # 房屋的设施
    facilities = db.relationship("Facility",
                                 secondary=house_facility,
                                 lazy="dynamic",
                                 backref=db.backref(
                                     "ih_house_info",
                                     lazy="dynamic")
                                 )  # 房屋的设施
    images = db.relationship("HouseImage")  # 房屋的图片
    orders = db.relationship("Order", backref="house", lazy='dynamic')  # 房屋的订单

    def to_basic_dict(self):
        """将基本信息转换为字典数据"""
        house_dict = {
            "house_id": self.id,
            "title": self.title,
            "price": self.price,
            "area_name": self.area.name,
            "img_url": constants.IMG_URL_DOMAIN + self.index_image_url if self.index_image_url else "",
            "room_count": self.room_count,
            "order_count": self.order_count,
            "address": self.address,
            "user_avatar": constants.IMG_URL_DOMAIN + self.user.avatar_url if self.user.avatar_url else "",
            "ctime": self.create_time.strftime("%Y-%m-%d")
        }
        return house_dict

    def to_full_dict(self):
        """将详细信息转换为字典数据"""
        house_dict = {
            "hid": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name,
            "user_avatar": constants.IMG_URL_DOMAIN + self.user.avatar_url if self.user.avatar_url else "",
            "title": self.title,
            "price": self.price,
            "address": self.address,
            "room_count": self.room_count,
            "acreage": self.acreage,
            "unit": self.unit,
            "capacity": self.capacity,
            "beds": self.beds,
            "deposit": self.deposit,
            "min_days": self.min_days,
            "max_days": self.max_days,
        }

        # 房屋图片
        img_urls = []
        for image in self.images:
            img_urls.append(constants.IMG_URL_DOMAIN + image.url)
        house_dict["img_urls"] = img_urls

        # 房屋设施
        facilities = []
        for facility in self.facilities:
            facilities.append(facility.id)
        house_dict["facilities"] = facilities

        # 评论信息
        comments = []
        orders = Order.query.filter(Order.house_id == self.id, Order.status == "COMPLETE", Order.comment != None) \
            .order_by(Order.update_time.desc()).limit(constants.HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS)
        for order in orders:
            comment = {
                "comment": order.comment,  # 评论的内容
                "user_name": order.user.name if order.user.name != order.user.email else "匿名用户",  # 发表评论的用户
                "ctime": order.update_time.strftime("%Y-%m-%d %H:%M:%S")  # 评价的时间
            }
            comments.append(comment)
        house_dict["comments"] = comments
        return house_dict


class Facility(BaseModel, db.Model):
    """设施信息"""

    __tablename__ = "ih_facility_info"

    id = db.Column(db.Integer, primary_key=True)  # 设施编号
    name = db.Column(db.String(32), nullable=False)  # 设施名字


class HouseImage(BaseModel, db.Model):
    """房屋图片类"""

    __tablename__ = "ih_house_image"

    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey("ih_house_info.id"), nullable=False)  # 房屋编号
    url = db.Column(db.String(256), nullable=False)  # 图片的路径


class Order(BaseModel, db.Model):
    """订单"""

    __tablename__ = "ih_order_info"

    id = db.Column(db.Integer, primary_key=True)  # 订单编号
    user_id = db.Column(db.Integer, db.ForeignKey("ih_user_profile.id"), nullable=False)  # 下订单的用户编号
    house_id = db.Column(db.Integer, db.ForeignKey("ih_house_info.id"), nullable=False)  # 预订的房间编号
    begin_date = db.Column(db.DateTime, nullable=False)  # 预订的起始时间
    end_date = db.Column(db.DateTime, nullable=False)  # 预订的结束时间
    days = db.Column(db.Integer, nullable=False)  # 预订的总天数
    house_price = db.Column(db.Integer, nullable=False)  # 房屋的单价
    amount = db.Column(db.Integer, nullable=False)  # 订单的总金额
    status = db.Column(  # 订单的状态
        db.Enum(  # 枚举     # django choice
            "WAIT_ACCEPT",  # 待接单,
            "WAIT_PAYMENT",  # 待支付
            "PAID",  # 已支付
            "WAIT_COMMENT",  # 待评价
            "COMPLETE",  # 已完成
            "CANCELED",  # 已取消
            "REJECTED"  # 已拒单
        ),
        default="WAIT_ACCEPT", index=True)  # 指明在mysql中这个字段建立索引，加快查询速度
    comment = db.Column(db.Text)  # 订单的评论信息或者拒单原因
    trade_no = db.Column(db.String(128))  # 交易的流水号 支付宝的

    def to_dict(self):
        """将订单信息转换为字典数据"""
        order_dict = {
            "order_id": self.id,
            "title": self.house.title,
            "img_url": constants.IMG_URL_DOMAIN + self.house.index_image_url if self.house.index_image_url else "",
            "start_date": self.begin_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "ctime": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "days": self.days,
            "amount": self.amount,
            "status": self.status,
            "comment": self.comment if self.comment else ""
        }
        return order_dict

# if __name__ == '__main__':
#
#     # # db.create_all()  # 创建所有的表
#
#     # 添加记录
#     area1 = Area(name="张三")
#     area2 = Area(name="李四")
#     area3 = Area("王五")
#     db.session.add_all([area1, area2, area3])
#     db.session.commit()

# 删除单条记录
# area = db.session.query(Area).filter(name="张三").first() # 查询到的单条记录
# db.session.query(Area).filter_by(name="王五").delete()
# db.session.commit()

# # 删除多条记录
# area = db.session.query(Area).all()
# print("area对象-------------：", area)
# # area = Area.query.get(7)
# for i in area:
#     db.session.delete(i)
# db.session.commit()
