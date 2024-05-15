# -*- coding: utf-8 -*-
# @Time    : 2023/12/26 20:50
# @Author  : Yuecheng_Li
# @FileName: 高德API爬取

import requests
import math

pi = 3.1415926535897932384626  # π
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 扁率


# 判断是否在国内，不在国内不做偏移
def out_of_china(lng, lat):
    if lng < 72.004 or lng > 137.8347:
        return True
    if lat < 0.8293 or lat > 55.8271:
        return True
    return False


def transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 *
            math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 *
            math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret


def transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 *
            math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 *
            math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret


# 坐标转换
def gcj02towgs84(lng, lat):
    """
    GCJ02(火星坐标系)转GPS84
    :param lng:火星坐标系的经度
    :param lat:火星坐标系纬度
    :return:
    """
    if out_of_china(lng, lat):
        return lng, lat
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [lng * 2 - mglng, lat * 2 - mglat]


# -----POI数据获取部分-----
# 获取地理编码
def get_POI(Keyword, ak):
    # 高德地图api   https://lbs.amap.com/
    url = f'https://restapi.amap.com/v3/geocode/geo?key={ak}&address={Keyword}'
    html = requests.get(url)  # 获取网页信息
    data = html.json()  # 获取网页信息的json格式数据
    item = data['geocodes'][0]
    Name = item['formatted_address']  # 全名
    ######获取经纬度######
    location = item['location']
    mid = location.split(',')  # 以","分割开经纬度
    Longitude = mid[0]  # 经度
    Latitude = mid[1]  # 纬度
    return Name, Longitude, Latitude


# 根据名称获取地理编码并转换坐标
def match_price_POI(hp_infor, ak):
    name_x = hp_infor
    try:
        name, lon, lat = get_POI(name_x, ak)  # 以键作为关键词获取POI数据

        # 坐标转换
        lng_lat_wgs84_list = gcj02towgs84(float(lon), float(lat))
        lon = lng_lat_wgs84_list[0]
        lat = lng_lat_wgs84_list[1]

    except:
        print(f'！！！！！！查询 {name_x} 的条数据时遇到一个不可避免的错误！！！！！！')
        name = ''
        lon = ''
        lat = ''
    print(name, lon, lat)
    return name, lon, lat

