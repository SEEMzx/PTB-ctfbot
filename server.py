import json
import operator
import os
from sanic import Sanic
import re
import requests
import random_topic as tm

app = Sanic('qqbot')


def send_group_msg(msg, gc):
    ret = {
        'action': 'send_group_msg',
        'params': {
            'group_id': gc,
            'message': msg,
        }
    }
    return ret


def send_private_msg(msg, uin):
    ret = {
        'action': 'send_private_msg',
        'params': {
            'user_id': uin,
            'message': msg
        }
    }
    return ret


# 积分
def integral(uin):
    with open(file, 'r') as f:
        data = json.loads(f.read())
        if uin in data:
            data[uin] += 1
        else:
            data[uin] = 1
    with open(file, 'w') as f1:
        f1.write(json.dumps(data))


# 排行榜
def integral_list():
    with open(file, 'r') as f:
        d = json.loads(f.read())
    if d:
        data = sorted(d.items(), key=operator.itemgetter(1), reverse=True)
        msg_list = [f"第{x}名:{y[0]}\t积分:{y[1]}" for x, y in enumerate(data, 1)]
        return '-------积分排行榜-------\n' + '\n'.join(msg_list)
    else:
        return '暂时还无人上榜，还请大家积极做题~'


@app.websocket('/qqbot')
async def qqbot(request, ws):
    """uin机器人"""

    def sgbk(text):
        url = f'https://wenxin110.top/api/sg_encyclopedia?text={text}&type=json'
        result = requests.get(url)
        try:
            result = json.loads(result.content.decode())
            if result.get('img'):
                data = f"[CQ:image,file=123,url={result.get('img')}]标题：{result.get('title')}\n内容：{result.get('content')}"
            else:
                data = f"标题：{result.get('title')}\n内容：{result.get('content')}"
        except:
            data = result.content.decode()
        return data


    while True:
        data = await ws.recv()
        data = json.loads(data)

        print(json.dumps(data, indent=4, ensure_ascii=False))
        # if 判断是群消息且文本消息不为空private

        if data.get('message_type') == 'group' and data.get('raw_message'):
            raw_message = data['raw_message']
            uin = data['user_id']
            name = data['sender']['nickname']
            gc = data['group_id']
            if '题目' in raw_message:
                if os.path.exists(f'All_Data/Account/{uin}.txt'):
                    if os.path.exists(f'All_Data/Login/{uin}.txt'):
                        config = tm.read_configuration(uin)
                        if len(raw_message) > 2:
                            p = re.match('题目 (\d+)', raw_message).group(1)
                            config['p'] = str(p)
                            tm.update_configuration(config, uin)
                            msg = tm.id_list(uin)
                        else:
                            config['p'] = '1'
                            tm.update_configuration(config, uin)
                            msg = tm.id_list(uin)
                    else:
                        msg = f'{name}，你没发送签到呢？（会登录账号）'
                else:
                    msg = '请添加好友，私聊绑定账号密码！格式为(有空格):绑定 账号 密码'
                ret = send_group_msg(msg, gc)
                await ws.send(json.dumps(ret, ensure_ascii=False))
            elif re.match('提交 (.*)', raw_message):
                id = tm.read_configuration(uin).get('id')
                result = tm.submit(uin, re.match('提交 (.*)', raw_message).group(1))
                if id:
                    if result is True:
                        msg = f'恭喜你！{name}，ID:{id}答案正确，积分加1！\n请发送：题目，获取下一题！'
                        integral(uin)
                    elif result is False:
                        msg = f'很抱歉，{name}，ID:{id}答案错误！'
                    else:
                        msg = result
                    ret = send_group_msg(msg, gc)
                    await ws.send(json.dumps(ret))
                else:
                    msg = '还没有选择题目呢？着什么急，发送：题目'
                    ret = send_group_msg(msg, gc)
                    await ws.send(json.dumps(ret))
            elif raw_message == '排行榜':
                msg = integral_list()
                ret = send_group_msg(msg, gc)
                await ws.send(json.dumps(ret))
            elif raw_message == '签到':
                if os.path.exists(f'All_Data/Account/{uin}.txt'):
                    tm.login(uin)
                    msg = f'{name}, 签到成功'
                else:
                    msg = f'{name}, 你没绑定账号！'
                ret = send_group_msg(msg, gc)
                await ws.send(json.dumps(ret))
            elif re.match('选择 (.*)', raw_message):
                msg = tm.get_questions(re.match('选择 (.*)', raw_message).group(1), uin)
                ret = send_group_msg(msg, gc)
                await ws.send(json.dumps(ret))

            elif raw_message == '使用手册':
                msg = '私聊bot绑定账号，选择题目格式为:选择 +id 提交flag：提交 +flag'
                ret = send_group_msg(msg, gc)
                await ws.send(json.dumps(ret))
            elif raw_message == '更改':
                msg = '选择题目难度的格式：更改难度 0-3，选择类型的格式为：更改类型 1-12数字对应的分别是杂项 逆向 密码 pwn web nibook sql upload 待解出 DVWA xss CVE'
                ret = send_group_msg(msg, gc)
                await ws.send(json.dumps(ret))
            elif '更改难度' in raw_message:
                diff = re.search(r'([0123])', raw_message).group(1)
                if diff:
                    config = tm.read_configuration(uin)
                    config['diff'] = diff
                    tm.update_configuration(config, uin)
                    msg = '更改成功！'
                    ret = send_group_msg(msg, gc)
                    await ws.send(json.dumps(ret))
                else:
                    msg = '更改失败，格式为：更改难度 0~3'
                    ret = send_group_msg(msg, gc)
                    await ws.send(json.dumps(ret))
            elif '更改类型' in raw_message:
                type = re.search(r'([\d+])', raw_message).group(1)
                if type:
                    config = tm.read_configuration(uin)
                    config['type'] = type
                    tm.update_configuration(config, uin)
                    msg = '更改成功！'
                else:
                    msg = '更改失败，格式为：更改类型 1~11'
                ret = send_group_msg(msg, gc)
                await ws.send(json.dumps(ret))


        elif data.get('message_type') == 'private' and data.get('raw_message'):
            raw_message = data['raw_message']
            uin = data['user_id']
            data = re.match('绑定 (.*) (.*)', raw_message)
            if data:
                tm.save_user(data.group(1), data.group(2), uin)
                msg = '绑定成功！'
                ret = send_private_msg(msg, uin)
                await ws.send(json.dumps(ret))
        elif data.get('request_type'):
            flag = data.get('flag')
            ret = {
                'action': 'set_friend_add_request',
                'params': {
                    'flag': flag
                }
            }
            data = await ws.recv()
            data = json.loads(data)
            print(json.dumps(data, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    file = 'integral.txt'
    if not os.path.exists('All_Data'):
        os.mkdir('All_Data')
    if not os.path.exists('image_data'):
        os.mkdir('image_data')
    if not os.path.exists('All_Data/Account'):
        os.mkdir('All_Data/Account')  # 保存用户账号密码
        if not os.path.exists('All_Data/Login'):
            os.mkdir('All_Data/Login')  # 保存用户登录信息
            if not os.path.exists('All_Data/User'):
                os.mkdir('All_Data/User')  # 保存用户基本配置
                if not os.path.exists(file):
                    with open(file, 'w') as f1:
                        f1.write('{}')
    app.run(debug=True, auto_reload=True)
