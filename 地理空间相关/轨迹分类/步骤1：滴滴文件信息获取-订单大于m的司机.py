import os

f = open('gps_20161109.csv', encoding='utf-8', mode='r')
newf = open(r'.\司机订单大于20的集合\11-09\大于20的司机id11-09.txt', mode='x')
driver_num = 0
Order_num = 0
line_num = 0
driver_id = ''
Order_id = ''
driverlist = []
orderlist = []
order_num_more_ten = 0
for line in f:
    line_num += 1

    line = line.rstrip('\n').split(',')

    if driver_id != line[0]:
        if len(orderlist)+1 > 20:
            order_num_more_ten += 1
            print(driver_id, '司机有', len(orderlist), '个订单')
            newf.write(driver_id + '\n')
        driver_num += 1
        driver_id = line[0]
        orderlist = []
    else:
        if line[1] not in orderlist:
            orderlist.append(line[1])
f.close()
newf.close()
print('数据集中共有', line_num, '行数据')
print('数据集中共有', driver_num, '位司机在开车')  # 17855位司机
# print('20161001数据集中共有',Order_num,'个订单')
print('11-09号数据集中订单大于20的司机有', order_num_more_ten, '个')
# 20161001数据集中订单大于10的司机有 3839 个
# 20161001数据集中订单大于15的司机有 1265 个
# 20161001数据集中订单大于20的司机有 261 个
# 20161001数据集中订单大于25的司机有 34 个


driver = open(r'.\司机订单大于20的集合\11-09\大于20的司机id11-09.txt', mode='r')
f = open('gps_20161109.csv', encoding='utf-8', mode='r')
driver_id = driver.readline().rstrip('\n')
nem = 0
for line in f:
    line1 = line.rstrip('\n').split(',')
    if driver_id == line1[0]:

        if nem == 0:
            newf = open(r'.\司机订单大于20的集合\11-09\司机' + driver_id + '.csv',
                        mode='w', encoding='utf-8')
            newf.write('driver_id' + ',' + 'order_id' + ',' + 'time' + ',' + 'long_lat\n')
            datalist = []
            datalist.append([line1[0], line1[1], int(line1[2]), line1[3], line1[4]])
            nem = 1
        elif nem == 1:
            datalist.append([line1[0], line1[1], int(line1[2]), line1[3], line1[4]])
    else:
        if nem == 1:
            datalist.sort(key=lambda x: (x[1], x[2]))
            for data in datalist:
                newf.write(data[0] + ',' + data[1] + ',' + str(data[2]) + ',' + '"' + data[3] + ',' + data[
                    4] + '"' + '\n')  # 直接处理成高德地图要求的数据格式
            newf.close()
            driver_id = driver.readline().rstrip('\n')
            print(driver_id)
            nem = 0
f.close()
