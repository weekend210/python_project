# -*- coding: utf-8 -*-
# @Time    : 2023/4/25 13:33
# @Author  : 余建华
# @FileName: txt2shp.py

import time
import shapefile
import coordinate_conversion as cc
from osgeo import osr

# 输入的轨迹数据文件路径
input_txt_path = r".\train_points\20140804_train.txt"
# 输出的轨迹数据文件路径
output_shp_path = r".\train_points\20140804_train_output.shp"

# 读取输入的轨迹数据
of = open(input_txt_path, 'r')
# 写入输出的轨迹数据
wf = shapefile.Writer(output_shp_path, shapeType=shapefile.POINT)
# 定义轨迹数据的参考坐标系
project = osr.SpatialReference()
project.ImportFromEPSG(4326)  # EPSG：4326表示GCS_WGS_1984
wkt = project.ExportToWkt()
# 写入坐标信息
f = open(output_shp_path.replace(".shp", ".prj"), 'w')
f.write(wkt)  # 写入坐标信息
# 字段属性
wf.field('VehicleID')   # 车辆id
wf.field('Lat')         # 坐标纬度
wf.field('Lng')         # 坐标经度
wf.field('OpenStatus')  # 载客状态
wf.field('timestamp')   # 时间戳
for readline in of.readlines():
    # 去掉每一行记录的换行符
    readline = readline.strip('\n')
    print(readline)  # 观察控制台输出判断程序的运行
    # 以","符号进行分割读取指定的字段值
    vehicleID, Lat_gcj02, Lng_gcj02, OpenStatus, date = readline.split(',')
    # 筛选前500辆车的轨迹数据（可根据自己电脑性能增加数据量）
    vehicleNum = 500
    if int(vehicleID) < vehicleNum + 1:
        # 坐标转换由火星坐标（gcj02）转为wgs84
        lng_lat_wgs84_list = cc.gcj02towgs84(float(Lng_gcj02), float(Lat_gcj02))
        Lng_wgs84 = lng_lat_wgs84_list[0]
        Lat_wgs84 = lng_lat_wgs84_list[1]
        # 筛选成都市四环内的轨迹数据（可根据自己的需求扩大研究区域）
        if 103.93 < Lng_wgs84 < 104.21 and 30.57 < Lat_wgs84 < 30.79:
            # 时间格式date转时间戳
            time_Array = time.strptime(date, "%Y/%m/%d %H:%M:%S")
            time_stamp = int(time.mktime(time_Array))
            # 写入几何信息的坐标
            wf.point(Lng_wgs84, Lat_wgs84)
            # 写入属性信息的字段值
            wf.record(vehicleID, Lat_gcj02, Lng_gcj02, OpenStatus, time_stamp)
    elif int(vehicleID) == vehicleNum + 1:
        break

wf.close()
f.close()
