import network
wlan = network.WLAN(network.STA_IF) # 创建 station 接口
wlan.active(True)       # 激活接口
wlan.disconnect()
wlan.connect('xx', 'xxx') # 连接到指定ESSID网络
while not wlan.isconnected(): # 检查创建的station是否连已经接到AP
    pass   
print(wlan.config('mac'))      # 获取接口的MAC地址
print(wlan.ifconfig())         # 获取接口的 IP/netmask(子网掩码)/gw(网关)/DNS 地址
