# 导包 ，利用captcha 生成随机验证码
from io import BytesIO

from captcha.image import ImageCaptcha
from PIL import Image
import random
import time
import os


class Captcha:

    @staticmethod
    def instance():
        if not hasattr(Captcha, "_instance"):
            Captcha._instance = Captcha()
        return Captcha._instance

    # 定义随机方法
    def random_captcha(self):
        # 做一个容器
        captcha_text = []
        for i in range(4):
            # 定义验证码字符
            c = random.choice(
                ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])
            captcha_text.append(c)
        # 返回一个随机生成的字符串
        return ''.join(captcha_text)

    # 生成验证码方法
    def gen_captcha(self):
        # 定义图片对象
        image = ImageCaptcha(width=200, height=75)
        # 获取随机的四个字符串
        captcha_text = self.random_captcha()
        # 生成图像
        captcha_img = Image.open(image.generate(captcha_text))
        # name = str(int(random.randint(1, 99999)))  # 取一个随机名
        name = "%06d" % (random.randint(1, 99999))  # 取一个随机名6位
        # captcha_img.show()
        # print("类型：", type(captcha_img))
        bytesio = BytesIO()
        captcha_img.save(bytesio, format='jpeg')

        return name, captcha_text, bytesio.getvalue()


captcha = Captcha.instance()

if __name__ == '__main__':
    captcha = Captcha()
    name, text, img = captcha.gen_captcha()
    print("name,img,img::", name, text, img)
    print("img的类型:", type(img))
