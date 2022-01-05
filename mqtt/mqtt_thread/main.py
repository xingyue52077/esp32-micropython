from umqtt.simple import MQTTClient
import time
from machine import Pin
import _thread
import json
import wlan

N=1

def led():
    while True:
        print(N)
        led=Pin(2,Pin.OUT)
        led.value(1)
        time.sleep(N)
        led.value(0)
        time.sleep(N)
    

def sub_cb(topic, msg):
    print((topic, msg))
    global N
    N=json.loads(msg).get('time',N)

def pub(c):
    while True:
        c.publish("topic_out", f"Hello RT-Thread !!!{N}")
        time.sleep(1)
        # led(N)


def sub(c):
    while True:
            if True:
                # Blocking wait for message
                c.wait_msg()
            else:   
                pass


if __name__ == '__main__':
    c = MQTTClient("aaa", 'xingyue.art',user='xingyue',password='fanhaolun')
    c.set_callback(sub_cb)
    c.connect()
    c.subscribe("topic_in")
    _thread.start_new_thread(pub, (c,))
    _thread.start_new_thread(sub, (c,))
    _thread.start_new_thread(led, ())    