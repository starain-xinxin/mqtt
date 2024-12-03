import paho.mqtt.client as mqtt
import json
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, messagebox
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

bgc = "#ffffff"  # 
activebackground= "#f7f2d3"
bt_style = "groove"
btc = "#f4fbb1"
# 创建 GUI 界面
class MqttGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT 用户控制界面")
        # root.overrideredirect(True)
        self.root.geometry("1200x800")
        self.root.configure(bg=bgc)  # 浅米黄色背景
        root.attributes("-alpha", 0.80)  # 设置窗口透明度，值范围 0.0~1.0

        # 日志显示区
        self.log_frame = tk.Frame(self.root, bg=bgc)
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 用户日志区（显示 [log] 标记的信息）
        tk.Label(self.log_frame, text="用户日志", bg=bgc, font=("Comic Sans MS", 15, "bold")).pack()
        self.user_log_text = scrolledtext.ScrolledText(
            self.log_frame, state=tk.DISABLED, wrap=tk.WORD, height=10, bg="#1c1c1c", fg="#90ee90", font=("Cascadia Mono", 15)
        )
        self.user_log_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # MQTT 调试信息日志区
        tk.Label(self.log_frame, text="调试日志", bg=bgc, font=("Comic Sans MS", 15, "bold")).pack()
        self.debug_log_text = scrolledtext.ScrolledText(
            self.log_frame, state=tk.DISABLED, wrap=tk.WORD, height=10, bg="#1c1c1c", fg="#a9a9a9", font=("Cascadia Mono", 15)
        )
        self.debug_log_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # 控制按钮区
        self.control_frame = tk.Frame(self.root, bg=bgc)
        self.control_frame.pack(pady=10)

        self.init_button = tk.Button(
            self.control_frame,
            text="发送初始化任务",
            command=self.init_tasks,
            bg=btc, fg="black", font=("Comic Sans MS", 12, "bold"), relief=bt_style
        )
        self.init_button.grid(row=0, column=0, padx=10, pady=5)

        self.task_button = tk.Button(
            self.control_frame,
            text="发送任务指令",
            command=partial(self.send_task, is_button=True),
            bg=btc, fg="black", font=("Comic Sans MS", 12, "bold"), relief=bt_style,
        )
        self.task_button.grid(row=0, column=1, padx=10, pady=5)

        self.stop_button = tk.Button(
            self.control_frame,
            text="发送停止指令",
            command=self.send_stop,
            bg=btc, fg="black", font=("Comic Sans MS", 12, "bold"), relief=bt_style
        )
        self.stop_button.grid(row=0, column=2, padx=10, pady=5)

        tk.Label(self.control_frame, text="路径 ID:", bg=bgc, font=("Comic Sans MS", 12)).grid(row=1, column=0)
        self.path_id_entry = tk.Entry(self.control_frame, font=("Comic Sans MS", 12))
        self.path_id_entry.grid(row=1, column=1, padx=10)

        # 调试日志切换按钮
        self.toggle_debug = tk.Button(
            self.control_frame,
            text="隐藏调试日志",
            command=self.toggle_debug_logs,
            bg=btc, font=("Comic Sans MS", 12, "bold"), relief=bt_style, activebackground=activebackground
        )
        self.toggle_debug.grid(row=2, column=1, pady=10)

        # 添加退出按钮
        tk.Button(
            self.control_frame,
            text="退出程序",
            command=self.exit_program,
            bg=bgc, fg="black", font=("Comic Sans MS", 12, "bold"), relief=bt_style
        ).grid(row=3, column=1, pady=10)

    def log_message(self, msg, level="info"):
        """在日志区域显示消息"""
        if "[log]" in msg:  # 用户日志
            target_text_widget = self.user_log_text
        else:  # 调试日志
            target_text_widget = self.debug_log_text

        if level == "error":
            color = "#ffa07a"  # 浅橙色
        else:
            if "[log]" in msg: 
                color = "#a5f4d3"  # 浅绿色
            else:
                color = "#7ddced" # 浅蓝

        target_text_widget.config(state=tk.NORMAL)
        target_text_widget.insert(tk.END, f"[{datetime.now()}] {msg}\n", ("colored",))
        target_text_widget.tag_config("colored", foreground=color, font=("Cascadia Mono", 13, "normal"))
        target_text_widget.see(tk.END)  # 滚动到底部
        target_text_widget.config(state=tk.DISABLED)

    def toggle_debug_logs(self):
        """切换调试日志的显示/隐藏"""
        if self.debug_log_text.winfo_viewable():
            self.debug_log_text.pack_forget()
            self.toggle_debug.config(text="显示调试日志")
        else:
            self.debug_log_text.pack(fill=tk.BOTH, expand=True, pady=5)
            self.toggle_debug.config(text="隐藏调试日志")

    def send_message(self, topic, payload):
        """发送 MQTT 消息"""
        try:
            json_payload = json.dumps(payload)
            mqttc.publish(topic, json_payload)
            self.log_message(f"[Sent][topic:{topic}]: {json_payload}")
        except Exception as e:
            self.log_message(f"Failed to send message: {e}", level="error")

    def init_tasks(self):
        """发送初始化任务"""
        message_payload = {"command-type": "init"}
        self.send_message("data", message_payload)

    def send_task(self, is_button, car_path_id=1):
        """发送任务指令"""
        try:
            if is_button:  # 从用户界面获取路径ID
                path_id = int(self.path_id_entry.get())
            else:
                path_id = car_path_id
            if 1 <= path_id < len(car_path):
                message_payload = {
                    "command-type": "task",
                    "tasks": car_path[path_id],
                    "path-id": path_id,
                }
                self.send_message("data", message_payload)
            else:
                self.log_message("无效的路径 ID，请输入有效的数字！", level="error")
        except ValueError:
            self.log_message("路径 ID 必须是一个数字！", level="error")

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
    client.subscribe("server")

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
        else:
            gui.log_message(f"[Unknown command type]: {message['command-type']}")
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
