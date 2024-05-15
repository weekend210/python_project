import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

# 加载数据集
all_arrays_path = r'.\司机订单大于20的集合\11-09\all_arrays2.npy'
label_array_path = r'.\司机订单大于20的集合\11-09\label_arrays2.npy'


# 定义MLP模型类，输入维度为400（100*4），输出维度为2（驾驶员行为和行驶时间）
class MLP(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(MLP, self).__init__()
        # 定义三个全连接层，中间使用ReLU激活函数
        self.fc1 = nn.Linear(input_dim, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, output_dim)
        self.relu = nn.ReLU()

    def forward(self, x):
        # 前向传播，将输入x通过三个全连接层得到输出y
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        y = self.fc3(x)
        return y


# 加载数据，假设all_arrays2.npy和label_arrays2.npy已经存在
X = np.load(all_arrays_path)  # 加载司机行为数据，形状为(n, 1, 100, 4)
y = np.load(label_array_path)  # 加载司机行为标签数据，形状为(n, 2)
n = X.shape[0]  # 获取样本数量

# 将数据转换为torch张量，并将X的形状从(n, 1, 100, 4)变为(n, 400)
X = torch.from_numpy(X).float().view(n, -1)
y = torch.from_numpy(y).float()

# 划分训练集和测试集，比例为8:2
train_size = int(n * 0.8)
test_size = n - train_size
X_train, X_test = torch.split(X, [train_size, test_size])
y_train, y_test = torch.split(y, [train_size, test_size])

# 定义模型参数
input_dim = 400  # 输入维度
output_dim = 2  # 输出维度
lr = 0.01  # 学习率
epochs = 100  # 训练轮数
batch_size = 32  # 批量大小

# 创建模型实例
model = MLP(input_dim, output_dim)

# 定义损失函数，使用均方误差（MSE）
criterion = nn.MSELoss()

# 定义优化器，使用随机梯度下降（SGD）
optimizer = optim.SGD(model.parameters(), lr=lr)

# 训练模型
for epoch in range(epochs):
    # 打乱训练数据的顺序
    perm = torch.randperm(train_size)
    X_train = X_train[perm]
    y_train = y_train[perm]

    # 按批量进行训练
    for i in range(0, train_size, batch_size):
        # 获取一个批量的数据
        X_batch = X_train[i:i + batch_size]
        y_batch = y_train[i:i + batch_size]

        # 清空梯度
        optimizer.zero_grad()

        # 前向传播，得到预测值
        y_pred = model(X_batch)

        # 计算损失
        loss = criterion(y_pred, y_batch)

        # 反向传播，更新参数
        loss.backward()
        optimizer.step()

    # 在测试集上评估模型
    with torch.no_grad():
        # 得到测试集的预测值
        y_test_pred = model(X_test)

        # 计算测试集的损失
        test_loss = criterion(y_test_pred, y_test)

        # 打印训练轮数和测试集损失
        print(f"Epoch {epoch + 1}, Test Loss: {test_loss:.4f}")


# 定义一个函数，用于将预测值和真实值转换为列表
def convert_to_time_and_label(y_pred, y_true):
    # 初始化两个空列表，用于存储预测的行驶时间和驾驶员行为标签
    pred_time = []
    pred_label = []

    # 遍历预测值和真实值
    for pred, true in zip(y_pred, y_true):
        # 将预测值的第一个元素转换为行驶时间，单位为分钟
        time = pred[0] * 60
        # 将预测值的第二个元素转换为驾驶员行为标签，根据阈值划分为四种类别
        if pred[1] < 0.25:
            label = "安全"
        elif pred[1] < 0.5:
            label = "相对安全"
        elif pred[1] < 0.75:
            label = "相对危险"
        else:
            label = "危险"
        # 将行驶时间和驾驶员行为标签添加到对应的列表中
        pred_time.append(time)
        pred_label.append(label)

    # 返回一个元组，包含两个列表
    return (pred_time, pred_label)


# 调用这个函数，将测试集的预测值和真实值转换为列表，并保存到一个变量中
pred_time_and_label = convert_to_time_and_label(y_test_pred, y_test)

print(y_test_pred)
print(y_test)
print(type(y_test_pred))
print(type(y_test))


'''for i in range(len(y_test_pred)):
    print('',,,'')'''


# 将这个变量保存到一个文件中，以便后续使用

#np.save("pred_time_and_label.npy", pred_time_and_label)
