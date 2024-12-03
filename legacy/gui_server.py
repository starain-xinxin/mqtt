import paho.mqtt.client as mqtt
import json
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext
from threading import Thread
from functools import partial

# 小车路径指令全局变量，每个列表代表一个指令
car_path = [
    ["end"],
    ['straight', 'left', 'right', 'left', 'straight', 'right'],
    ['straight', 'left', 'end'],
]

broker_ip = "192.168.3.28"

# MQTT 客户端初始化
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# 创建 GUI 界面
class MqttGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT 用户控制界面")
        self.root.geometry("1200x800")

        # 日志显示区
        self.log_frame = tk.Frame(self.root)
        self.log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(self.log_frame, state=tk.DISABLED, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 控制按钮区
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(pady=10)

        tk.Button(self.control_frame, text="发送初始化任务", command=self.init_tasks).grid(row=0, column=0, padx=10, pady=5)
        tk.Button(self.control_frame, text="发送任务指令", command=partial(self.send_task, is_button=True)).grid(row=0, column=1, padx=10, pady=5)
        tk.Button(self.control_frame, text="发送停止指令", command=self.send_stop).grid(row=0, column=2, padx=10, pady=5)

        tk.Label(self.control_frame, text="路径 ID:").grid(row=1, column=0)
        self.path_id_entry = tk.Entry(self.control_frame)
        self.path_id_entry.grid(row=1, column=1)

        # 添加退出按钮
        tk.Button(self.control_frame, text="退出程序", command=self.exit_program).grid(row=2, column=1, pady=10)

    def log_message(self, msg):
        """在日志区域显示消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{datetime.now()}] {msg}\n")
        self.log_text.see(tk.END)  # 滚动到底部
        self.log_text.config(state=tk.DISABLED)

    def send_message(self, topic, payload):
        """发送 MQTT 消息"""
        try:
            json_payload = json.dumps(payload)
            mqttc.publish(topic, json_payload)
            self.log_message(f"[Sent][topic:{topic}]: {json_payload}")
        except Exception as e:
            self.log_message(f"Failed to send message: {e}")

    def init_tasks(self):
        """发送初始化任务"""
        message_payload = {"command-type": "init"}
        self.send_message("data", message_payload)

    def send_task(self, is_button, car_path_id=1 ):
        """发送任务指令"""
        try:
            if is_button:        # 从用户界面获取路径ID
                path_id = int(self.path_id_entry.get())      
            else:
                path_id =  car_path_id    
            if 1 <= path_id < len(car_path):
                message_payload = {
                    "command-type": "task",
                    "tasks": car_path[path_id],
                    "path-id": path_id,
                }
                self.send_message("data", message_payload)
            else:
                self.log_message("无效的路径 ID，请输入有效的数字！")
        except ValueError:
            self.log_message("路径 ID 必须是一个数字！")


    def send_stop(self):
        """发送停止指令"""
        message_payload = {
            "command-type": "stop",
            "tasks": ["end"],
        }
        self.send_message("data", message_payload)

    def exit_program(self):
        """退出程序"""
        self.log_message("程序即将退出...")
        mqttc.loop_stop()  # 停止 MQTT 循环
        self.root.quit()  # 退出 tkinter 界面

# MQTT 回调函数
def on_connect(client, userdata, flags, reason_code, properties):
    gui.log_message(f"Connected with result code {reason_code}")
    client.subscribe("data")

def on_message(client, userdata, msg):
    try:
        message = json.loads(msg.payload.decode())
        gui.log_message(f"[Received][topic {msg.topic}]: {message}")

        if message['command-type'] == 'ack_init':
            car_path_id = message.get('path-id', 1)
            gui.log_message(f"[log] 小车选择路径 {car_path_id}")
            gui.send_task(is_button=False, car_path_id=car_path_id)
        elif message['command-type'] == 'ack_task':
            gui.log_message(f"[log] 小车正在路径{message['path-id']}上行进...")
        elif message['command-type'] == 'ack_stop':
            gui.log_message("[log] 小车已停止任务")
    except json.JSONDecodeError:
        gui.log_message(f"Failed to decode message: {msg.payload.decode()}")

# 运行 MQTT 客户端
def start_mqtt_client():
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.connect(broker_ip, 1883, 60)
    mqttc.loop_forever()

# 启动 GUI 界面和 MQTT 客户端
if __name__ == "__main__":
    root = tk.Tk()
    gui = MqttGUI(root)

    # 启动 MQTT 客户端线程
    mqtt_thread = Thread(target=start_mqtt_client, daemon=True)
    mqtt_thread.start()

    # 启动 GUI 事件循环
    root.mainloop()
