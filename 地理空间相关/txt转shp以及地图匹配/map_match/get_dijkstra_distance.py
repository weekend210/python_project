"""

获得两点间的dijkstra距离

"""
import fiona
import networkx as nx
from cache import get_distance_from_cache, save_distance_to_cache, get_unique_id

print('load road')

# namedtuple 返回具有命名字段的元组的新子类。
# CPointRec = namedtuple('CPointRec', ["log_x", "log_y", "p_x", "p_y", "road_id", "log_id", "source", "target",
#                                     "weight", "fraction", "v", "log_time", "track_id", "car_id"])

MAX_V = 45  # 设置最大行驶速度
MAX_DIS = 6000  # 设置最大前后轨迹点间的距离
ROAD_GRAPH = None


def init_road_graph(road_path):
    global ROAD_GRAPH
    # 读取路网数据
    road_features = fiona.open(road_path)
    road_graph = nx.DiGraph()

    print(len(road_features))
    i = 0

    for feature in road_features:
        road_id = int(feature['id'])
        properties = feature['properties']
        source = int(properties['from_'])
        target = int(properties['to_'])
        weight = float(properties['length'])  # 以道路的长度“length”字段作为权重
        road_graph.add_edge(source, target, weight=weight, road_id=road_id)

        i+=1
        print(i)

    ROAD_GRAPH = road_graph


def get_dijkstra_distance(pre_closest_point, now_closest_point, road_path, cufoff=5000):
    if ROAD_GRAPH is None:
        print('init road_graph')
        # 调用init_road_graph()函数构建路网权重图
        init_road_graph(road_path)

    """
    获得两个点之间的dijkstra距离

    如果两个点之间的距离>cufoff，则认为两点之间的距离为MAX_DIS，这个操作是为了提高效率。

    Parameters:
    -----------
    pre_closest_point : CPointRec
        起点
    now_closest_point : CPointRec
        终点

    """
    pre_road_id = pre_closest_point.road_id
    pre_source = pre_closest_point.source
    pre_target = pre_closest_point.target
    pre_fraction = pre_closest_point.fraction
    pre_weight = pre_closest_point.weight

    now_road_id = now_closest_point.road_id
    now_source = now_closest_point.source
    now_target = now_closest_point.target
    now_fraction = now_closest_point.fraction
    now_weight = now_closest_point.weight

    if not (ROAD_GRAPH[pre_source][pre_target]['weight'] == pre_weight) and (ROAD_GRAPH[now_source][now_target]['weight'] == now_weight):
        dis = 50
        return dis
    # assert (ROAD_GRAPH[pre_source][pre_target]['weight'] == pre_weight)
    # assert (ROAD_GRAPH[now_source][now_target]['weight'] == now_weight)
    else:
        source_id = get_unique_id(pre_road_id, pre_fraction)  # 唯一标识一个起点
        target_id = get_unique_id(now_road_id, now_fraction)  # 唯一标识一个终点

        # if cached
        result = get_distance_from_cache(source_id, target_id)
        if result:
            # print('from cache')
            return result[0]

        # if not cached
        if pre_road_id == now_road_id:
            if now_fraction <= pre_fraction:
                save_distance_to_cache(source_id, target_id, MAX_DIS, None, None)
                return MAX_DIS
            else:
                dis = (now_fraction - pre_fraction) * now_weight
                save_distance_to_cache(source_id, target_id, dis, ['a', 'b'], [pre_road_id])
                return dis

        pre_id = 'a'
        now_id = 'b'

        if pre_fraction == 0:
            pre_id = pre_source
        elif pre_fraction == 1:
            pre_id = pre_target
        else:
            ROAD_GRAPH.add_edge(pre_source, pre_id, weight=pre_fraction * pre_weight, road_id=pre_road_id)
            ROAD_GRAPH.add_edge(pre_id, pre_target, weight=(1 - pre_fraction) * pre_weight, road_id=pre_road_id)

        if now_fraction == 0:
            now_id = now_source
        elif now_fraction == 1:
            now_id = now_target
        else:
            ROAD_GRAPH.add_edge(now_source, now_id, weight=now_fraction * now_weight, road_id=now_road_id)
            ROAD_GRAPH.add_edge(now_id, now_target, weight=(1 - now_fraction) * now_weight, road_id=now_road_id)

        dis = MAX_DIS
        vertex_path = None

        length, path = nx.single_source_dijkstra(ROAD_GRAPH, pre_id, cutoff=cufoff)
        try:
            dis = length[now_id]
            vertex_path = path[now_id]
        except KeyError:
            pass

        if vertex_path is None:
            save_distance_to_cache(source_id, target_id, dis, None, None)
        else:
            road_path = ['x']
            for i in range(1, len(vertex_path)):
                pre_vertex = vertex_path[i - 1]
                now_vertex = vertex_path[i]
                road_id = ROAD_GRAPH[pre_vertex][now_vertex]['road_id']
                if road_id != road_path[-1]:
                    road_path.append(road_id)

            save_distance_to_cache(source_id, target_id, dis, vertex_path, road_path[1:])

        if pre_fraction != 0 and pre_fraction != 1:
            ROAD_GRAPH.remove_edge(pre_source, pre_id)
            ROAD_GRAPH.remove_edge(pre_id, pre_target)

        if now_fraction != 0 and now_fraction != 1:
            ROAD_GRAPH.remove_edge(now_source, now_id)
            ROAD_GRAPH.remove_edge(now_id, now_target)

        return dis


def get_connected_path(match_point_list):
    """
    获得match_list对应的connected vertex path和connected road path

    Parameters:
    -------------
    match_point_list: list
        匹配好的点列表
    Returns:
    ----------
    connected_vertex_path: list
        轨迹按顺序经过的vertex
    connected_road_path: list
        轨迹按顺序经过的road

    """

    pre_point = match_point_list[0]
    connected_vertex_path = ['x']
    connected_road_path = ['x']
    # 遍历匹配点列表剩余的其他点
    for now_point in match_point_list[1:]:
        # 调用外部get_unique_id()函数
        source_id = get_unique_id(pre_point.road_id, pre_point.fraction)
        target_id = get_unique_id(now_point.road_id, now_point.fraction)

        # 调用外部get_distance_from_cache()函数
        result = get_distance_from_cache(source_id, target_id)
        assert (result is not None)

        dis, vertex_path, road_path = result

        assert (vertex_path is not None)
        assert (road_path is not None)
        # 计算记录前后两个轨迹点经过的时间
        elapse_time = float(now_point.log_time) - float(pre_point.log_time)
        if elapse_time * MAX_V < dis:
            return None, None  # 超速行驶

        # 遍历添加符合条件的vertex
        for vertex in vertex_path:
            if vertex in ['a', 'b']:
                continue
            else:
                if vertex != connected_vertex_path[-1]:
                    connected_vertex_path.append(int(vertex))
        # 遍历添加符合条件的road
        for road in road_path:
            if road != connected_road_path[-1]:
                connected_road_path.append(int(road))
        pre_point = now_point

    return connected_vertex_path[1:], connected_road_path[1:]
