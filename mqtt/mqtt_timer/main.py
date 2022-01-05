'''
定时器做的异步mqtt通讯，效果一般 不建议使用

'''
from umqtt.simple import MQTTClient
import time
from machine import Pin, Timer
import json
import _thread
import wlan


N = 1
flag = 0


def led_f(tim):  
    global flag
    print(flag)
    led.value(flag)
    if flag==0:
        flag =1
    else:
        flag=0


def sub_cb(topic, msg):
    print((topic, msg))
    global N
    N = json.loads(msg).get('time', N)
    tim.init(period=N*1000, mode=Timer.PERIODIC, callback=led_f)


def pub(tim):
    c.publish("topic_out", f"Hello RT-Thread !!!{N}")
    print(1)


# def sub(tim):
#     c.wait_msg()
def sub(c):
    while True:
            if True:
                # Blocking wait for message
                c.wait_msg()
            else:   
                pass



def main():

    # tim2 = Timer(2)
    tim.init(period=N*1000, mode=Timer.PERIODIC, callback=led_f)
    tim1.init(period=1000, mode=Timer.PERIODIC, callback=pub)
    # tim2.init(period=1000, mode=Timer.PERIODIC, callback=sub) # 定时器做不到异步，仍然会阻塞


if __name__ == '__main__':
    c = MQTTClient("aaa", 'xingyue.art', user='xingyue', password='fanhaolun')
    c.set_callback(sub_cb)
    c.connect()
    c.subscribe("topic_in")
    led=Pin(2,Pin.OUT)
    _thread.start_new_thread(sub, (c,))
    tim = Timer(0)
    tim1 = Timer(1)
    main()

