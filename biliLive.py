import re
import time
import json
import socket
import struct
import requests
import threading
import brotli
import datetime
from random import randint

# 头部数据固定值
CONST_HEADER = 16
CONST_CONSTANT = 1
# 协议版本
VERSION_UNZIPPED = 0
VERSION_HEARTBEAT = 1
VERSION_ZIPPED = 3
# 数据包类型
TYPE_CLIENT_HEARTBEAT = 2
TYPE_SERVER_HEARTBEAT = 3
TYPE_SERVER_INFO = 5
TYPE_CLIENT_AUTH = 7
TYPE_SERVER_AUTH = 8

FILENAME_TRANSFORM_RULES = {
    "/":"／", "\\":"＼", "|":"｜", "*":"＊", "?":"？",
    ":":"：", "<":"＜", ">":"＞", "\"":"“",
}

setSocket = None

"""获取直播间标题、简介等信息"""
def get_room_info(roomid, timeout=None) -> dict:
        url = "https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom"
        params = {"room_id": roomid}
        if timeout is None: timeout = 5
        res = requests.get(url=url, params=params, timeout=timeout)
        return json.loads(res.text)

def GetLiveInfo(roomid):
    try:
        data = get_room_info(roomid)
        live_title = data["data"]["room_info"]["title"].replace(",", "，")
        liver_name = data["data"]["anchor_info"]["base_info"]["uname"].replace(",", "，")
        liver_name = re.sub(r"(?i)[_\-]*(official|channel)", "", liver_name)
        for k, v in FILENAME_TRANSFORM_RULES.items():
            liver_name = liver_name.replace(k, v)
        return liver_name, live_title
    except Exception as e:
        print(str(e))
        return str(roomid), ""

"""获取直播间ip、端口、token"""
def get_blive_url(roomid, ssl=True, platform="pc", player="web"):
    resp = requests.get(
        f"https://api.live.bilibili.com/room/v1/Danmu/getConf",
        params={"room_id": roomid, "platform": platform, "player": player},
    )
    data = resp.json()
    lens = len(data["data"]["host_server_list"])
    url_obj = data["data"]["host_server_list"][randint(0, lens - 1)]
    host = url_obj['host']
    port = url_obj['port']

    return host, port, data["data"]["token"]

"""解包信息"""
def unpack_packets(message):
    ptr = 0
    total_length = len(message)
    while ptr < total_length:
        header = message[ptr: ptr + CONST_HEADER]
        length, _, version, msg_type, _ = struct.unpack("!IHHII", header)
        data = message[ptr + CONST_HEADER: ptr+length]
        ptr += length
        yield version, msg_type, data

"""连接socket"""
def get_socket_connect(host,port,roomid,token):
    global setSocket
    setSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('connect')
    setSocket.connect((host, port))
    data = {"uid": 0,
            "roomid": roomid,
            "protover": 3,
            "platform": "pc_link",
            "type": 2,
            "key": token
            }
    print('认证')
    socket_send(json.dumps(data, separators=(',', ':')), TYPE_CLIENT_AUTH)
    print('心跳包')
    socket_heartbeat()

"""发送socket"""
def socket_send(message, msg_type):
    global setSocket
    header = [CONST_HEADER + len(message),
              CONST_HEADER,
              VERSION_HEARTBEAT,
              msg_type,
              CONST_CONSTANT
              ]
    message_encoded = struct.pack("!IHHII", *header) + message.encode()
    setSocket.sendall(message_encoded)

"""心跳包"""
def socket_heartbeat():
    global setSocket
    socket_send("", TYPE_CLIENT_HEARTBEAT)
    heartbeat = threading.Timer(30, socket_heartbeat)
    heartbeat.daemon = True
    heartbeat.start()

"""监听接收"""
def socket_recv():
    global setSocket
    header = setSocket.recv(CONST_HEADER, socket.MSG_WAITALL)
    length, _, version, msg_type, _ = struct.unpack("!IHHII", header)
    message = setSocket.recv(length-CONST_HEADER, socket.MSG_WAITALL)

    if version == VERSION_ZIPPED:
        for data in unpack_packets(brotli.decompress(message)):
            yield data
    else:
        yield version, msg_type, message

"""解析数据包"""
def handle(version, msg_type, data):
    if msg_type == TYPE_SERVER_INFO:
        data = json.loads(data)
        cmd = data.get("cmd")

        if cmd == "DANMU_MSG":
            info = data.get("info")
            ts = info[9]["ts"]
            uid, nickname = info[2][:2]
            text = info[1]
            date, time = datetime.datetime.fromtimestamp(ts).isoformat(' ').split()
            print(date,time)

            if info[3]:
                medal_level, medal = info[3][:2]
                return {"code": 2,
                        "data": {"medal": f"{medal}{medal_level}",
                                 "nickname": nickname,
                                 "text": text}
                        }
            else:
                return {"code": 2,
                        "data": {"nickname": nickname,
                                 "text": text}
                        }
        elif cmd == "SEND_GIFT":
            return {"code": 3,
                    "data": {"nickname": data['data']['uname'],
                             "giftname": data['data']['giftName'],
                             "num": data['data']['num'],
                             'price': data['data']['price']
                             }}
        elif cmd == "INTERACT_WORD":
            return {"code": 4, "data":
                {"info": f"{data['data']['uname']}进入了直播间"}
                    }
        elif cmd == "WATCHED_CHANGE":
            return {"code": 5,
                    "data": {"num": data["data"]["num"],
                             "text": data["data"]["text_large"]
                             }}
        elif cmd == "ONLINE_RANK_COUNT":
            return {"code": 6,
                    "data": {"num": data["data"]["count"]
                             }}
        elif cmd == "ONLINE_RANK_V2":
            return {"code": 7, "data": data}
        elif cmd.startswith("ONLINE_RANK_TOP"):
            return {"code": 8, "data": data}
        elif cmd == "STOP_LIVE_ROOM_LIST":
            return {"code": 9}
        elif cmd == "NOTICE_MSG":
            return {"code": 9}
        else:
            return {"code": 10, "data": data}

    elif msg_type == TYPE_SERVER_HEARTBEAT:
        return {"code": 1,
                "data": {"text": f"{int.from_bytes(data, 'big')}人气"}
                }
    elif msg_type == TYPE_SERVER_AUTH:
        return {"code": 0,
                "data": {"info": "服务器认证通过"}
                }


if __name__ == '__main__':
    a,b = GetLiveInfo(12272289)
    print(a,' ----- ',b)

    host, port, token = get_blive_url(12272289)
    print(host, port, token)

    get_socket_connect(host,port,12272289,token)
    try:
        while 1:
            for data in socket_recv():
                data = handle(*data)
                print(data)
    except:
        print('close')
        setSocket.close()

