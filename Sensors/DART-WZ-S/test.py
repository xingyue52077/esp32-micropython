from WZ_S import WZ_S,PassiveWZ_S
import machine
import utime


mic = WZ_S(uart=2)
while 1:
    mic_data = mic.read()
    print(mic_data)

    


