# -*- coding: utf-8 -*-
"""
地图匹配 map matching
程序的主体部分
有主函数

"""

import os.path
import time
from collections import namedtuple, defaultdict

import fiona
import shapefile
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

from cache import clear_cache
from core import match_until_connect

os.environ['PROJ_LIB'] = 'D:\anaconda3\envs\new_env\Library\share\proj'# 假设gdal对应的proj.db在这个文件夹下
os.environ['GDAL_DATA'] = 'D:\anaconda3\envs\new_env\Library\share'

# 创建一个名称为'CPointRec'的新元组子类
CPointRec = namedtuple('CPointRec', ["log_x", "log_y", "p_x", "p_y", "road_id", "log_id", "source", "target",
                                     "weight", "fraction", "log_time", "taxi_id"])
# 创建一个名称为'TrackRec'的新元组子类
TrackRec = namedtuple('TrackRec', ['x', 'y', 'taxi_id', 'object_id', 'log_time'])


def get_road_rtree(shp_path):
    """
    获得道路：
    rtree
    (coords,id)->feature字典 coords:表示路段的首尾坐标
    Parameters:
    -----------
    shp_path : str
        道路文件路径

    Returns:
        rtree
        coord_id_feature_dict
    """
    # 读取指定路径的所有要素
    road_features = fiona.open(shp_path)

    coord_id_feature_dict = {}  # list格式存储 road: (coords, id)->feature 字典
    geom_list = []  # array格式存储 road：geometry几何图形

    # 遍历road的每个要素的几何信息，然后把geometry添加至geom_list
    for road_feature in road_features:
        geometry = road_feature['geometry']
        if geometry is None:
            print("geometry is none")
            print(road_feature['id'])
        # 读取道路的id
        road_feature_id = road_feature['id']
        # 返回一个新的独立的几何图形
        geom = shape(geometry)
        geom_list.append(geom)

        # coord[0]表示数组的第一个元素，[-1]表示数组的最后一个元素(倒数第一个元素)
        coord_key = geom.coords[0] + geom.coords[-1]

        # assert(断言)用于判断一个表达式，在表达式条件为false的时候触发异常
        # 可在条件不满足程序运行的情况下直接返回错误，而不必等待程序运行后出现崩溃的情况
        assert ((coord_key, road_feature_id) not in coord_id_feature_dict)
        # road：(coord, id)->feature 字典赋值
        coord_id_feature_dict[(coord_key, road_feature_id)] = road_feature

    road_features.close()
    # STRtree构建空间索引-查询方法可以用于对索引上的对象进行空间查询。
    # 一旦创建，STRtree是不可变的。您不能添加或删除几何图形
    rtree = STRtree(geom_list)

    return rtree, coord_id_feature_dict


def get_closest_points(log, road_rtree, coord_feature_dict, key_coord_id_dict):
    """
    获得点在路网中的投影点

    Parameters:
    -------------
    point : shapely point
        gps log点
    road_tree : shapely rtree
        道路 road_rtree
    coord_feature_dict: dict
        道路头尾标识 (source, target)-> 道路feature字典
    key_coord_id_dict: dict
        道路头尾坐标 (geom[0], geom[1])-> 道路id 字典
    """

    point = Point(log.x, log.y)
    # 以point为中心 根据道路的常规宽度，设置参数“radius=35”为半径构建缓冲区
    point_buffer = point.buffer(35)

    project_roads = []  # 存储在缓冲区范围内的road
    # road_rtree空间索引 遍历query查询与轨迹点在缓冲区内的roads
    for road in road_rtree.query(point_buffer):
        # 如果相交则返回True，否则返回False
        if road.intersects(point_buffer):
            project_roads.append(road)

    proj_points = []  # 存储符合条件的投影点
    for road in project_roads:
        # 返回沿着这个图形(road)到最近的指定点(point)的距离
        # 如果归一化参数(normalized)为真，则返回归一化到线性几何的长度 归一化距离(0,1)之间取值
        fraction = road.project(point, normalized=True)
        # 沿着road返回指定距离(fraction)的点
        # 如果归一化参数(normalized)为真，那么距离将被解释为几何图形长度的分数。
        project_point = road.interpolate(fraction, normalized=True)
        # 获取路段要素信息
        coord_key = road.coords[0] + road.coords[-1]
        road_feature_id = str(key_coord_id_dict[coord_key])
        road_feature = coord_feature_dict[(coord_key, road_feature_id)]
        proj_points.append(CPointRec(
            log.x,
            log.y,
            project_point.x,
            project_point.y,
            int(road_feature['id']),
            log.object_id,
            road_feature['properties']['from_'],
            road_feature['properties']['to_'],
            road_feature['properties']['length'],
            fraction,
            log.log_time,
            log.taxi_id
        ))

    return proj_points


def read_track(shp_path):
    """
    读取轨迹数据
    Args:
        shp_path:
        # 轨迹数据输入路径
    Returns:
        taxi_by_id 轨迹数据集 taxi_id -> TrackRec

    """
    # 创建默认格式的字典
    taxi_id_logs = defaultdict(list)

    track_features = fiona.open(shp_path)
    object_num = 0
    # 遍历轨迹所有要素
    for feature in track_features:
        geometry = feature['geometry']
        # x,y分别表示轨迹点的横纵坐标
        x = geometry['coordinates'][0]
        y = geometry['coordinates'][1]
        # # 不考虑不在指定范围内的轨迹点
        # # 判别轨迹点是否在范围内，不在continue
        # if 40164158.015 < x < 40215011.033 and 4409132.785 < y < 4448026.613:
        properties = feature['properties']
        taxi_id = properties['VehicleID']
        taxi_id_logs[taxi_id].append(
            TrackRec(
                x,
                y,
                taxi_id,
                object_num,
                # 轨迹记录的时间：时间戳
                properties['timestamp']
            )
        )
        object_num += 1
        # else:
        #     continue
    return taxi_id_logs


def read_road(shp_path):
    """
    读取road文件，

    构建并获得：
        (source, target) -> road_id 字典 key_road_id_dict
        road_id -> geometry字典 road_id_geometry_dict
        coords-> road_id  字典 key_coord_id_dict
        road_id -> properties字典 road_id_properties_dict
    
    """
    road_features = fiona.open(shp_path)

    road_id_geometry_dict = {}
    key_road_id_dict = {}
    key_coord_id_dict = {}
    road_id_properties_dict = {}
    # 遍历所有道路要素 获取需要的信息字典
    for feature in road_features:
        geometry = feature['geometry']
        geom = shape(geometry)
        properties = feature['properties']
        source = properties['from_']
        target = properties['to_']
        road_id = int(feature['id'])

        road_id_geometry_dict[road_id] = geometry
        road_id_properties_dict[road_id] = properties
        key_road_id_dict[(source, target)] = road_id
        key_coord_id_dict[geom.coords[0] + geom.coords[-1]] = road_id

    return key_road_id_dict, road_id_geometry_dict, road_id_properties_dict, key_coord_id_dict


if __name__ == '__main__':

    KS_time = time.time()
    # # 设置读取前m辆车的轨迹数据
    # m = 1000
    # 输入和输出的路径名称
    input_road_shp_path = './road/Roads.shp'
    input_track_shp_path = './track/c20140804_Project.shp'
    output_track_shp_path = './result/chengdu_20140804_train_match.shp'

    if os.path.isfile(input_road_shp_path):
        # 调用get_road_rtree()函数
        road_rtree, coord_feature_dict = get_road_rtree(input_road_shp_path)
        # 调用read_road()函数
        key_road_id_dict, road_id_geometry_dict, road_id_properties_dict, key_coord_id_dict \
            = read_road(input_road_shp_path)
        print('读取路网数据结束！')
        # # 遍历读取前m辆车的轨迹数据
        # for i in range(m):

        write_shp_file = shapefile.Writer(output_track_shp_path, shapeType=shapefile.POINT)

        all_match_point_list = defaultdict(list)
        if os.path.isfile(input_track_shp_path):
            # 调用read_track()函数
            track_id_logs = read_track(input_track_shp_path)
            # 遍历读取轨迹数据点

            print(len(track_id_logs))

            for taxi_id, logs in track_id_logs.items():
                # begin_tick = time.time()

                log_id_list = []
                log_closest_points = defaultdict(list)

                print(len(logs))

                for log in logs:
                    # 调用get_closest_points()函数 返回符合条件的投影点
                    project_points_list = get_closest_points(log, road_rtree, coord_feature_dict, key_coord_id_dict)

                    # if not project_points:
                    #     print(log.object_id)



                    #     print("no project point!")
                    # else:
                    if project_points_list:
                        log_closest_points[log.object_id] = project_points_list
                        log_id_list.append(log.object_id)
                # 清空缓存的距离
                clear_cache()

                if not log_id_list:
                    continue
                # 调用match_until_connect() 以log_id列表和投影点list作为输入
                # 返回获取的连通匹配点列表作为输出
                match_point_list = match_until_connect(log_id_list, log_closest_points, input_road_shp_path)

                if match_point_list is not None:
                    all_match_point_list[taxi_id] = match_point_list
                else:
                    continue
            write_shp_file.field('VehicleID')
            write_shp_file.field('object_id')
            write_shp_file.field('road_id')
            write_shp_file.field('log_x')
            write_shp_file.field('log_y')
            write_shp_file.field('log_time')

            print(len(all_match_point_list))

            for taxi_id, match_point_list in all_match_point_list.items():
                for match_point in match_point_list:
                    record_list = []
                    write_shp_file.point(match_point.p_x, match_point.p_y)
                    record_list.append(match_point.taxi_id)
                    # record_list.append(match_point.object_id)
                    record_list.append(match_point.road_id)
                    record_list.append(match_point.log_x)
                    record_list.append(match_point.log_y)
                    record_list.append(match_point.log_time)
                    write_shp_file.record(*record_list)


            print('run over!')
        else:
            print('轨迹数据输入路径有问题 请检查后再运行程序！')

        write_shp_file.close()
        print("耗时（秒）：")
        print(time.time() - KS_time)
    else:
        print('路网数据输入路径有问题 请检查后再运行程序！')
    # 保存结果
