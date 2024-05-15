import shapefile
from matplotlib import pyplot as plt
import math
import random
from osgeo import osr
import multiprocessing
import datetime


# 绘制散点图
def plot_scatter(data, labels=None):
    x = [point[0] for point in data]
    y = [point[1] for point in data]

    plt.scatter(x, y, c=labels)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Scatter Plot')
    plt.colorbar(label='Cluster')
    plt.show()


# 计算两个点之间的欧几里得距离
def euclidean_distance(point1, point2):
    return math.sqrt(sum((x1 - x2) ** 2 for x1, x2 in zip(point1, point2)))


# 分配数据点到最近的聚类中心
def assign_data_points(data, centroids):
    labels = []
    for point in data:
        distances = [euclidean_distance(point, centroid) for centroid in centroids]
        label = distances.index(min(distances))
        labels.append(label)
    return labels


# 更新聚类中心为所属数据点的均值
def update_centroids(data, labels, k):
    centroids = []
    for i in range(k):
        cluster_points = [point for point, label in zip(data, labels) if label == i]

        # 计算均值
        centroid = [sum(coords) / len(coords) for coords in zip(*cluster_points)]
        centroids.append(centroid)
    return centroids


# k-means
def kmeans(data, k):
    # 随机初始化k个聚类中心
    centroids = random.sample(data, k)

    i = 0
    while (1):
        if i % 10 == 0:
            print(i)

        # 分配数据点到最近的聚类中心
        labels = assign_data_points(data, centroids)

        # 更新聚类中心为所属数据点的均值
        new_centroids = update_centroids(data, labels, k)

        # 如果新的聚类中心与旧的聚类中心几乎相同，则算法收敛，退出循环
        if new_centroids == centroids:
            break

        centroids = new_centroids
        i += 1
    return labels, centroids


def out_put_shp_file(file, output_shp_path, n):
    border_shape = shapefile.Reader(file)
    data = border_shape.records()
    border = border_shape.shapes()

    # 将point类型转为数组
    border_points = []  # 存原始点数据[[[x1,y1]],[[x2,y2]],...,...]
    points_xy = []  # 存修改后的只包含点的二维数组[[x1,y1],[x2,y2]，...，...]
    s = 0
    for i in border:
        border_points.append(i.points)
        points_xy.append(border_points[s][0])
        s += 1

    # 进行Kmeans聚类，并返回对应的类别labels数组
    labels, centroids = kmeans(points_xy, n)
    # 显示
    # plot_scatter(points_xy, labels)

    # 将数据写入shp文件
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
    wf.field('k_type')  # 类别

    i = 0
    for key in data:
        if i + 1 % 100000 == 0:
            print('正在写入第', i, '个数据')

        # 写入几何信息的坐标
        wf.point(key[3], key[4])
        # 写入属性信息的字段值
        wf.record(key[0], key[1], key[2], key[3], key[4], labels[i])
        i += 1

    wf.close()
    f.close()


if __name__ == '__main__':
    # 计时
    startime = datetime.datetime.now()
    print(f'当前时间   {startime}')
    n = 18  # 类别数

    process_1 = multiprocessing.Process(target=out_put_shp_file,
                                        args=(r'./shp_file/1109起点.shp', r'./result/K1109起点.shp', n))
    process_2 = multiprocessing.Process(target=out_put_shp_file,
                                        args=(r'./shp_file/1109终点.shp', r'./result/K1109终点.shp', n))
    process_3 = multiprocessing.Process(target=out_put_shp_file,
                                        args=(r'./shp_file/1112起点.shp', r'./result/K1112起点.shp', n))
    process_4 = multiprocessing.Process(target=out_put_shp_file,
                                        args=(r'./shp_file/1112终点.shp', r'./result/K1112终点.shp', n))

    process_1.start()
    process_2.start()
    process_3.start()
    process_4.start()

    process_1.join()
    process_2.join()
    process_3.join()
    process_4.join()

    # 计时结束
    endtime = datetime.datetime.now()
    print(f'当前时间   {endtime}')
    print('')
    print(f'共花费时间   {endtime - startime}')
    print('')
