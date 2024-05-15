# -*- coding: UTF-8 -*-
import requests
import json
import re
import time
import csv
import datetime
import multiprocessing
import os

# -----房价爬取部分-----
# 爬取房价并且返回一个页面的字典
def get_housing_price(url):
    url = str(url)
    html = requests.get(url).text  # 获取页面原代码
    # 正则表达式
    # 小区名
    name_rule = r'lianjia.com/xiaoqu/[0-9]*/" target="_blank">(.*?)</a>'  # [0-9]* 表示任意多个数字     .*? 匹配一次
    name = re.findall(name_rule, html)
    # 房价
    price_rule = r'<div class="totalPrice"><span>(.*?)</span>'
    price = re.findall(price_rule, html)
    # 小区所在区域
    district_rule = r'class="district" title=".*?">(.*?)</a>'
    district = re.findall(district_rule, html)
    # 小区所在商圈
    bizcircle_rule = r'class="bizcircle" title=".*?">(.*?)</a>&nbsp'
    bizcircle = re.findall(bizcircle_rule, html)
    # 建立小区名和房价对应的字典
    housing_price_dict = {}
    if len(name) == len(price) == len(district) == len(bizcircle):
        for i in range(len(name)):
            infor = []  # 存放信息的列表
            if price[i] != '暂无':  # 因为存在暂无，把除了暂无房价数据以外的房价变成浮点型
                floated = float(price[i])
            else:
                floated = '暂无'
            infor.append(name[i])
            infor.append(district[i])
            infor.append(bizcircle[i])
            infor.append(floated)
            housing_price_dict[str(url) + '-' + str(i) + '-' + name[i]] = infor  # 遍历生成键值
    else:
        print('参数匹配失败')
    return housing_price_dict


# 合并字典
def merge_dict(dict1, dict2):
    merged = {**dict1, **dict2}
    return merged


# 整合房价字典
def merge_price_dict(url, pagekey, PageStart, PageEnd):
    initial = {}
    for pg in range(PageStart, PageEnd + 1):  # 设置起始和中止界面
        url_new = str(url) + '/pg' + str(pg) + pagekey  # 翻页
        prices = get_housing_price(url_new)
        time.sleep(5)
        print("线程：", os.getpid(), f'====正在获取第 {pg} 页房价数据====')
        initial = merge_dict(initial, prices)
    return initial

# 获取房价数据并写入json文件
def writer_in_json(url, pgkey, PageStart, PageEnd, json_name):
    data = merge_price_dict(url, pgkey, PageStart, PageEnd)
    count = 1
    with open(json_name, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)  # 写为多行

    if count % 10 == 0:
        print("线程：", os.getpid(), f'====正在写入第 {count} 条房价数据====')
    count += 1

    print("线程：", os.getpid(), '数据写入完成')


# -----POI数据获取部分-----
# 获取POI数据
def get_POI(Keyword, City, ak):
    # 高德地图api   https://lbs.amap.com/
    url = f'https://restapi.amap.com/v3/geocode/geo?key={ak}&address={Keyword}&city={City}'
    html = requests.get(url)  # 获取网页信息
    data = html.json()  # 获取网页信息的json格式数据
    item = data['geocodes'][0]  # 读取reults里第一个元素，可能是最匹配的
    Name = item['formatted_address']    # 全名
    City = item['city'] # 城市
    Area = item['district'] # 区
    Region = City + Area    # 城市+区
    ######获取经纬度#####
    location = item['location']
    mid = location.split(',')   # 以","分割开经纬度
    Longitude = mid[0]  # 经度
    Latitude = mid[1]  # 纬度
    return Name, Region, Longitude, Latitude


# 把房价数据和POI数据匹配，生成新字典
def match_price_POI(hp_infor, City, ak, queue_data):
    count = 1
    for key, value in hp_infor.items():  # 遍历获得房价信息字典的键和值
        print("线程：", os.getpid(), f'====正在获取第 {count} 条POI数据====')
        if count % 50 == 0:

            time.sleep(1)
        count += 1
        try:
            name, region, lon, lat = get_POI(value[0], str(City), ak)  # 以键（小区名）作为关键词获取POI数据
        except:
            print(f'！！！！！！查询 {key} 的POI数据时遇到一个不可避免的错误！！！！！！')
            name = ''
            region = ''
            lon = ''
            lat = ''
        time.sleep(2)
        value.append(name)
        value.append(region)
        value.append(lon)
        value.append(lat)
        hp_infor[key] = value  # 更新字典
    queue_data.append(hp_infor)
    print("线程：", os.getpid(), 'POI数据爬取完成')
    return hp_infor


# 把房价数据和POI数据写入CSV
def write_CSV_with_POI(data, FileName):
    Mycsv = open(f'{FileName}.csv', 'a', newline='')  # 打开csv
    csv_write = csv.writer(Mycsv, dialect='excel')
    tittle = ('小区', '地区', '商圈', '房价', 'POI小区', 'POI地区', '经度', '纬度')  # 表头
    csv_write.writerow(tittle)  # 写入表头
    count = 1
    for key, value in data.items():
        content = (value[0], value[1], value[2], value[3], value[4], value[5], value[6], value[7])
        try:
            csv_write.writerow(content)
        except:
            test_bug = ("???", value[1], value[2], value[3], value[4], value[5], value[6], value[7])  # 针对无法识别的字符
            csv_write.writerow(test_bug)
        if count % 10 == 0:
            print(f'===================正在写入第 {count} 条房价数据===================')
        count += 1
    print('数据写入完成')


# ----------

# 读取本地所有js文件并合并成字典
def read_json(local_path):
    list_data = {}
    for filename in os.listdir(local_path):
        if filename.endswith(".json"):
            file_path = os.path.join(filename)
            with open(file_path, 'r', encoding='UTF-8') as f:
                one_data = json.load(f)
            list_data[file_path] = one_data

    return list_data


if __name__ == '__main__':
    # 计时
    startime = datetime.datetime.now()
    print(f'当前时间   {startime}')

    # --1--
    # -----爬取房价数据并写入json文件-----

    url = 'https://wh.lianjia.com/xiaoqu/'
    process_1 = multiprocessing.Process(target=writer_in_json,
                                        args=(url, 'cro21/', 1, 50, '房价升序1-50.json'))
    process_2 = multiprocessing.Process(target=writer_in_json,
                                        args=(url, 'cro21/', 51, 100, '房价升序51-100.json'))
    process_3 = multiprocessing.Process(target=writer_in_json,
                                        args=(url, 'cro22/', 1, 50, '房价降序1-50.json'))
    process_4 = multiprocessing.Process(target=writer_in_json,
                                        args=(url, 'cro22/', 51, 100, '房价降序51-100.json'))
    process_5 = multiprocessing.Process(target=writer_in_json,
                                        args=(url, 'cro22p3/', 1, 55, '房价1w-1.5w段降序1-55.json'))
    process_6 = multiprocessing.Process(target=writer_in_json,
                                        args=(url, 'cro22p3/', 56, 80, '房价1w-1.5w段降序56-80.json'))
    process_7 = multiprocessing.Process(target=writer_in_json,
                                        args=(url, 'cro21p4/', 1, 30, '房价1.5w-2w段正序1-30.json'))

    process_1.start()
    process_2.start()
    process_3.start()
    process_4.start()
    process_5.start()
    process_6.start()
    process_7.start()
    
    # 等待线程结束再继续执行主程序
    process_1.join()
    process_2.join()
    process_3.join()
    process_4.join()
    process_5.join()
    process_6.join()
    process_7.join()
    
    print(f'-----房价爬取结束，开始爬取POI-----')
    print(f'-------------------------------')

    # --2--
    # 高德api key
    ak = '451beffca500dbdef34d1385fcc83d87'
    ak1 = 'a09f40df50fc729451b4315d3799808c'
    city = '武汉'
    local_path = os.path.abspath('.')

    # 读取文件中的数据
    list_data = read_json(local_path)
    re_data = {}

    manager = multiprocessing.Manager()
    queue_data = manager.list()    # 进程列表，用于获取返回值

    process_8 = multiprocessing.Process(target=match_price_POI,
                                        args=(list_data['房价升序1-50.json'], city, ak, queue_data))
    process_9 = multiprocessing.Process(target=match_price_POI,
                                        args=(list_data['房价升序51-100.json'], city, ak, queue_data))
    process_10 = multiprocessing.Process(target=match_price_POI,
                                        args=(list_data['房价1w-1.5w段降序56-80.json'], city, ak, queue_data))
    process_11 = multiprocessing.Process(target=match_price_POI,
                                        args=(list_data['房价1.5w-2w段正序1-30.json'], city, ak, queue_data))
    process_12 = multiprocessing.Process(target=match_price_POI,
                                        args=(list_data['房价降序1-50.json'], city, ak1, queue_data))
    process_13 = multiprocessing.Process(target=match_price_POI,
                                        args=(list_data['房价降序51-100.json'], city, ak1, queue_data))
    process_14 = multiprocessing.Process(target=match_price_POI,
                                        args=(list_data['房价1w-1.5w段降序1-55.json'], city, ak1, queue_data))

    process_8.start()
    process_9.start()
    process_10.start()
    process_11.start()
    process_12.start()
    process_13.start()
    process_14.start()

    # 等待线程结束再继续执行主程序
    process_8.join()
    process_9.join()
    process_10.join()
    process_11.join()
    process_12.join()
    process_13.join()
    process_14.join()

    print(f'-----POI爬取结束，开始写入文件-----')
    print(f'-------------------------------')

    # 写入文件
    # 合并数据
    for i in queue_data:
        re_data.update(i)

    write_CSV_with_POI(re_data, '武汉房价和POI')
    # 计时结束
    endtime = datetime.datetime.now()
    print(f'当前时间   {endtime}')
    print('')
    print(f'共花费时间   {endtime - startime}')
    print('')
