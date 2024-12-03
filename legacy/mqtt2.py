import paho.mqtt.client as mqtt
import json
from datetime import datetime
import time
import tkinter as tk
from tkinter import scrolledtext

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    # 订阅主题
    client.subscribe("data")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    try:
        # 解析收到的消息为 JSON 格式
        message = json.loads(msg.payload.decode())

        # 1. 接收到初始化回复指令，发送任务指令
        if message['command-type'] == 'ack_init':
            print(f"[Received][time:{datetime.now()}][topic {msg.topic}][type:{message['command-type']}]: {message}")
            car_path = message['path-id']
            send_task(car_path)
            print(f"[log] 小车选择路径 {car_path}")

        # 2. 接收到任务回复指令，打印回复
        if message['command-type'] == 'ack_task':
            print(f"[Received][time:{datetime.now()}][topic {msg.topic}][type:{message['command-type']}]: {message}")
            print(f"[log] 小车正在路径{message['path-id']}上行进...")
        # 3. 接收到停止回复指令，打印回复
        if message['command-type'] == 'ack_stop':
            print(f"[Received][time:{datetime.now()}][topic {msg.topic}][type:{message['command-type']}]: {message}")

    except json.JSONDecodeError:
        print(f"Failed to decode message: {msg.payload.decode()}")

# 发送消息
def send_message(client, topic, payload):
    """
    发送 JSON 格式的消息
    :param client: MQTT 客户端实例
    :param topic: 发布的主题
    :param payload: 消息内容（字典，将自动转换为 JSON）
    """
    try:
        # 将 payload 转换为 JSON 格式
        json_payload = json.dumps(payload)
        client.publish(topic, json_payload)
        print(f"[Sent][time:{datetime.now()}][topic:{topic}]: {json_payload}")
    except Exception as e:
        print(f"Failed to send message: {e}")


def init_tasks():
    message_payload = {
        "command-type": "init",
    }
    send_message(mqttc, "data", message_payload)

def send_task(path_id = 1):
    global car_path
    message_payload = {
        "command-type": "task",
        "tasks": ['straight', 'left', 'right', 'left', 'straight', 'right'],
        "path-id": path_id,
    }
    message_payload["tasks"] = car_path[path_id]
    send_message(mqttc, "data", message_payload)

def send_stop():
    message_payload = {
        "command-type": "stop",
        "tasks": ['end'],
    }
    send_message(mqttc, "data", message_payload)


# 小车路径指令全局变量,每个列表代表一个指令
car_path = [
    ["end"],
    ['straight', 'left', 'right', 'left', 'straight', 'right'],
    ['straight', 'left', 'end'],
]

# 创建 MQTT 客户端
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
broker_ip = "192.168.3.28"


# 连接到 MQTT Broker
mqttc.connect(broker_ip, 1883, 60)
# 启动 MQTT 事件循环（非阻塞）
mqttc.loop_start()

# 标志位用于控制线程结束
stop_thread = False

# 开启一个线程，用于用户发送指令
import threading
# 用户输入线程函数
def user_input_thread():
    """
    处理用户输入，通过输入指令控制小车行为。
    """
    global mqttc, stop_thread
    while True:
        print("\n请输入指令：")
        print("1 - 发送初始化任务")
        print("2 - 发送任务指令")
        print("3 - 发送停止指令")
        print("4 - 退出程序")
        try:
            choice = int(input("选择操作编号: "))
            if choice == 1:
                init_tasks()
            elif choice == 2:
                path_id = int(input("请输入路径 ID（1 到 {}）: ".format(len(car_path) - 1)))
                if 1 <= path_id < len(car_path):
                    send_task(path_id)
                else:
                    print("无效的路径 ID")
            elif choice == 3:
                send_stop()
            elif choice == 4:
                print("退出程序")
                mqttc.loop_stop()  # 停止 MQTT 事件循环
                stop_thread = True  # 通知线程结束
                break
            else:
                print("无效的操作编号，请重试。")
        except ValueError:
            print("输入无效，请输入数字编号。")
        except Exception as e:
            print(f"发生错误: {e}")
        time.sleep(5)

# 创建并启动用户输入线程
input_thread = threading.Thread(target=user_input_thread, daemon=True)
input_thread.start()
# 等待用户线程结束
input_thread.join()

# 发送初始化指令
# init_tasks()


# # 开启事件循环，监听消息
# mqttc.loop_forever()