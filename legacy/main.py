# 初始化函数
from machine import Pin, SoftI2C, ADC, PWM
import time
from ST_VL6180 import Sensor
import time
from legacy.umqttsimple import MQTTClient
import ubinascii
import machine
import micropython
import network
import esp

esp.osdebug(None)
import gc

gc.collect()

# 定义I2C通信接口和TOF测距传感器的初始化变量
i2c = SoftI2C(scl=Pin(22), sda=Pin(23), freq=100000)
sensor = Sensor(i2c)

# 定义小车控制相关的初始化变量
left1 = Pin(32, Pin.IN)
left2 = Pin(34, Pin.IN)
middle = Pin(35, Pin.IN)
right1 = Pin(13, Pin.IN)
right2 = Pin(12, Pin.IN)

BAIN1 = Pin(33, Pin.OUT)
BBIN1 = Pin(27, Pin.OUT)
BAIN2 = PWM(Pin(25))
BBIN2 = PWM(Pin(26))

FAIN1 = Pin(16, Pin.OUT)
FBIN1 = Pin(17, Pin.OUT)
FAIN2 = PWM(Pin(4))
FBIN2 = PWM(Pin(18))

LED = Pin(2, Pin.OUT)

start = time.ticks_ms()

# MQTT网络通信
ssid = 'IoT-Lab_WiFi6_2.4G'
password = 'CD449C0E36'
mqtt_server = '192.168.112.127'
client_id = ubinascii.hexlify(machine.unique_id())
# print(client_id)
topic_sub = b'center'
topic_pub = b'car'
last_message = 0
message_interval = 5
counter = 0
m = []
m = ['straight', 'straight', 'left', 'left', 'left', 'straight', 'straight', 'left', 'right', 'left', 'right',
     'tiny_right', 'tiny_left', 'tiny_left', 'tiny_right', 'left', 'left', 'straight', 'straight', 'straight', 'left',
     'straight', 'straight', 'end']
# m = ['left', 'right', 'left', 'right', 'tiny_right', 'tiny_left', 'tiny_left', 'tiny_right','right','end']

cross_counter = 0
# cross_num = 0
cross_num = len(m)
roundabout = 0


def WIFI_connect():
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(ssid, password)
    while station.isconnected() == False:
        pass
    print('Connection successful')
    print(station.ifconfig())


def sub_cb(topic, msg):
    print(msg)
    if msg != b'0':
        message = bytes.decode(msg)
        global m
        m = message.split(',')


def connect_and_subscribe():
    global client_id, mqtt_server, topic_sub
    client = MQTTClient(client_id, mqtt_server)
    client.set_callback(sub_cb)
    client.connect()
    client.subscribe(topic_sub)
    print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub))
    return client


def restart_and_reconnect():
    print('Failed to connect to MQTT broker. Reconnecting...')
    time.sleep(10)
    machine.reset()


def MQTT_start():
    try:
        client = connect_and_subscribe()
    except OSError as e:
        restart_and_reconnect()
    return client


# 控制相关函数
def go_straight(l, r):
    if l == 1:
        BAIN2.duty(250)
        BBIN2.duty(650)
        FAIN2.duty(650)
        FBIN2.duty(250)
    elif r == 1:
        BAIN2.duty(650)
        BBIN2.duty(250)
        FAIN2.duty(250)
        FBIN2.duty(650)
    else:
        BAIN2.duty(430)
        BBIN2.duty(400)
        FAIN2.duty(400)
        FBIN2.duty(430)


def cross():
    BAIN2.duty(0)
    BBIN2.duty(0)
    FAIN2.duty(0)
    FBIN2.duty(0)
    time.sleep(1)


def turn_left():
    BAIN2.duty(0)
    BBIN2.duty(1000)
    FAIN2.duty(1000)
    FBIN2.duty(0)
    time.sleep(0.65)


def turn_right():
    BAIN2.duty(1000)
    BBIN2.duty(300)
    FAIN2.duty(200)
    FBIN2.duty(1000)
    time.sleep(0.8)


def tiny_right():
    BAIN2.duty(1000)
    BBIN2.duty(300)
    FAIN2.duty(200)
    FBIN2.duty(1000)
    time.sleep(0.4)


def tiny_left():
    BAIN2.duty(400)
    BBIN2.duty(900)
    FAIN2.duty(900)
    FBIN2.duty(400)
    time.sleep(0.3)


def obstacle():
    BAIN2.duty(0)
    BBIN2.duty(0)
    FAIN2.duty(0)
    FBIN2.duty(0)
    LED.on()


# # 连接网络与MQTT客户端
# WIFI_connect()
client = MQTT_start()
# try:
#     client.check_msg()
# except OSError as e:
#     restart_and_reconnect()
#
# while(1):
#     BAIN2.duty(0)
#     BBIN2.duty(0)
#     FAIN2.duty(0)
#     FBIN2.duty(0)
#     try:
        # client.check_msg()
#     except OSError as e:
#         restart_and_reconnect()
#     if m:
#         print(m)
#         cross_num = len(m);
#         for i in range(5):
#             LED.on()
#             time.sleep(0.5)
#             LED.off()
#             time.sleep(0.5)
#         break

while (1):

    distance = sensor.range()

    l1 = left1.value()
    l2 = left2.value()
    mi = middle.value()
    r1 = right1.value()
    r2 = right2.value()
    #     print('l1 = ', l1, 'l2 = ', l2, 'middle = ', mi, 'r1 = ', r1, 'r2 = ', r2)
    if distance > 70:
        LED.off()
        delta = time.ticks_diff(time.ticks_ms(), start)
        if delta > 800 - roundabout:
            if l1 or r1:
                cross()
                if cross_counter < cross_num:
                    #                 print(m[cross_counter])
                    if m[cross_counter] == 'left':
                        turn_left()
                        roundabout = 0
                        start = time.ticks_ms()
                    elif m[cross_counter] == 'right':
                        turn_right()
                        roundabout = 0
                        start = time.ticks_ms()
                    elif m[cross_counter] == 'straight':
                        go_straight(l2, r2)
                        roundabout = 300
                        start = time.ticks_ms()
                    elif m[cross_counter] == 'tiny_right':
                        tiny_right()
                        roundabout = 0
                        start = time.ticks_ms()
                    elif m[cross_counter] == 'tiny_left':
                        tiny_left()
                        roundabout = 800
                        start = time.ticks_ms()
                    elif m[cross_counter] == 'end':
                        break
                    cross_counter += 1
                else:
                    break

            else:
                go_straight(l2, r2)
        #         if not flag_turn:
        #             flag_turn = 1
        #             time.sleep(0.5)
        else:
            go_straight(l1 | l2, r1 | r2)
    else:
        obstacle()
    time.sleep(0.05)

