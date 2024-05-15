# -*- coding: utf-8 -*-
# @Time    : 2024/1/9 23:55
# @Author  : Yuecheng_Li
# @FileName: 航线爬虫

import requests
import pandas as pd
import numpy as np
from API import match_price_POI


# 爬取航班目的地和飞行时间
def get_airway(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                             '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'}

    # 获取网页的信息
    response = requests.get(url=url, headers=headers)
    # 储存为json格式
    content = response.json()

    # 获取航班目的地
    end_area_list = []
    use_time_list = []
    for data in content['data']:
        end_area_list.append(data['destAirportNameCn'])
        use_time_list.append(data['useTime'])

    return end_area_list, use_time_list


if __name__ == '__main__':
    pg1 = 1
    pgend = 29
    filename = 'API_result.csv'
    ak = '451beffca500dbdef34d1385fcc83d87'

    get_data = pd.DataFrame()
    end_area_list = []
    use_time_list = []
    # 逐页爬取数据
    # 链接可能已经失效，需要重新获取链接
    for i in range(pg1, pgend):
        url = f'http://www.whairport.com/airport/domPassFlightDepInfo/list.do?pageIndex={i}&date=20240110&beginHour=00&endHour=&flightNo=&terminal=&airport=&airline=&_=17048107344{38+i}'
        end_area, use_time = get_airway(url)
        end_area_list += end_area
        use_time_list += use_time
    get_data['end'] = pd.Series(end_area_list)
    get_data['use_time'] = pd.Series(use_time_list)

    # 数据清洗
    # 删除不能识别的数据
    get_data = get_data[~get_data['end'].str.contains('未识别三字码')]
    # 删除重复值
    get_data.drop_duplicates(subset=None, keep='first', inplace=False)
    # 将所有0的项转为缺失值
    get_data = get_data.replace(0, np.nan)
    # 删除值为0的行
    get_data = get_data[(get_data != 0).all(axis=1)].dropna()
    # 重置索引
    get_data = get_data.drop_duplicates().reset_index(drop=True)

    # 通过高德API获取地理编码
    # 武汉经纬度
    slon = 114.310176
    slat = 30.590076
    name_list = []
    slon_list = []
    slat_list = []
    lon_list = []
    lat_list = []
    for end in get_data['end']:
        name, lon, lat = match_price_POI(end, ak)
        name_list.append(name)
        lon_list.append(lon)
        lat_list.append(lat)
        slon_list.append(slon)
        slat_list.append(slat)
    get_data['slon'] = pd.Series(slon_list)
    get_data['slat'] = pd.Series(slat_list)
    get_data['match_name'] = pd.Series(name_list)
    get_data['lon'] = pd.Series(lon_list)
    get_data['lat'] = pd.Series(lat_list)

    # 写入csv文件中
    get_data.to_csv(filename, index=False, sep=',')
