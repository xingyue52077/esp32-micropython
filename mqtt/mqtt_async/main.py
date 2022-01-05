import ujson
import wlan
import time
from machine import Pin
import uasyncio as asyncio
from async_mqtt import MQTTClient



class MyIotPrj:
    def __init__(self):
        client_id = "slim_id"
        self.mserver   = 'xingyue.art'
        port           = 1883
        self.client = MQTTClient(client_id, self.mserver, user='xingyue', password='fanhaolun')
        self.isconn = False

        self.topic_in = b'topic_in'
        self.topic_out = b'topic_out'
        self.n=1

    async def sub_callback(self, topic, msg):       
        self.n=ujson.loads(msg).get("time",self.n)
        print((topic, msg))

    async def mqtt_main_thread(self):

        try:
            self.client.set_callback(self.sub_callback)

            conn_ret_code = await self.client.connect()
            if conn_ret_code != 0:
                return
                            
            print('conn_ret_code = {0}'.format(conn_ret_code))
            
            await self.client.subscribe(self.topic_in)
            print("Connected to %s, subscribed to %s topic" % (self.mserver, self.topic_in))
            
            self.isconn = True

            while True:
                await self.client.wait_msg()
                print('wait_msg')
        finally:
            if self.client is not None:
                print('off line')
                await self.client.disconnect()
                self.isconn = False

    async def mqtt_upload_thread(self):

        
        while True:
            dht_data = {
            'time':self.n
            }
            my_dht = Pin(2, Pin.OUT)
            my_dht.value(1)
            # time.sleep(self.n)
            await asyncio.sleep(self.n)
            my_dht.value(0)
            # time.sleep(self.n)
            await asyncio.sleep(self.n)
            await self.client.publish(self.topic_out, ujson.dumps(dht_data), retain=True)
#             if self.isconn == True:
# #                my_dht.measure()
# #                dht_data['temperature'] = my_dht.temperature()
# #                dht_data['humidity']    = my_dht.humidity()
#                 print(dht_data)
#                 await self.client.publish(self.topic_out, ujson.dumps(dht_data), retain=True)
            
            # await asyncio.sleep(1)

        while True:
            if self.isconn == True:
                await self.client.ping()
            await asyncio.sleep(5)
            
def main():
    mip = MyIotPrj()
    
    loop = asyncio.get_event_loop()
    loop.create_task(mip.mqtt_main_thread())
    loop.create_task(mip.mqtt_upload_thread())
    loop.run_forever()
    # asyncio.run(asyncio.gather(mip.mqtt_main_thread(),mip.mqtt_upload_thread()))
 
if __name__ == '__main__':
    main()