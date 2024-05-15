import os
import cv2
import numpy as np
import xlsxwriter as xw

class Nstr:
    def __init__(self, arg):
       self.x=arg
    def __sub__(self,other):
        c=self.x.replace(other.x,"")
        return c

##############################
# 感知哈希算法
def pHash(img):
    # 缩放32*32
    img = cv2.resize(img, (128, 128))  # , interpolation=cv2.INTER_CUBIC

    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 将灰度图转为浮点型，再进行dct变换
    dct = cv2.dct(np.float32(gray))
    # opencv实现的掩码操作
    dct_roi = dct[0:8, 0:8]

    hash = []
    avreage = np.mean(dct_roi)
    for i in range(dct_roi.shape[0]):
        for j in range(dct_roi.shape[1]):
            if dct_roi[i, j] > avreage:
                hash.append(1)
            else:
                hash.append(0)
    return hash

# Hash值对比
def cmpHash(hash1, hash2):
    # 算法中1和0顺序组合起来的即是图片的指纹hash。顺序不固定，但是比较的时候必须是相同的顺序。
    # 对比两幅图的指纹，计算汉明距离，即两个64位的hash值有多少是不一样的，不同的位数越小，图片越相似
    # 汉明距离：一组二进制数据变成另一组数据所需要的步骤，可以衡量两图的差异，汉明距离越小，则相似度越高。汉明距离为0，即两张图片完全一样
    n = 0
    # hash长度不同则返回-1代表传参出错
    if len(hash1) != len(hash2):
        return -1
    # 遍历判断
    for i in range(len(hash1)):
        # 不相等则n计数+1，n最终为相似度
        if hash1[i] != hash2[i]:
            n = n + 1
    return n

##############################

def xw_toExcel(data):  # xlsxwriter库储存数据到excel
    workbook = xw.Workbook("Attendance_Record.xlsx")  # 创建工作簿
    worksheet1 = workbook.add_worksheet("sheet1")  # 创建子表
    worksheet1.activate()  # 激活表
    title = ['学号', '考勤']  # 设置表头
    worksheet1.write_row('A1', title)  # 从A1单元格开始写入表头
    i = 2  # 从第二行开始写入数据
    for j in range(len(data)):
        insertData = [data[j]["id"], data[j]["attendance"]]
        row = 'A' + str(i)
        worksheet1.write_row(row, insertData)
        i += 1
    workbook.close()  # 关闭表

# 图片中人脸识别
def Face_Detect_Pic(image):
    #转灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    #训练一组人脸
    face_detector = cv2.CascadeClassifier(
        "D:\opencv\opencv\sources\data\haarcascades\haarcascade_frontalface_alt.xml")
    #检测人脸（用灰度图检测，返回人脸矩形坐标(4个角)）
    faces_rect = face_detector.detectMultiScale(gray, 1.05, 7)
    #                                          灰度图  图像尺寸缩小比例  至少检测次数（若为3，表示一个目标至少检测到3次才是真正目标）

    print("人脸矩形坐标faces_rect：", faces_rect)

    # 返回矩形框
    return faces_rect

#根据文件对比人脸
def Comparing_Faces(img,path_face):
    #循环读文件，并对两张图片进行比较
    for item in os.scandir(path_face):
        img_location = cv2.imread(item.path)
        #计算出哈希差值
        result = cmpHash(pHash(img),pHash(img_location))
        print(result)
        #设置阈值
        if result <= 22:
            #仅输出文件名字，把前缀后缀给删了
            name = Nstr(item.path) - Nstr(path_face)
            name = Nstr(name) - Nstr(".jpg")
            return name
    #没有匹配人脸，返回NULL
    return None

#人脸比对,并写入文件
def Image_Face_Recognition(img,path_name):
    out_img = img.copy()
    # 人脸识别得到矩形框数组
    result = Face_Detect_Pic(img)

    # 储存考勤情况数组格式：储存字典的数组
    # [{"学号"，"考勤"}]
    # 将所有文件名写入数组
    attendance = []
    for item in os.scandir(path_name):
        #删除路径的前缀后缀，只留下文件名
        name = Nstr(item.path) - Nstr(path_name)
        name = Nstr(name) - Nstr(".jpg")
        # 创建字典
        dict_mid = {'id':name,'attendance':'缺勤'}
        attendance.append(dict_mid)

    # 在图像中添加矩形框，同时对框中的人脸进行识别，并输出名字
    for x, y, w, h in result:
        cv2.rectangle(out_img, (x, y), (x + w, y + h), (0, 0, 255), 3)  # 画出矩形框

        # 裁剪出人脸
        cropped = img[x:x + w, y:y + h]

        # 对人脸进行识别，返回名字
        name_result = Comparing_Faces(cropped, path_name)
        if name_result != None:
            # 输出名字
            cv2.putText(out_img, name_result, (x + w + 10, y - 10),
                        cv2.FONT_HERSHEY_COMPLEX, 1.0, (255, 128, 0), 2)

            # 更改该名字的考勤情况
            for i in attendance:
                if i['id'] == name_result:
                    i['attendance'] = '已到'
                    break

        else:
            cv2.putText(out_img, "unknow", (x + w + 10, y - 10),
                        cv2.FONT_HERSHEY_COMPLEX, 1.0, (255, 128, 0), 2)

    #写入excel表格
    xw_toExcel(attendance)

    return out_img


# 摄像头中人脸识别
def Face_Detect_Cam(path_name):
    # 打开摄像头
    capture = cv2.VideoCapture(0)  # 0：本地摄像头    1：外接摄像头
    files = []#存地址
    file_name = []#存姓名

    while (True):
        #按帧读取视频
        ret, frame = capture.read()  # frame为每一帧的图像

        #左右翻转（否则向左右移动的时候，对象右左移动，反着移）
        frame = cv2.flip(frame, 1)

        out_img = Image_Face_Recognition(frame,path_name)

        cv2.imshow("out_img",out_img)

        # q键退出（设置读帧间隔时间）
        if cv2.waitKey(1) & 0XFF == ord("q"):
            return


if __name__ == '__main__':
    path1 = "./img/"
    Face_Detect_Cam(path1)
    cv2.waitKey(0)








