import cv2
import numpy as np
import math
from matplotlib import pyplot as plt
#from skimage.transform import resize

# 定义最少匹配点数目
MIN = 10

img1 = cv2.imread("./img/airport1.png")
img2 = cv2.imread("./img/airport2.png")


# 圆柱投影
# f为圆柱半径，每次匹配需要调节f
def cylindrical_projection(img, f):
    rows = img.shape[0]
    cols = img.shape[1]

    blank = np.zeros_like(img)
    center_x = int(cols / 2)
    center_y = int(rows / 2)

    for y in range(rows):
        for x in range(cols):
            theta = math.atan((x - center_x) / f)
            point_x = int(f * math.tan((x - center_x) / f) + center_x)
            point_y = int((y - center_y) / math.cos(theta) + center_y)

            if point_x >= cols or point_x < 0 or point_y >= rows or point_y < 0:
                pass
            else:
                blank[y, x, :] = img[point_y, point_x, :]
    return blank


# 创建SURF对象
surf = cv2.xfeatures2d.SURF_create(100, nOctaves=4, extended=False, upright=False)

# 柱面投影
img1 = cylindrical_projection(img1, 1500)
img2 = cylindrical_projection(img2, 1500)

# 提取特征点、特征描述符
kp1, descrip1 = surf.detectAndCompute(img1, None)
kp2, descrip2 = surf.detectAndCompute(img2, None)

# FLANN快速匹配器
FLANN_INDEX_KDTREE = 0
indexParams = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
searchParams = dict(checks=50)

flann = cv2.FlannBasedMatcher(indexParams, searchParams)
match = flann.knnMatch(descrip1, descrip2, k=2)

# 获取符合条件的匹配点
good = []
for i, (m, n) in enumerate(match):
    if (m.distance < 0.75 * n.distance):
        good.append(m)

if len(good) > MIN:
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    ano_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    # 实现单应性匹配，返回关键点srcPoints做M变换能变到dstPoints的位置
    M, mask = cv2.findHomography(src_pts, ano_pts, cv2.RANSAC, 5.0)
    # 对图片进行透视变换，变换视角。src是要变换的图片，np.linalg.inv(M)是单应性矩阵M的逆矩阵
    warpImg = cv2.warpPerspective(img2, np.linalg.inv(M), (img1.shape[1] + img2.shape[1], img2.shape[0]))
    rows, cols = img1.shape[:2]

    # 图像融合，进行加权处理

    for col in range(0, cols):
        if img1[:, col].any() and warpImg[:, col].any():  # 开始重叠的最左端
            left = col
            break
    for col in range(cols - 1, 0, -1):
        if img1[:, col].any() and warpImg[:, col].any():  # 重叠的最右一列
            right = col
            break

    res = np.zeros([rows, cols, 3], np.uint8)
    for row in range(0, rows):
        for col in range(0, cols):
            if not img1[row, col].any():  # 如果没有原图，用旋转的填充
                res[row, col] = warpImg[row, col]
            elif not warpImg[row, col].any():
                res[row, col] = img1[row, col]
            else:
                srcImgLen = float(abs(col - left))
                testImgLen = float(abs(col - right))
                alpha = srcImgLen / (srcImgLen + testImgLen)
                res[row, col] = np.clip(img1[row, col] * (1 - alpha) + warpImg[row, col] * alpha, 0, 255)

    warpImg[0:img1.shape[0], 0:img1.shape[1]] = res
    img4 = cv2.cvtColor(warpImg, cv2.COLOR_BGR2RGB)
    plt.imshow(img4, ), plt.show()
    cv2.imwrite("test12.png", warpImg)

else:
    print("not enough matches!")
