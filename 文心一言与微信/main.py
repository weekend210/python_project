# -*- coding: utf-8 -*-

from uiautomation import WindowControl  # 引入uiautomation库中的WindowControl类，用来进行图像识别和模拟操作
import requests
import json


API_KEY = "Iy0terGLkhiZi6IzyD4CmSCh"
SECRET_KEY = "OFuDhSkLwuCculD0UPlH3RQNgk54ZxF2"


def chat(messages):
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token=" + get_access_token()

    payload = json.dumps({
        "messages": messages,
        "disable_search": False,
        "enable_citation": False
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response


def get_access_token():
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))

# 文心一言
def requests_to_baidu(input_questions):
    messages = []
    user = 'user'

    question1 = {
        'role': user,
        'content': input_questions
    }

    messages.append(question1)
    # 通过API请求回答
    result = json.loads(chat(messages).text)

    return result['result']


# 微信回复
def wechat_respond():
    # 绑定微信主窗口
    wx = WindowControl(
        Name='微信',
        searchDepth=1
    )
    # 切换窗口
    wx.ListControl()
    wx.SwitchToThisWindow()
    # 寻找会话控件绑定
    hw = wx.ListControl(Name='会话')

    # 死循环接收消息
    while True:
        # 从查找未读消息
        we = hw.TextControl(searchDepth=4)

        # 死循环维持，没有超时报错
        while not we.Exists():
            pass

        # 存在未读消息
        if we.Name:
            # 点击未读消息
            we.Click(simulateMove=False)
            # 读取最后一条消息
            last_msg = wx.ListControl(Name='消息').GetChildren()[-1].Name

            responds = []

            # 文心一言回复
            responds.append(requests_to_baidu(last_msg))

            # 能够匹配到数据时
            if responds:
                # 将数据输入
                # 替换换行符号
                wx.SendKeys(responds[0].replace('{br}', '{Shift}{Enter}'), waitTime=1)
                # 发送消息 回车键
                wx.SendKeys('{Enter}', waitTime=1)

                # 通过消息匹配检索会话栏的联系人
                wx.TextControl(SubName=responds[0][:5]).RightClick()
            # 没有匹配到数据时
            else:
                wx.SendKeys('搜寻回复失败，请重试', waitTime=1)
                wx.SendKeys('{Enter}', waitTime=1)
                wx.TextControl(SubName=last_msg[:5]).RightClick()

if __name__ == '__main__':
    wechat_respond()

