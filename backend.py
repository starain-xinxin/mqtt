import socket
import json
from datetime import datetime
import time
import threading

# 定义 Socket 服务器参数
HOST = "127.0.0.1"  # 本地 IP
PORT = 12345     # 端口号

# 小车路径指令
car_path = [
    ["end"],
    ['right', 'straight', 'right', 'right', 'right', 'end'],
    ['straight', 'left', 'end'],
]

def send_log(client_socket, log_type, message):
    """
    发送日志到前端，通过 Socket 通信。
    根据 log_type 来决定日志格式。
    直接发送格式化的字符串，不封装成 JSON。
    """
    try:
        # 根据 log_type 修改日志消息格式
        if log_type == "log":
            formatted_message = "[log] " + message

        elif log_type == "debug":
            formatted_message = "[debug] " + message

        else:
            formatted_message = "[unknown] " + message  # 其他类型日志使用默认格式
        
        # 直接发送格式化的字符串
        client_socket.sendall(formatted_message.encode() + b'\n')

    except Exception as e:
        print(f"发送日志失败: {e}")


# MQTT 回调函数
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Connected with result code {reason_code}")
    # 订阅主题
    client.subscribe("server")


def on_message(client, userdata, msg):
    try:
        # 解析收到的消息为 JSON 格式
        message = json.loads(msg.payload.decode())

        # 1. 接收到初始化回复指令，发送任务指令
        if message['command-type'] == 'ack_init':
            print(f"[Received][{datetime.now()}][topic {msg.topic}][type:{message['command-type']}]: {message}")
            send_log(client_socket, "debug", f"[Received][{datetime.now()}][topic {msg.topic}][type:{message['command-type']}]: {message}")
            car_path_id = message.get('path-id', 1)
            send_task(car_path_id)
            print(f"小车选择路径 {car_path[car_path_id]}")
            send_log(client_socket, "log", f"小车选择路径 {car_path_id}")

        # 2. 接收到任务回复指令，打印回复
        elif message['command-type'] == 'ack_task':
            print(f"[Received][{datetime.now()}][topic {msg.topic}][type:{message['command-type']}]: {message}")
            print(f"小车正在路径{message['path-id']}上行进...")
            send_log(client_socket, "debug", f"[Received][{datetime.now()}][topic {msg.topic}][type:{message['command-type']}]: {message}")
            send_log(client_socket, "log", f"小车正在路径{message['path-id']}上行进...")

        # 3. 接收到停止回复指令，打印回复
        elif message['command-type'] == 'ack_stop':
            print(f"[Received][time:{datetime.now()}][topic {msg.topic}][type:{message['command-type']}]: {message}")
            print(f"小车停止行进")
            send_log(client_socket, "debug", f"[Received][time:{datetime.now()}][topic {msg.topic}][type:{message['command-type']}]: {message}")
            send_log(client_socket, "log", f"小车停止行进")
        else:
            print(f"[Received][time:{datetime.now()}][topic {msg.topic}][type:{message['command-type']}]: {message}")
            send_log(client_socket, "unkonwn", f"{message}")
    except json.JSONDecodeError:
        send_log(client_socket, "unknown", f"[解析消息失败]: {msg.payload.decode()}")

# MQTT 消息发送函数
def send_message(client, topic, payload):
    """
    发送 JSON 格式的 MQTT 消息。
    """
    try:
        json_payload = json.dumps(payload)
        client.publish(topic, json_payload)
        send_log(client_socket, "debug", f"发送消息至 {topic}: {json_payload}")
    except Exception as e:
        send_log(client_socket, "debug", f"发送消息失败: {e}")

# 初始化任务
def init_tasks():
    message_payload = {"command-type": "init"}
    send_message(mqttc, "data", message_payload)

# 发送任务指令
def send_task(path_id=1):
    message_payload = {
        "command-type": "task",
        "tasks": car_path[path_id],
        "path-id": path_id,
    }
    send_message(mqttc, "data", message_payload)

# 发送停止指令
def send_stop():
    message_payload = {
        "command-type": "stop",
        "tasks": ['end'],
    }
    send_message(mqttc, "data", message_payload)

# 处理前端指令
def process_command(command):
    """
    处理来自前端的指令。
    """
    if command.startswith("task:"):
        print(f'[前端][task]{command}')
        if command.split(":")[1] == "":
            path_id = 1
        else:
            path_id = int(command.split(":")[1])
        send_task(path_id)
        send_log(client_socket, "debug", f"处理任务指令，路径 ID: {path_id}")

    elif command == "init":
        print(f'[前端][init]{command}')
        init_tasks()
        send_log(client_socket, "debug", "处理初始化指令")

    elif command == "stop":
        print(f'[前端][stop]{command}')
        send_stop()
        send_log(client_socket, "debug", "处理停止指令")

    else:
        print(f'[前端][unknown]{command}')
        send_log(client_socket, "debug", f"未知指令: {command}")

# 初始化 MQTT 客户端
import paho.mqtt.client as mqtt
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
broker_ip = "10.223.47.2"
mqttc.connect(broker_ip, 1883, 60)
mqttc.loop_start()

# 启动 Socket 服务器
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"Socket 服务器已启动，监听地址: {HOST}:{PORT}")
    client_socket, client_address = server_socket.accept()
    print(f"前端已连接: {client_address}")

    # 主循环，处理指令和日志更新
    try:
        while True:
            data = client_socket.recv(1024).decode().strip()
            if data:
                print(f"收到前端指令: {data}")
                process_command(data)
    except KeyboardInterrupt:
        mqttc.loop_stop()
        print("服务器已停止")
        client_socket.close()
    finally:
        client_socket.close()
