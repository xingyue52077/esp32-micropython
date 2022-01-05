from machine import Pin, Timer
led = Pin(2, Pin.OUT)
Counter = 0
Fun_Num = 0


def fun(tim):
    global Counter
    Counter = Counter + 1
    print(Counter)
    led.value(Counter % 2)


# 开启 RTOS 定时器，编号为-1
tim = Timer(-1)
tim.init(period=1000, mode=Timer.PERIODIC, callback=fun)  # 周期为 1000ms
