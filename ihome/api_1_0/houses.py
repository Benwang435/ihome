# coding:utf-8
import datetime
import json
import os

from . import api
from ihome.utils.commons import login_required
from flask import g, current_app, jsonify, request, session
from ihome import db, constants, redis_store
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import User, Area, House, Facility, HouseImage, Order


# 城区信息很多地方会访问，可设置缓存数据
# 可以放在磁盘里：area_li = None
# 或用redis存放(内存中，速度更快)
@api.route("/areas/")
def get_area_info():
    """获取城区信息"""
    # 首先试着从redis获取缓存城区的数据
    try:
        resp_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            # redis缓存有数据
            # print("城区的缓存内容：", resp_json)  # 显示b'{}'
            # h1 = str(resp_json, encoding='utf-8')
            # print(h1)
            current_app.logger.info("hit area info on redis")
            return resp_json, 200, {"Content-Type": "application/json"}

    # 查询数据库,读取城区信息
    try:
        area_li = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    area_dict_li = []
    # 把对象转换成字典（可在类对象,转换封装到类中）
    # print("area_li:", area_li)
    for area in area_li:
        # d = {
        #     "aid":area.id,
        #     "aname":area.name
        # }
        area_dict_li.append(area.to_dict())
    # 将数据转换为json字符串
    resp_dict = dict(errno=RET.OK, errmsg="OK", data=area_dict_li)
    resp_json = json.dumps(resp_dict)  # 没有使用jsonify
    # print("城区的resp_json:", resp_json)
    # 使用缓存，将数据保存到redis中(数据在redis中不会被修改)
    try:
        redis_store.setex("area_info", constants.AREA_INFO_REDIS_CACHE_EXPIRES, resp_json)
    except Exception as e:
        current_app.logger.error(e)

    return resp_json, 200, {"Content-Type": "application/json"}
    # return jsonify(errno=RET.OK,errmsg="ok", data=area_dict_li)


@api.route("/houses/info/", methods=["POST"])
@login_required
def get_house_info():
    """
    功能：保存房屋的基本信息

    前端发送过来的json数据是：
    {
        "title":"",
        "price":"",
        "area_id":"1",
        "address":"",
        "room_count":"",
        "acreage":"",
        "unit":"",
        "capacity":"",
        "beds":"",
        "deposit":"",
        "min_days":"",
        "max_days":"",
        "facility":["7","8"]
    }
    """
    # 获取数据
    user_id = g.user_id
    house_data = request.get_json()

    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋 床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数
    max_days = house_data.get("max_days")  # 最大入住天数

    # 校验参数
    if not all(
            [title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    # 判断金额是否正确
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误1")

    # 判断城区id是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    if area is None:
        return jsonify(errno=RET.NODATA, errmsg="城区信息有误")

    # 保存房屋信息
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )
    # 处理房屋的设施信息
    facility_ids = house_data.get("facility")
    # 如果用户勾选了这样的设施信息，再保存数据库
    if facility_ids:
        # print("facility_ids列表内容：",facility_ids)  # 有内容
        # ["7","8"]
        # select * from ih_facility_info where id in []
        try:
            # facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()  # in_函数存在吗？
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库异常1")
        if facilities:
            # 表示这个列表里有合法的设施数据
            # 保存设施数据
            house.facilities = facilities
            # print("house内容是：", house)
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    # 保存数据成功
    return jsonify(errno=RET.OK, errmsg="OK", data={"house_id": house.id})


@api.route("/houses/image/", methods=["POST"])
@login_required
def save_house_image():
    """保存房屋的图片

    参数: 图片 房屋的id
    """
    image_file = request.files.get("house_image")  # 接收文件用request.files
    house_id = request.form.get("house_id")  # 接收id或名称的  要用request.form

    if not all([image_file, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误2")

    # 判断house_id的正确性
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常2")
    if house is None:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 保存图片到七牛网站

    # image_data = image_file.read()
    try:
        file_name = storage(image_file)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="保存图片失败啦")

    # 保存图片到本地网站

    # 保存图片名称到mysql数据库中
    house_image = HouseImage(house_id=house_id, url=file_name)
    db.session.add(house_image)

    # 处理房屋(House)的主图片 添加主图片
    if not house.index_image_url:
        house.index_image_url = file_name
        db.session.add(house)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.roolback()
        return jsonify(errno=RET.DBERR, errmsg="保存图片数据异常")

    image_url = constants.IMG_URL_DOMAIN + file_name
    return jsonify(errno=RET.OK, errmsg="OK", data={"image_url": image_url})


@api.route("/user/houses/", methods=["GET"])
@login_required
def get_user_houses():
    """
    获取房东发布的房源信息条目
    """
    user_id = g.user_id
    try:
        # House.query.filter_by(user_id=user_id)  可以用这种方式查询
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取数据失败")

    # 将查询到的房屋信息转换为字典存放到列表中
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())
    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_list})


@api.route("/houses/index/", methods=["GET"])
def get_house_index():
    """获取 主页幻灯片 展示的房屋基本信息"""
    # 从缓存中尝试获取数据(主页幻灯片展示的房屋基本信息)
    try:
        # ret = redis_store.get("home_page_data").decode("utf-8")
        ret = redis_store.get("home_page_data")
        # ret = redis_store.get("home_page_data").decode()
        # 上面的后面要加这句.decode() ，就没有b''，从Redis取出的Sting都变成bytes格式!!!!
        # redis_store = redis.StrictRedis(host='127.0.0.1',
        # port=6379, decode_responses=True)  这个ecode_responses=True试过不好使
        # 这样就没有b了，注意str(url, encoding='utf-8'
        # ret = json.loads(ret)
        # for data in ret:
        #     print(data["title"])
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    # rets = json.loads(ret)
    # for data in ret:
    #     print(data["title"])
    # print("缓存中的主页幻灯片展示的房屋基本信息: ",rets)
    if ret:
        current_app.logger.info("hit house info on redis")
        # 因为redis中保存的是json字符串，所以直接进行字符串拼接返回
        return '{"errno":0, "errmsg":"OK", "data":%s}' % ret, 200, {"Content-Type": "application/json"}
    else:
        try:
            # 查询数据库，返回房屋订单数目最多的5条数据
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

        if not houses:
            return jsonify(errno=RET.NODATA, errmsg="查询无数据")

        houses_list = []
        for house in houses:
            # 如果房屋未设置主图片，则跳过,continue继续
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())

        # 将数据转换为json，并保存到redis缓存
        json_houses = json.dumps(houses_list)  # "[{},{},{}]"
        try:
            redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            current_app.logger.error(e)

        # print("json_houses=home_page_data:",json_houses)  # 这个里面显示的是没有b''  ????

        return '{"errno":0, "errmsg":"OK", "data":%s}' % json_houses, 200, {"Content-Type": "application/json"}


@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """获取房屋详情页面信息"""
    # 前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示，
    # 所以需要后端返回登录用户的user_id
    # 尝试获取用户登录的信息，若登录，则返回给前端登录用户的user_id，否则返回user_id=-1
    user_id = session.get("user_id", "-1")

    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数缺失")

    # 先从redis缓存中获取房屋详情信息
    try:
        ret = redis_store.get("house_info_%s" % house_id)  # 要加上.decode() 终端显示会有问题???
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("hit house info on redis")
        return '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, ret), \
               200, {"Content-Type": "application/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 将房屋对象数据转换为字典
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据出错")

    # 存入到redis中
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_house)
    except Exception as e:
        current_app.logger.error(e)

    # 返回数据
    resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, json_house), \
           200, {"Content-Type": "application/json"}
    return resp


# GET /api/v1.0/houses?sd=2017-12-01&ed=2017-12-31&aid=10&sk=new&p=1
@api.route("/houses/")
def get_house_list():
    """获取房屋的列表信息页面（首页点击搜索的搜索页面）"""
    start_date = request.args.get("sd", "")  # 用户想要的起始时间
    end_date = request.args.get("ed", "")  # 用户想要的结束时间
    area_id = request.args.get("aid", "")  # 区域编号
    sort_key = request.args.get("sk", "new")  # 排序关键字  如果没有传就按默认值新旧来传
    page = request.args.get("p")  # 页数

    # 处理时间
    try:
        if start_date:
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期参数有误")

    # 判断区域id
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="区域参数有误")

    # 处理页数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1
    # 上面的参数都处理和判断并且都有了

    # 尝试获取redis缓存数据
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            return resp_json, 200, {"Content-Type": "application/json"}

    # 过滤条件参数的列表容器
    filter_params = []

    # 填充过滤参数
    # 时间条件
    conflict_orders = None

    try:
        if start_date and end_date:
            # 查询出冲突的订单
            conflict_orders = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            conflict_orders = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if conflict_orders:
        # 从订单中获取冲突的房屋id
        conflict_house_ids = [order.house_id for order in conflict_orders]
        # 如果冲突的房屋id不为空，向查询的参数中添加条件
        if conflict_orders:
            # filter_params.append([House.id.notin_(conflict_house_ids)])
            filter_params.append([House.id.not_in(conflict_house_ids)])

    # 查询筛选区域条件filter_params(下面的filter里用这个去解*filter_params)

    if area_id:
        # 其中的House.area_id == area_id不是判断结果为True，而是一种sqlalchemy的条件表达式，如果是python里比如a==1，是python自己
        # 实现的__eq__方法，sqlalchemy的__eq__双等号判断的逻辑方法自己去重新实现了。
        filter_params.append(House.area_id == area_id)

    # 查询数据库
    # 补充排序条件 只要不是前面的三种情况，都按新旧处理
    if sort_key == "booking":  # 入住最多
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == "price-inc":  # 按价格从低到高
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key == "price-des":  # 按价格从高到低
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:  # 新旧，只要不是前面的三种情况，都按新旧处理
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 处理分页
    try:
        # per_page每页显示两条 page页数  per_page每页显示条目数  error_out分页出错是否报错
        page_obj = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    # 获取页面数据
    house_li = page_obj.items
    houses = []
    for house in house_li:
        houses.append(house.to_basic_dict())

    # 获取总页数
    total_page = page_obj.pages

    resp_dict = dict(errno=RET.OK, errmsg="OK", data={"total_page": total_page, "houses": houses, "current_page": page})
    resp_json = json.dumps(resp_dict)

    if page <= total_page:
        # 设置缓存数据
        redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
        # 哈希类型
        try:
            # redis_store.hset(redis_key, page, resp_json)
            # redis_store.expire(redis_key, constants.HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES)
            # 创建redis管道对象，可以一次执行多个语句,然后一次性提交
            pipline = redis_store.pipeline()  # 命令的管道，不这样使用的话，上面注释的二条语句中。第一条失败了，但第二句执行后会永久有效
            # 开启多个语句的记录,
            pipline.multi()
            pipline.hset(redis_key, page, resp_json)
            pipline.expire(redis_key, constants.HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES)
            # 一次性执行多条语句
            pipline.execute()
        except Exception as e:
            current_app.logger.error(e)
    return resp_json, 200, {"Content-Type": "application/json"}

# redis_store
# redis缓存 “house_起始_结束_区域id_排序_页数”
# “house_起始_结束_区域id_排序“：hash
# {
#     "1":"{}",
#     "2":"{}",
# }
