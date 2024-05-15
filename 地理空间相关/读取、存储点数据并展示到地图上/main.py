import shapefile
import os
import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as msgbox
import folium
import subprocess

# 读取shp文件的点数据，返回点的二维数组
def read_shp_points(file):
    border_shape = file
    border = border_shape.shapes()
    border_points = [] # 存原始点数据[[[x1,y1]],[[x2,y2]],...,...]
    points_xy = [] # 存修改后的只包含点的二维数组[[x1,y1],[x2,y2]，...，...]
    s = 0
    for i in border:
        border_points.append(i.points)
        points_xy.append(border_points[s][0])
        s += 1
    print(points_xy)

    # 返回点的二维数组
    return points_xy

# 数据库初始化（读取文件、写入数据库）
def database_initialized():
    # 实例化
    root = tk.Tk()
    root.withdraw()
    # 获取文件夹路径
    # f_path = './MemPnts/MemPnts.shp'
    f_path = filedialog.askopenfilename(title='请选择一个文件', initialdir=r'D:\a', filetypes=[(
"shp", ".shp"),('All Files', '*')], defaultextension='.tif', multiple=True)
    print('\n获取的文件地址：', f_path[0])
    # 文件读取格式为只读
    file = shapefile.Reader(f_path[0])
    points = read_shp_points(file)

    data = open("test.txt", 'w+')
    # 文件头：编码格式
    print(file.encoding, file=data)
    # 数据索引：点总个数
    print(file.numRecords, file=data)
    id = 0
    for i in points:
        writer_line = str(id) + '\t' + str(i[0]) + '\t' + str(i[1])
        id += 1
        # print(writer_line)
        print(writer_line, file=data)
    return points

#将文件数据写入数组[['序号','经度','纬度'],['...','...','...'],...]
def read_file(filename):
    file_txt = open(filename, 'r+')
    data = file_txt.readline()
    data = data.strip('\n')
    data_sp = data.split('\t')
    data_points = []
    data_points.append(data_sp)
    while data:
        data = file_txt.readline()
        data = ''.join(data).strip('\n')
        data_sp = data.split('\t')
        data_points.append(data_sp)
    #print(data_points)
    return data_points


if __name__ == '__main__':
    points = database_initialized()
    msgbox.showinfo('提示','数据写入成功,请打开数据文件test.txt\n查询成功后关闭查询窗口将会自动打开地图')
    #打开GUI程序，并等待程序结束
    process = subprocess.Popen(["GUI.exe"])
    process.wait()
    openfile = os.path.isfile("temporary_files.txt")
    if openfile is True:
        data_points = read_file("temporary_files.txt")

        bj_map = folium.Map(location=[data_points[0][2], data_points[0][1]], zoom_start=12, tiles='Stamen Terrain')
        folium.Marker(
            location=[data_points[0][2], data_points[0][1]],
            popup='中心点',
            icon=folium.Icon(icon='cloud')
        ).add_to(bj_map)

        mid_point_num = int(data_points[0][0])
        if len(data_points)<41:
            if mid_point_num < 20:
                for i in range(1, mid_point_num+1):
                    pop_str = "前第" + str(i) + "个点"
                    folium.Marker(
                        location=[data_points[i][2], data_points[i][1]],
                        popup=pop_str,
                        icon=folium.Icon(color='red', icon='info-sign')  # 标记颜色  图标
                    ).add_to(bj_map)

                for i in range(mid_point_num+1, mid_point_num+21):
                    pop_str = "后第" + str(i - 20) + "个点"
                    folium.Marker(
                        location=[data_points[i][2], data_points[i][1]],
                        popup=pop_str,
                        icon=folium.Icon(color='green', icon='info-sign')  # 标记颜色  图标
                    ).add_to(bj_map)

            else:
                for i in range(1, 21):
                    pop_str = "前第" + str(i) + "个点"
                    folium.Marker(
                        location=[data_points[i][2], data_points[i][1]],
                        popup=pop_str,
                        icon=folium.Icon(color='red', icon='info-sign')  # 标记颜色  图标
                    ).add_to(bj_map)

                last_point = int(data_points[len(data_points)-2][0])
                for i in range(21,last_point - mid_point_num+21):
                    pop_str = "后第" + str(i - 20) + "个点"
                    folium.Marker(
                        location=[data_points[i][2], data_points[i][1]],
                        popup=pop_str,
                        icon=folium.Icon(color='green', icon='info-sign')  # 标记颜色  图标
                    ).add_to(bj_map)

        else:
            for i in range(1,21):
                pop_str = "前第"+str(i)+"个点"
                folium.Marker(
                    location=[data_points[i][2], data_points[i][1]],
                    popup=pop_str,
                    icon=folium.Icon(color='red', icon='info-sign')  # 标记颜色  图标
                ).add_to(bj_map)

            for i in range(21,41):
                pop_str = "后第" + str(i-20) + "个点"
                folium.Marker(
                    location=[data_points[i][2], data_points[i][1]],
                    popup=pop_str,
                    icon=folium.Icon(color='green', icon='info-sign')  # 标记颜色  图标
                ).add_to(bj_map)

        bj_map.save('to_map.html')
        os.startfile(r"to_map.html")
        os.remove('./temporary_files.txt')
