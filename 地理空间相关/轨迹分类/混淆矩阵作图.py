import numpy as np
import matplotlib.pyplot as plt
from pylab import *

plt.rcParams['font.sans-serif'] = ['SimHei']


def read():
    name_list = ['危险（预测）', '相对危险（预测）', '相对安全（预测）', '安全（预测）']
    time11 = [17, 16, 8, 0]
    time22 = [6, 509, 461, 23]
    time33 = [1, 131, 2371, 160]
    time44 = [0, 10, 367, 331]
    '''
    time1 = [17/sum(time11), 16/sum(time11), 8/sum(time11), 0/sum(time11)]
    time2 = [6/sum(time22), 509/sum(time22), 461/sum(time22), 23/sum(time22)]
    time3 = [1/sum(time33), 131/sum(time33), 2371/sum(time33), 160/sum(time33)]
    time4 = [0/sum(time44), 10/sum(time44), 367/sum(time44), 331/sum(time44)]
    '''
    time1 = [17/sum(time11), 6/sum(time22), 1/sum(time33), 0/sum(time44)]
    time2 = [16/sum(time11), 509/sum(time22), 131/sum(time33), 10/sum(time44)]
    time3 = [8/sum(time11), 461/sum(time22), 2371/sum(time33), 367/sum(time44)]
    time4 = [0/sum(time11), 23/sum(time22), 160/sum(time33), 331/sum(time44)]

    location = np.arange(len(name_list))
    width = 0.2

    plt.figure(figsize=(12, 4))
    plt.bar(location, time1, tick_label=name_list, width=width, label="危险（真实）", alpha=0.8, color="w", edgecolor="k", hatch="o")
    for a, b in zip(location, time1):
        plt.text(a, b + 0.05, '%.3f' % b, ha='center', va='bottom', fontsize=7)
    plt.bar(location + width, time2, tick_label=name_list, width=width, label="相对危险（真实）", alpha=0.8, color="w",
            edgecolor="k", hatch=".....")
    for a, b in zip(location + width, time2):
        plt.text(a, b + 0.05, '%.3f' % b, ha='center', va='bottom', fontsize=7)
    plt.bar(location + width * 2, time3, tick_label=name_list, width=width, label="相对安全（真实）", alpha=0.8, color="w",
            edgecolor="k", hatch="/////")
    for a, b in zip(location + width * 2, time3):
        plt.text(a, b + 0.05, '%.3f' % b, ha='center', va='bottom', fontsize=7)
    plt.bar(location + width * 3, time4, tick_label=name_list, width=width, label="安全（真实）", alpha=0.8, color="w",
            edgecolor="k", hatch="x")
    for a, b in zip(location + width * 3, time4):
        plt.text(a, b + 0.05, '%.3f' % b, ha='center', va='bottom', fontsize=7)

    plt.ylim(0, 1)
    plt.legend(loc=1)
    plt.show()






if __name__ == '__main__':
    read()





    
    '''
    C++    https://blog.csdn.net/l691899397/article/details/52291909 卷积神经网络map变化    
    要氪金    https://blog.csdn.net/blogshinelee/article/details/84826837 直观理解神经网络最后一层全连接+Softmax 
    纯公式    https://blog.csdn.net/GoodShot/article/details/79330545 对于全连接层的理解 全连接层的推导   
    ？           现在的趋势是尽量避免全连接，目前主流的一个方法是全局平均值。
    ？哪里？？     也就是最后那一层的feature map（最后一层卷积的输出结果），直接求平均值。有多少种分类就训练多少层，这十个数字就是对应的概率或者叫置信度。
    要氪金    https://blog.csdn.net/whyymlm/article/details/79739840 CNN（卷积层convolutional layer，激励层activating layer，池化层pooling，全连接层fully connected）
    根本看不懂    https://blog.csdn.net/boon_228/article/details/81238091 理解卷积神经网络CNN中的特征图 feature map    
    '''
