import shutil
import subprocess
import httpx
import asyncio
import os
import requests
from subprocess import call
from retrying import retry
from fake_useragent import UserAgent
import zipfile
from PIL import Image
import base64
import cv2
import numpy as np
import io
import time
import csv


ua = UserAgent()
headers = {'user-agent': ua.random, 'Connection': 'close'}


# 处理列表空值
def list_index(li, li_index):
    try:
        return li[li_index]
    except:
        return None


# 异步下载图片
async def img_down(title, url, semaphore=10, path='imgs'):
    async with semaphore:
        illegal = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for i in illegal:
            title = title.replace(i, '-')
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                if not os.path.exists(path):
                    os.makedirs(path)
                else:
                    with open(f'{path}/{title}', 'wb') as f:
                        f.write(resp.content)
            elif resp.status_code != 404:
                raise Exception('ip异常，可能该加代理了')
            else:
                raise '响应码错误'


# 发送邮件
def email():
    msg = MIMEText('程序停止运行', 'plain', 'utf-8')
    from_addr = ''
    password = ''
    to_addr = ''
    smtp_server = 'smtp.qq.com'
    msg['From'] = Header(from_addr)
    msg['To'] = Header(to_addr)
    msg['Subject'] = Header('python test')
    server = smtplib.SMTP()
    server.connect(smtp_server, 25)
    server.login(from_addr, password)
    server.sendmail(from_addr, to_addr, msg.as_string())
    server.quit()


# 分片下载器
@retry(stop_max_attempt_number=3, wait_fixed=1000)
def download_source(url, output_path, chunk_size=5120):
    response = requests.get(url, stream=True, headers=headers)
    with open(output_path, mode='wb') as f:
        for chunk in response.iter_content(chunk_size):
            f.write(chunk)
    print(f'{output_path}--下载完成')


# IDM下载器
def idm_down(down_url, path, title, mode='a'):
    """
    路径一定要和文件名分开
    a--挂起，s--立即下载

    参数：
        /d URL - 下载一个文件，等等。
        /s - 开始任务调度里的队列
        /p 本地_路径 - 定义要保存的文件放在哪个本地路径
        /f 本地local_文件_名 - 定义要保存的文件到本地的文件名
        /q - IDM 将在成功下载之后退出。这个参数只为第一个副本工作
        /h - IDM 将在成功下载之后挂起您的连接
        /n - 当不要 IDM 询问任何问题时启用安静模式
        /a - 添加一个指定的文件 用 /d 到下载队列，但是不要开始下载
    """
    IDM = r'D:\工具\Internet Download Manager\IDMan.exe'
    if type(down_url) == list:
        for url in down_url:
            call([IDM, '/d', url, '/p', path, '/f', title, '/n', f'/{mode}'])
    else:
        call([IDM, '/d', down_url, '/p', path, '/f', title, '/n', f'/{mode}'])


# 改图片分辨率
def ResizeImage(filein, fileout, scale=4):
    """
    改变图片大小
    :param filein: 输入图片
    :param fileout: 输出图片
    :param width: 输出图片宽度
    :param height: 输出图片宽度
    :param type: 输出图片类型（png, gif, jpeg...）
    :return:
    """
    img = Image.open(filein)
    width = int(img.size[0] * scale)
    height = int(img.size[1] * scale)
    type = img.format
    out = img.resize((width, height), Image.ANTIALIAS)
    # 第二个参数：
    # Image.NEAREST ：低质量
    # Image.BILINEAR：双线性
    # Image.BICUBIC ：三次样条插值
    # Image.ANTIALIAS：高质量
    out.save(fileout, type, dpi=(600.0, 600.0))


# 压缩文件夹
def getZipDir(dirpath, outFullName):
    """
    压缩指定文件夹
    :param dirpath: 目标文件夹路径
    :param outFullName: 压缩文件保存路径+xxxx.zip
    :return: 无
    """
    l = os.listdir(dirpath)
    if len(l) == 0:
        raise '文件为空'
    else:
        # zip = zipfile.ZipFile(outFullName, "w", zipfile.ZIP_DEFLATED)
        # for path, dirnames, filenames in os.walk(dirpath):
        #     # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        #     fpath = path.replace(dirpath, '')
        #     for filename in filenames:
        #         zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
        # zip.close()
        # call(fr'bz.exe c {dirpath}.zip {dirpath}', stdout=open('log.txt', 'a'), shell=True)
        call(fr'bz.exe c {dirpath}.zip {dirpath}', stdout=open('log.txt', 'a'), shell=True)
        try:
            shutil.rmtree(dirpath)
        except Exception as e:
            print('删除时出错')
            print(e)


# 图片Base64标准解码, 返回图片
def b64decode(imgString):
    imgByte = base64.standard_b64decode(imgString)
    return imgByte


# X坐标缺口检测
def detectDistanceX(imgSlider, imgBackground):
    imgSliderGray = cv2.cvtColor(np.array(Image.open(io.BytesIO(imgSlider))), cv2.COLOR_BGR2GRAY)
    imgBackgroundGray = cv2.cvtColor(np.array(Image.open(io.BytesIO(imgBackground))), cv2.COLOR_BGR2GRAY)

    # 寻找最佳匹配
    res = cv2.matchTemplate(_tran_canny(imgSliderGray), _tran_canny(imgBackgroundGray),
                            cv2.TM_CCOEFF_NORMED)
    # 最小值，最大值，并得到最小值, 最大值的索引
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    return max_loc[0]


def _tran_canny(image):
    """消除噪声"""
    image = cv2.GaussianBlur(image, (3, 3), 0)
    return cv2.Canny(image, 100, 200)


# 规范文件名
def set_file_name(file_name):
    illegal_char = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for char in illegal_char:
        file_name = file_name.replace(char, '-')
    return file_name


# 创建文件夹，去除不规范的字符
def set_file_folder(file_name):
    file_name = set_file_name(file_name)
    if not os.path.exists(file_name):
        os.mkdir(file_name)
        print(file_name + '----创建成功！')
        return file_name
    else:
        print(file_name + '----已创建！')
        return False


# 时间戳转换
def timeStamp(timeNum):
    if len(str(timeNum)) == 13:
        timeNum = float(timeNum/1000)
    time_local = time.localtime(timeNum)
    dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    return dt


# csv写入表头
def csv_write(file_name, header, data):
    with open(f"{file_name}.csv", "a", encoding='utf-8', newline="") as f:
        k = csv.writer(f, dialect="excel")
        with open(f"{file_name}.csv", "r", encoding='utf-8', newline="") as f:
            reader = csv.reader(f)
            if not [row for row in reader]:
                k.writerow(header)
                k.writerows(data)
            else:
                k.writerows(data)


