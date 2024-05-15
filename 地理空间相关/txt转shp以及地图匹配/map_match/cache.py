"""

缓存计算好的dijkstra距离和路网轨迹

"""

print('load cache')

DISTANCE_CACHE = {}


def get_distance_from_cache(source, target):
    """
    从缓存中获得距离
    """
    if (source, target) in DISTANCE_CACHE:
        return DISTANCE_CACHE[(source, target)]
    else:
        return None


def save_distance_to_cache(source, target, distance, vertex_path, road_path):
    """
    将距离和路网路径保存到缓冲中
    """
    if (source, target) in DISTANCE_CACHE:
        assert(get_distance_from_cache(source, target)[0] == distance)

    DISTANCE_CACHE[(source, target)] = (distance, vertex_path, road_path)


def clear_cache():
    """
    清空缓存数据
    """
    DISTANCE_CACHE = {}


def get_unique_id(road_id, fraction):
    return str(road_id) + '_' + str(int(fraction * 10000000))
