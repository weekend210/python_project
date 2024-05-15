# -*- coding: utf-8 -*-
# @Time    : 2023/12/5 1:32
# @Author  : Yuecheng_Li
# @FileName: view_DO_points

from shapely.geometry import Point
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import MultiLineString
from shapely.ops import polygonize
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib
import imageio
import os


# 炫酷进度条
# progress: 70.71%	[>>>>>>>>>>>>>>>>>>>>>--------]
def bar1(now, total, length=30, prefix='progress:'):
    print('\r' + prefix + ' %.2f%%\t' % (now / total * 100), end='')
    print('[' + '>' * int(now / total * length) + '-' * int(length - now / total * length) + ']', end='')


# progress:[32.38%]
def bar2(now, total, prefix='progress:'):
    print('\r' + prefix + '[ %.2f%% ]' % (now / total * 100), end='')


# 按照时间进行分类
def classify_timestamps(order_file):
    # 初始化一个长度为 24 的二维数组
    result = [[] for _ in range(24)]

    # 将时间戳按小时分类
    for row in order_file.itertuples():
        dt = datetime.fromtimestamp(row.start_time)
        hour = dt.hour
        result[hour].append(row)

    return result


# 空间连接获取下车点
def get_dropoff_number(fishing_net, order_file, fishing_net_centroid, n):
    # 移除行选择限制，使用整个 fishing_net 数据集
    dropoff = (
        gpd
        .sjoin(fishing_net.loc[n:n, :],
               right_df=order_file,
               predicate='contains',
               how='inner')
        [['end_lon', 'end_lat', 'start_time']]
    )

    dropoff['geometry'] = (dropoff.apply(lambda row: Point(row['end_lon'], row['end_lat']), axis=1))
    dropoff = gpd.GeoDataFrame(dropoff, crs='EPSG:4326').to_crs('EPSG:3857')

    grid_distrib = (
        gpd
        .sjoin(fishing_net.loc[0:100, :],
               right_df=dropoff,
               predicate='contains',
               how='inner')
        .groupby('id', as_index=False)
        .agg({'index_right': 'count'})
        .rename(columns={'index_right': '下车记录数'})
    )

    to_pic = pd.DataFrame()
    start_lon = []
    start_lat = []
    end_lon = []
    end_lat = []
    traffic = []
    for i in range(len(grid_distrib)):
        start_lon.append(fishing_net_centroid[n].x)
        start_lat.append(fishing_net_centroid[n].y)
        end_lon.append(fishing_net_centroid[grid_distrib['id'][i]].x)
        end_lat.append(fishing_net_centroid[grid_distrib['id'][i]].y)

        traffic.append(grid_distrib['下车记录数'][i])

    to_pic['start_lon'] = pd.Series(start_lon)
    to_pic['start_lat'] = pd.Series(start_lat)
    to_pic['end_lon'] = pd.Series(end_lon)
    to_pic['end_lat'] = pd.Series(end_lat)
    to_pic['traffic'] = pd.Series(traffic)

    return to_pic


# 绘制线条
def demo_con_style(x2, y2, x1, y1, traffic_norm, i, ax):
    # 获取渐变色对象，这里使用RdYlGn渐变色
    my_cmap = matplotlib.colormaps.get_cmap("RdYlGn_r")

    # 使用渐变色对象根据归一化的数值生成颜色
    my_colors = my_cmap(traffic_norm)

    ax.annotate("",
                xy=(x1, y1), xycoords='data',
                xytext=(x2, y2), textcoords='data',
                arrowprops=dict(arrowstyle="-", color=my_colors[i],
                                shrinkA=0, shrinkB=0,
                                patchA=None, patchB=None,
                                connectionstyle='arc3,rad=0.3',
                                linewidth=0.3,  # 设置线条粗细
                                # mutation_scale=1  # 设置箭头大小
                                ),
                )


if __name__ == '__main__':
    # 计时
    startime = datetime.now()
    print(f'当前时间   {startime}')
    print()

    # 文件路径
    order_path = 'new_order_20161109.csv'
    chengdu_shp_path = r'.\chengdu\chengdu.shp'
    chengdu_road_path = r'.\chengdu_road\road.shp'
    output_GIF = 'output.gif'

    # -----读取文件
    print('(1/5)-----读取文件-----')
    order_file = pd.read_csv(order_path)
    chengdu_shp = gpd.read_file(chengdu_shp_path)
    chengdu_road = gpd.read_file(chengdu_road_path)

    # 根据特定范围筛选数据，利用条件判断来选择满足条件的数据
    order_file = order_file[
        (order_file['start_lon'].between(103.82, 104.32)) &
        (order_file['start_lat'].between(30.512, 30.888)) &
        (order_file['end_lon'].between(103.82, 104.32)) &
        (order_file['end_lat'].between(30.512, 30.888))
        ]

    # 重置索引
    order_file.reset_index(drop=True, inplace=True)

    # 基于经纬度信息为order_file添加矢量信息列
    order_file['geometry'] = (order_file.apply(lambda row: Point(row['start_lon'], row['start_lat']), axis=1))

    # 转换为GeoDataFrame并统一坐标到Web墨卡托
    order_file = gpd.GeoDataFrame(order_file, crs='EPSG:4326').to_crs('EPSG:3857')

    # -----按照时间进行分类
    print()
    print('(2/5)-----按照时间进行分类-----')
    result = classify_timestamps(order_file)
    result_df_list = []
    bar_num = 0
    all = len(result)
    for i in result:
        # 将字典对象转换为DataFrame
        dfs = [pd.DataFrame([obj]) for obj in i]

        # 合并DataFrame
        result_df = pd.concat(dfs, ignore_index=True)
        # 基于经纬度信息为order_file添加矢量信息列
        result_df['geometry'] = (result_df.apply(lambda row: Point(row['start_lon'], row['start_lat']), axis=1))
        # 转换为GeoDataFrame并统一坐标到Web墨卡托
        result_df = gpd.GeoDataFrame(result_df, crs='EPSG:4326').to_crs('EPSG:3857')

        result_df_list.append(result_df)

        # 显示进度
        bar1(bar_num + 1, all, 30, '进度：')
        bar_num += 1

    # -----创建格网
    print()
    print('(3/5)-----创建格网-----')
    # 提取所有上下车坐标点范围的左下角及右上角坐标信息
    xmin, ymin, xmax, ymax = order_file.total_bounds

    # 创建x方向上的所有坐标位置
    x = np.linspace(xmin, xmax, 11)

    # 创建y方向上的所有坐标位置
    y = np.linspace(ymin, ymax, 11)

    # 生成全部交叉线坐标信息
    hlines = [((x1, yi), (x2, yi)) for x1, x2 in zip(x[:-1], x[1:]) for yi in y]
    vlines = [((xi, y1), (xi, y2)) for y1, y2 in zip(y[:-1], y[1:]) for xi in x]

    # 创建网格
    fishing_net = gpd.GeoDataFrame({
        'geometry': list(polygonize(MultiLineString(hlines + vlines)))},
        crs='EPSG:3857')

    # 添加一一对应得id信息
    fishing_net['id'] = fishing_net.index

    # 标注每个网格的id
    fishing_net_centroid = []  # 所有格网的质心
    for row in fishing_net.itertuples():
        centroid = row.geometry.centroid  # 质心
        fishing_net_centroid.append(centroid)

    # -----绘制线条
    print()
    print('(4/5)-----绘制线条-----')
    # 准备底图
    # 成都矢量数据转换到 EPSG:3857 坐标系
    chengdu_shp = chengdu_shp.to_crs(epsg=3857)
    chengdu_road = chengdu_road.to_crs(epsg=3857)

    # 图像列表
    images = []
    img_number = 0
    all = len(result_df_list)

    # 依次遍历所有时间
    for each_time in result_df_list:
        # 创建画板
        fig, ax = plt.subplots(figsize=(4, 4), dpi=300)
        # 先绘制底图
        chengdu_shp.plot(ax=ax, color='blue', alpha=0.5)
        chengdu_road.plot(ax=ax, color='white', alpha=0.1, linewidth=0.6)

        # 获取下车点数量，并根据数量绘制线条
        all_off = []
        for i in range(100):
            one_piece_off = get_dropoff_number(fishing_net, each_time, fishing_net_centroid, i)
            all_off.append(one_piece_off)

        for j in all_off:
            # 将交通流量的数值归一化到0到1的范围
            try:
                min_value = min(j['traffic'])
            except:
                min_value = 0
            try:
                max_value = max(j['traffic'])
            except:
                max_value = 0

            traffic_norm = []
            for i in range(len(j['start_lon'])):
                if j['traffic'][i] != 0:
                    traffic_value = 0
                    if min_value == max_value:
                        traffic_value = 0
                    else:
                        traffic_value = (j['traffic'][i] - min_value) / (max_value - min_value)
                    traffic_norm.append(traffic_value)

            for i in range(len(j['start_lon'])):
                demo_con_style(j['start_lon'][i], j['start_lat'][i], j['end_lon'][i], j['end_lat'][i], traffic_norm, i,
                               ax)

        ax.set_xlim([xmin, xmax])  # x轴的最小值和最大值
        ax.set_ylim([ymin, ymax])  # y轴的最小值和最大值

        ax.text(x=0.5, y=1, s=f'{img_number}:00', ha='center', va='top', transform=ax.transAxes)  # 添加标题
        ax.axis('off')  # 关闭坐标轴
        fig.savefig(f'image_area_{img_number}.png', dpi=300, bbox_inches='tight', pad_inches=0)  # 保存为单独的图片文件
        images.append(f'image_area_{img_number}.png')  # 将文件名添加到图像列表中
        matplotlib.pyplot.close()
        img_number += 1

        bar1(img_number, all, 30, '进度：')

    # -----合并为GIF
    print()
    print('(5/5)-----合并为GIF-----')
    # 合并成为一张GIF图
    with imageio.get_writer(uri=output_GIF, mode='I', fps=1) as writer:
        for i in range(len(result_df_list)):
            writer.append_data(imageio.v2.imread(f'image_area_{i}.png'))
            os.remove(f'image_area_{i}.png')
            bar2(img_number, all, '进度：')
    os.startfile(output_GIF)

    # 计时结束
    endtime = datetime.now()
    print('')
    print('')
    print(f'当前时间   {endtime}')
    print('')
    print(f'共花费时间   {endtime - startime}')
    print('')
