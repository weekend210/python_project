# -*- coding: utf-8 -*-
import json
from PIL import Image, ImageDraw


# 利用九交模型求多边形面积
def polygon_area(points):
    n = len(points)
    if n < 3:
        return 0  # 无法构成多边形

    area = 0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]  # 下一个顶点
        area += (x1 * y2 - x2 * y1)
    area = area / 2.0
    if area >= 0:
        print(n, '边形的方向为顺时针')
    else:
        print(n, '边形的方向为逆时针')
    return area


# 多边形类
class new_polygon(object):
    def __init__(self, outer_polygon=None, holes=None, islands=None):
        if holes is None:
            holes = []
        if outer_polygon is None:
            outer_polygon = []
        if islands is None:
            islands = []
        self.outer_polygon = outer_polygon  # 外层多边形
        self.holes = holes  # 洞
        self.islands = islands  # 岛（嵌套在其中的一个新的多边形类）

    # 求多边形面积
    def area(self):
        area_value = polygon_area(self.outer_polygon)
        for hole in self.holes:
            area_value += polygon_area(hole)
        for island in self.islands:
            area_value += island.area()  # 递归求岛的面积
        return area_value


# 坐标转换，为了更好的显示
def coordinate_change(point):
    return ((point[0] - 113) * 1000, (point[1] - 29) * 1000)


#   读取json文件中的坐标信息并求面积
def read_file_and_get_area(data_json):
    #   根据geojson格式读取数据
    all_polygons = []
    # 多边形
    for feature in data_json['features']:
        if feature['geometry']['type'] == 'Polygon':
            polygons = new_polygon()
            a = 1  # 计数，第一个是最外层多边形，其他是洞，没有岛
            for coordinate in feature['geometry']['coordinates']:
                polygon = []  # 多边形

                for x in coordinate:
                    point = (x[0], x[1])  # 点的元组
                    polygon.append(coordinate_change(point))  # 坐标转换

                if a == 1:
                    polygons.outer_polygon = polygon
                    a += 1
                else:
                    polygons.holes.append(polygon)

            all_polygons.append(polygons)

        # 多多边形
        elif feature['geometry']['type'] == 'MultiPolygon':
            i = 1  # 计数，第一个是最外层多边形，其他是岛
            polygons = new_polygon()
            for coordinate in feature['geometry']['coordinates']:
                if i == 1:  # 最外层多边形
                    i += 1
                    a = 1  # 计数，第一个是最外层多边形，其他是洞
                    for multi in coordinate:
                        polygon = []  # 多边形

                        for x in multi:
                            point = (x[0], x[1])  # 点的元组
                            polygon.append(coordinate_change(point))  # 坐标转换

                        if a == 1:
                            polygons.outer_polygon = polygon
                            a += 1

                        else:
                            polygons.holes.append(polygon)
                            a += 1
                else:  # 岛
                    i += 1
                    a = 1  # 计数，第一个是岛的最外层多边形，其他是洞
                    polygons_island = new_polygon()  # 岛
                    for multi in coordinate:
                        polygon = []
                        for x in multi:
                            point = (x[0], x[1])  # 点的元组
                            polygon.append(coordinate_change(point))  # 坐标转换

                        if a == 1:
                            polygons_island.outer_polygon = polygon
                            a += 1

                        else:
                            polygons_island.holes.append(polygon)
                            a += 1
                    polygons.islands.append(polygons_island)

            all_polygons.append(polygons)

    # 求面积，但已经进行了坐标转换，得到的面积并不是真实值，而是相对值
    j = 1
    for i in all_polygons:
        print('图形', j, '的面积为：', i.area())
        j += 1

    return all_polygons


# 自带的填充多边形函数（用于对比）
def fill_polygons(polygons, draw, fill_color, outline_color):
    # 遍历每个多边形类
    for polygon in polygons:
        # 绘制外部多边形，填充为指定颜色，轮廓为指定颜色
        draw.polygon(polygon.outer_polygon, fill=fill_color, outline=outline_color)
        # 遍历每个内部孔洞多边形
        for hole in polygon.holes:
            # 绘制内部孔洞多边形，填充为白色，轮廓为指定颜色
            draw.polygon(hole, fill=(255, 255, 255), outline=outline_color)
        fill_polygons(polygon.islands, draw, fill_color, outline_color)


# 扫描线填充算法
def scanning_line(polygon, draw, fill_color):
    # 如果多边形为空，则不进行绘制
    if polygon == None:
        return
    # 定义扫描线范围
    # 计算多边形的最底部和最顶部的扫描线的Y坐标范围，即y_min和y_max。 min函数取最小，max函数取最大
    y_min = int(min(v[1] for v in polygon))
    y_max = int(max(v[1] for v in polygon))

    # 初始化活动边表
    # 用于存储当前扫描线与多边形边界的交点的数据结构,用于在后续步骤中存储交点的X坐标对
    active_edges = []

    # 扫描线算法主循环
    for y in range(y_min, y_max + 1):
        # 从y_min到y_max的每个扫描线逐一进行操作。

        # 寻找当前扫描线与多边形各边的交点，将这些交点的X坐标存储在一个列表中。
        intersections = []
        #  寻找所有边与扫描线的交点
        for i in range(len(polygon)):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % len(polygon)]

            # 计算交点
            if y1 <= y < y2 or y2 <= y < y1:
                if y2 - y1 != 0:
                    x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                    intersections.append(x)
        # 对交点列表进行排序，按照X坐标的升序排列。直接调用sort函数实现排序
        intersections.sort()

        for i in range(0, len(intersections), 2):
            x1 = int(intersections[i])
            x2 = int(intersections[i + 1])

            for x in range(x1, x2 + 1):
                # 一个点一个的画
                draw.point((x, y), fill=fill_color)


# 扫描线绘制所有多边形
def draw_for_scanning_line(class_polygons, draw, fill_color):
    scanning_line(class_polygons.outer_polygon, draw, fill_color)
    for hole in class_polygons.holes:
        scanning_line(hole, draw, fill_color=(255, 255, 255))
    for island in class_polygons.islands:
        draw_for_scanning_line(island, draw, fill_color)  # 岛需要进行递归调用


# 判断一个点是否在裁剪边的内侧
def is_inside(point, clip_start, clip_end):
    # 计算点和裁剪边的叉积，如果为正，说明点在裁剪边的左侧，即内侧
    return ((clip_end[0] - clip_start[0]) * (point[1] - clip_start[1]) >
            (clip_end[1] - clip_start[1]) * (point[0] - clip_start[0]))


# 计算两条线段的交点
def get_intersection(clip_start, clip_end, poly_start, poly_end):
    # 计算两条线段的方向向量
    clip_vector = [clip_start[0] - clip_end[0], clip_start[1] - clip_end[1]]
    poly_vector = [poly_start[0] - poly_end[0], poly_start[1] - poly_end[1]]
    # 计算两条线段的常数项
    clip_const = clip_start[0] * clip_end[1] - clip_start[1] * clip_end[0]
    poly_const = poly_start[0] * poly_end[1] - poly_start[1] * poly_end[0]
    # 计算两条线段的交点的分母
    denom = 1.0 / (clip_vector[0] * poly_vector[1] - clip_vector[1] * poly_vector[0])
    # 返回交点的坐标
    return ((clip_const * poly_vector[0] - poly_const * clip_vector[0]) * denom,
            (clip_const * poly_vector[1] - poly_const * clip_vector[1]) * denom)


# Sutherland-Hodgman裁剪算法
def clip_polygon(input_polygon, input_clipper):
    # 删除多边形列表的最后一个点元素，因为这些多边形是闭合的点集
    cropping = input_polygon[:]
    clipper = input_clipper[:]
    del cropping[-1]
    del clipper[-1]
    # 初始化输出列表为原始多边形的顶点列表
    output_list = cropping
    # 取裁剪多边形的最后一个顶点作为第一个裁剪边的起点
    clip_start = clipper[-1]

    # 遍历裁剪多边形的每个顶点
    for clip_vertex in clipper:
        # 取当前顶点作为裁剪边的终点
        clip_end = clip_vertex
        # 将输出列表作为输入列表
        input_list = output_list

        # 判断多边形是否相交，如果不相交则直接返回空值
        if len(input_list) == 0:
            return None

        output_list = []
        # 取输入列表的最后一个顶点作为第一个多边形边的起点
        poly_start = input_list[-1]

        # 遍历输入列表的每个顶点
        for poly_vertex in input_list:
            # 取当前顶点作为多边形边的终点
            poly_end = poly_vertex
            # 判断多边形边的终点是否在裁剪边的内侧
            if is_inside(poly_end, clip_start, clip_end):
                # 如果多边形边的起点不在裁剪边的内侧，说明有交点，将交点加入输出列表
                if not is_inside(poly_start, clip_start, clip_end):
                    output_list.append(get_intersection(clip_start, clip_end, poly_start, poly_end))
                # 将多边形边的终点加入输出列表
                output_list.append(poly_end)
            # 如果多边形边的起点在裁剪边的内侧，说明有交点，将交点加入输出列表
            elif is_inside(poly_start, clip_start, clip_end):
                output_list.append(get_intersection(clip_start, clip_end, poly_start, poly_end))
            # 更新多边形边的起点为当前顶点
            poly_start = poly_vertex
        # 更新裁剪边的起点为当前顶点
        clip_start = clip_vertex

    # 返回输出列表，即裁剪后的多边形的顶点列表
    return output_list


# 对所有多边形进行裁剪
def clip_all_polygons(polygons, clip):
    clip_result = new_polygon()
    # 最外层
    clip_out = clip_polygon(clip.outer_polygon, polygons.outer_polygon)
    clip_result.outer_polygon = clip_out

    # 洞
    for hole in polygons.holes:
        # 洞坐标为逆时针，先转换成顺时针
        hole_turn = hole[::-1]
        clip_hole = clip_polygon(clip.outer_polygon, hole_turn)
        clip_result.holes.append(clip_hole)

    # 岛
    for island in polygons.islands:
        clip_result.islands.append(clip_all_polygons(island, clip))

    return clip_result


if __name__ == '__main__':
    # 创建一个空白的图像
    img = Image.new("RGB", (2500, 2500), (255, 255, 255))
    # 创建一个绘图对象
    draw = ImageDraw.Draw(img)

    file_json = open('new_polygon1.json', 'r', encoding='gb18030', errors='ignore')
    data_json = json.loads(file_json.read())
    file_json.close()

    # 1
    # 读取geojson文件中的多边形内容，并计算面积
    all_polygons = read_file_and_get_area(data_json)

    # 2
    # 扫描线填充算法
    # 绘制多边形
    for polygons in all_polygons:
        draw_for_scanning_line(polygons, draw, fill_color=(0, 0, 255))

    # PIL库自带的多边形填充
    # fill_polygons(all_polygons, draw, fill_color=(255, 0, 0), outline_color=(0, 0, 0))

    # 显示填充结果
    img.show()

    # 3
    # Sutherland-Hodgman裁剪算法
    # 创建一个裁剪对象
    clip = new_polygon()
    clip.outer_polygon = [(1250.0, 1750.0), (1450.0, 1750.0), (1450.0, 1350.0), (1250.0, 1350.0), (1250.0, 1750.0)]

    # 绘制裁剪多边形
    scanning_line(clip.outer_polygon, draw, fill_color=(0, 255, 0))

    # 裁剪并绘制裁剪后的多边形
    all_clip_result = []
    for polygons in all_polygons:
        all_clip_result.append(clip_all_polygons(polygons, clip))

    for polygons in all_clip_result:
        draw_for_scanning_line(polygons, draw, fill_color=(255, 0, 0))

    # 显示和保存图像
    img.show()
    # img.save("polygons.png")
