# -*- coding: utf-8 -*-
# @Time    : 2023/11/27 13:42
# @Author  : Yuecheng_Li
# @FileName: read_csvfile_toshp

import numpy as np
import datetime
import pandas as pd
import shapefile
import coordinate_conversion as cc
from osgeo import osr
import multiprocessing
import os
from math import sin, cos, atan2, pi
from geopy.distance import geodesic
import warnings



# https://blog.csdn.net/Mr_deadline/article/details/111264116
# 计算方向角
def calcu_azimuth(lat1, lon1, lat2, lon2):
    lat1_rad = lat1 * pi / 180
    lon1_rad = lon1 * pi / 180
    lat2_rad = lat2 * pi / 180
    lon2_rad = lon2 * pi / 180
    y = sin(lon2_rad - lon1_rad) * cos(lat2_rad)
    x = cos(lat1_rad) * sin(lat2_rad) - sin(lat1_rad) * cos(lat2_rad) * cos(lon2_rad - lon1_rad)
    brng = atan2(y, x) / pi * 180
    return float((brng + 360.0) % 360.0)


# 计算时间差，返回秒
def get_timepast(startime, endtime):
    star_time = datetime.datetime.fromtimestamp(startime)
    end_time = datetime.datetime.fromtimestamp(endtime)
    return (end_time - star_time).total_seconds()


# 读取后，转换坐标，再写入文件中
def mutl_Thread_run(gps_data, star, end, re_data_list):
    global x, how_many_cars
    car_id = ''

    # 循环遍历轨迹数据的每一行
    for i in range(star, end):
        if i % 10000 == 0:
            print(i)

        # 设置为到固定车辆时就停止，可更改
        if x == how_many_cars:
            break

        if car_id != gps_data['car_id'][i]:
            car_id = gps_data['car_id'][i]
            x += 1
            print("线程：", os.getpid(), ':', x)

        # 坐标转换由火星坐标（gcj02）转为wgs84
        lng_lat_wgs84_list = cc.gcj02towgs84(float(gps_data['lon'][i]), float(gps_data['lat'][i]))

        one_row = [gps_data['car_id'][i], gps_data['order_id'][i], gps_data['time'][i],
                   lng_lat_wgs84_list[0], lng_lat_wgs84_list[1]]

        re_data_list.append(one_row)

    print("线程：", os.getpid(), '转换完成')


# 计算订单轨迹属性
def get_attribute(order_data_in, filename):
    order_data = order_data_in.copy()

    # 禁用特定警告
    warnings.filterwarnings('ignore')

    timelist = []  # 时间列表
    distencelist = []  # 距离列表
    directionlist = []  # 方向列表

    for i in range(len(order_data['order_id'])):
        if i % 10000 == 0:
            print('处理订单属性中：', i)

        # 坐标转换
        # 坐标转换由火星坐标（gcj02）转为wgs84
        start_lng_lat_wgs84_list = cc.gcj02towgs84(float(order_data['start_lon'][i]), float(order_data['start_lat'][i]))
        end_lng_lat_wgs84_list = cc.gcj02towgs84(float(order_data['end_lon'][i]), float(order_data['end_lat'][i]))

        order_data['start_lon'][i] = start_lng_lat_wgs84_list[0]
        order_data['start_lat'][i] = start_lng_lat_wgs84_list[1]
        order_data['end_lon'][i] = end_lng_lat_wgs84_list[0]
        order_data['end_lat'][i] = end_lng_lat_wgs84_list[1]

        # 计算时间差，单位为秒
        time_past = get_timepast(order_data['start_time'][i], order_data['end_time'][i])
        timelist.append(time_past)

        # 计算起点终点之间的距离,单位为米
        distance = geodesic((start_lng_lat_wgs84_list[1], start_lng_lat_wgs84_list[0]),
                            (end_lng_lat_wgs84_list[1], end_lng_lat_wgs84_list[0])).kilometers
        distencelist.append(distance)

        # 计算起点终点之间的角度
        direction = calcu_azimuth(start_lng_lat_wgs84_list[1], start_lng_lat_wgs84_list[0],
                                  end_lng_lat_wgs84_list[1], end_lng_lat_wgs84_list[0])
        directionlist.append(direction)


    order_data['timepast'] = pd.Series(timelist)
    order_data['distence'] = pd.Series(distencelist)
    order_data['direction'] = pd.Series(directionlist)

    # 写入新的csv文件中
    order_data.to_csv(filename, index=False, sep=',')
    return order_data

x = 1 # 车辆计数
how_many_cars = 500 # 提取车辆数
# 按装订区域中的绿色按钮以运行脚本。
if __name__ == '__main__':
    # 计时
    startime = datetime.datetime.now()
    print(f'当前时间   {startime}')

    order_file = r'order_20161112.csv'
    gps_file = r'gps_20161112.csv'
    output_order_path = r'.\result\new_order_20161112.csv'
    output_shp_path = r'.\result\gps_20161112.shp'

    # 订单文件
    order_col_names = ['order_id',
                       'start_time',
                       'end_time',
                       'start_lon',
                       'start_lat',
                       'end_lon',
                       'end_lat']

    order_data = pd.read_csv(order_file, names=order_col_names, header=None)
    # 删除重复项
    order_data.drop_duplicates(subset=None, keep='first', inplace=False)
    # 将所有0的项转为缺失值
    order_data = order_data.replace(0, np.nan)
    # 删除值为0的行
    order_data = order_data[(order_data != 0).all(axis=1)].dropna()
    # 重置索引
    order_data = order_data.drop_duplicates().reset_index(drop=True)


    # 轨迹点文件
    gps_col_names = ['car_id',
                     'order_id',
                     'time',
                     'lon',
                     'lat']

    gps_data = pd.read_csv(gps_file, names=gps_col_names, header=None)
    # 删除重复项
    gps_data.drop_duplicates(subset=None, keep='first', inplace=False)
    # 删除值为0的行
    gps_data = gps_data[gps_data.loc[:] != 0].dropna()
    # 重置索引
    gps_data.drop_duplicates().reset_index(drop=True)

    


    # 输出shp文件
    wf = shapefile.Writer(output_shp_path, shapeType=shapefile.POINT)
    # 坐标系
    project = osr.SpatialReference()
    project.ImportFromEPSG(4326)  # EPSG：4326表示GCS_WGS_1984
    wkt = project.ExportToWkt()
    # 写入坐标信息
    f = open(output_shp_path.replace(".shp", ".prj"), 'w')
    f.write(wkt)  # 写入坐标信息
    # 字段属性
    wf.field('car_id')  # 车辆id
    wf.field('order_id')  # 订单id
    wf.field('time')  # 时间戳
    wf.field('lon')  # 经度
    wf.field('lat')  # 纬度

    manager = multiprocessing.Manager()
    re_data_list = manager.list()  # 进程列表，用于获取返回值

    process_1 = multiprocessing.Process(target=mutl_Thread_run, args=(gps_data, 0, 2878734, re_data_list))
    process_2 = multiprocessing.Process(target=mutl_Thread_run, args=(gps_data, 2878734, 5757468, re_data_list))
    process_3 = multiprocessing.Process(target=mutl_Thread_run, args=(gps_data, 5757468, 8636202, re_data_list))
    process_4 = multiprocessing.Process(target=mutl_Thread_run, args=(gps_data, 8636202, 11514936, re_data_list))
    process_5 = multiprocessing.Process(target=mutl_Thread_run, args=(gps_data, 11514936, 14393670, re_data_list))
    process_6 = multiprocessing.Process(target=mutl_Thread_run, args=(gps_data, 14393670, 17272404, re_data_list))
    process_7 = multiprocessing.Process(target=mutl_Thread_run, args=(gps_data, 17272404, 20151138, re_data_list))
    process_8 = multiprocessing.Process(target=mutl_Thread_run, args=(gps_data, 20151138, 23029872, re_data_list))
    process_9 = multiprocessing.Process(target=mutl_Thread_run, args=(gps_data, 23029872, 25908606, re_data_list))
    process_10 = multiprocessing.Process(target=mutl_Thread_run, args=(gps_data, 25908606, 28787340, re_data_list))
    process_11 = multiprocessing.Process(target=mutl_Thread_run, args=(gps_data, 28787340, 31666074, re_data_list))
    process_12 = multiprocessing.Process(target=mutl_Thread_run, args=(gps_data, 31666074, len(gps_data['car_id']), re_data_list))

    # 计算轨迹属性
    process_x = multiprocessing.Process(target=get_attribute, args=(order_data, output_order_path))

    process_1.start()
    process_2.start()
    process_3.start()
    process_4.start()
    process_5.start()
    process_6.start()
    process_7.start()
    process_8.start()
    process_9.start()
    process_10.start()
    process_11.start()
    process_12.start()

    process_x.start()

    process_1.join()
    process_2.join()
    process_3.join()
    process_4.join()
    process_5.join()
    process_6.join()
    process_7.join()
    process_8.join()
    process_9.join()
    process_10.join()
    process_11.join()
    process_12.join()

    process_x.join()


    # 将数据写入shp文件
    i = 1
    for key in re_data_list:
        if i % 100000 == 0:
            print('正在写入第', i, '个数据')
        i += 1
        # 写入几何信息的坐标
        wf.point(key[3], key[4])
        # 写入属性信息的字段值
        wf.record(key[0], key[1], key[2], key[3], key[4])

    wf.close()
    f.close()


    # 计时结束
    endtime = datetime.datetime.now()
    print(f'当前时间   {endtime}')
    print('')
    print(f'共花费时间   {endtime - startime}')
    print('')
