import machine  # 导入引脚控制
import struct  # 导入格式化字符串模块 https://blog.csdn.net/qq_30638831/article/details/80421019
import time


class UartError(Exception):  # 定义一个异常类 继承得是Exception类
    pass


class Pms7003:
    '''
    pms7003 response协议帧32字节，1，2字节为固定字节0x42，0x4d，3，4字节为帧长度位，表示后面2*13个字节得数据位和最后得2个校验和位，
    5-28字节每两个字节为一套数据，代表一种检测结果，具体查看手册 https://www.snlion.com/nd.jsp?id=33，
    29字节为版本号，30字节为错误代码，31，32字节校验和，为前30个字节相加之和。根据协议帧定义如下索引。
    '''

    START_BYTE_1 = 0x42
    START_BYTE_2 = 0x4d

    PMS_FRAME_LENGTH = 0
    PMS_PM1_0 = 1
    PMS_PM2_5 = 2
    PMS_PM10_0 = 3
    PMS_PM1_0_ATM = 4
    PMS_PM2_5_ATM = 5
    PMS_PM10_0_ATM = 6
    PMS_PCNT_0_3 = 7
    PMS_PCNT_0_5 = 8
    PMS_PCNT_1_0 = 9
    PMS_PCNT_2_5 = 10
    PMS_PCNT_5_0 = 11
    PMS_PCNT_10_0 = 12
    PMS_VERSION = 13
    PMS_ERROR = 14
    PMS_CHECKSUM = 15

    def __init__(self, uart):   #初始化串口
        self.uart = machine.UART(
            uart, baudrate=9600, bits=8, parity=None, stop=1)

    def __repr__(self):  #打印实例  等同于__str__
        return "Pms7003({})".format(self.uart)

    @staticmethod
    def _assert_byte(byte, expected):       #校验字节是否正确
        if byte is None or len(byte) < 1 or ord(byte) != expected:
            return False
        return True

    @staticmethod
    def _format_bytearray(buffer):    #抛出异常的byte格式化方法
        return "".join("0x{:02x} ".format(i) for i in buffer)

    def _send_cmd(self, request, response):      # 发送请求的方法

        nr_of_written_bytes = self.uart.write(request)  #uart串口发送请求 返回request的长度

        if nr_of_written_bytes != len(request):   # 校验请求
            raise UartError('Failed to write to UART') #抛出异常

        if response:  #校验应答是否正确
            time.sleep(2)
            buffer = self.uart.read(len(response))

            if buffer != response:
                raise UartError(
                    'Wrong UART response, expecting: {}, getting: {}'.format(
                        Pms7003._format_bytearray(
                            response), Pms7003._format_bytearray(buffer)
                    )
                )

    def read(self):  #读取结果方法

        while True:

            first_byte = self.uart.read(1)   #读取一个字节判断是不是 Pms7003.START_BYTE_1 是则继续 否则从新读取
            if not self._assert_byte(first_byte, Pms7003.START_BYTE_1):
                continue

            second_byte = self.uart.read(1) #读取第二个字节判断是不是 Pms7003.START_BYTE_2 是则继续读取后面30个字节
            if not self._assert_byte(second_byte, Pms7003.START_BYTE_2):
                continue

            # we are reading 30 bytes left
            read_bytes = self.uart.read(30)
            if len(read_bytes) < 30:
                continue

            data = struct.unpack('!HHHHHHHHHHHHHBBH', read_bytes)   #采用大端的方式解包，返回array，内有16个数据结果 具体为上面定义的索引

            checksum = Pms7003.START_BYTE_1 + Pms7003.START_BYTE_2  #计算校验和 先加前俩字节
            checksum += sum(read_bytes[:28])    #与3~30字节和相加

            if checksum != data[Pms7003.PMS_CHECKSUM]:  #判断校验和
                continue

            return {    #返回结果
                'FRAME_LENGTH': data[Pms7003.PMS_FRAME_LENGTH],
                'PM1_0': data[Pms7003.PMS_PM1_0],
                'PM2_5': data[Pms7003.PMS_PM2_5],
                'PM10_0': data[Pms7003.PMS_PM10_0],
                'PM1_0_ATM': data[Pms7003.PMS_PM1_0_ATM],
                'PM2_5_ATM': data[Pms7003.PMS_PM2_5_ATM],
                'PM10_0_ATM': data[Pms7003.PMS_PM10_0_ATM],
                'PCNT_0_3': data[Pms7003.PMS_PCNT_0_3],
                'PCNT_0_5': data[Pms7003.PMS_PCNT_0_5],
                'PCNT_1_0': data[Pms7003.PMS_PCNT_1_0],
                'PCNT_2_5': data[Pms7003.PMS_PCNT_2_5],
                'PCNT_5_0': data[Pms7003.PMS_PCNT_5_0],
                'PCNT_10_0': data[Pms7003.PMS_PCNT_10_0],
                'VERSION': data[Pms7003.PMS_VERSION],
                'ERROR': data[Pms7003.PMS_ERROR],
                'CHECKSUM': data[Pms7003.PMS_CHECKSUM],
            }


class PassivePms7003(Pms7003):       #定义被动式应答方式的类   可以用中断或者采用定时器方式来读取结果 可以省电 
    """
    More about passive mode here:
    https://github.com/teusH/MySense/blob/master/docs/pms7003.md
    https://patchwork.ozlabs.org/cover/1039261/
    https://joshefin.xyz/air-quality-with-raspberrypi-pms7003-and-java/
    """
    ENTER_PASSIVE_MODE_REQUEST = bytearray(                  #定义开启被动模式的请求字节流 返回bytearray(b'BM\xe1\x00\x00\x01p')
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2, 0xe1, 0x00, 0x00, 0x01, 0x70]
    )
    ENTER_PASSIVE_MODE_RESPONSE = bytearray(                #定义开启被动模式的应答字节流
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2,
            0x00, 0x04, 0xe1, 0x00, 0x01, 0x74]
    )
    SLEEP_REQUEST = bytearray(                              #定义开启待机模式的请求字节流
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2, 0xe4, 0x00, 0x00, 0x01, 0x73]
    )
    SLEEP_RESPONSE = bytearray(                             #定义开启待机模式的应答字节流
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2,
            0x00, 0x04, 0xe4, 0x00, 0x01, 0x77]
    )
    # NO response
    WAKEUP_REQUEST = bytearray(                             #定义待机模式唤醒为正常模式的请求字节流
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2, 0xe4, 0x00, 0x01, 0x01, 0x74]
    )
    # data as response
    READ_IN_PASSIVE_REQUEST = bytearray(                    #定义索要测量结果的请求字节流
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2, 0xe2, 0x00, 0x00, 0x01, 0x71]
    )

    def __init__(self, uart):
        super().__init__(uart=uart)
        # use passive mode pms7003   使用被动模式
        self._send_cmd(request=PassivePms7003.ENTER_PASSIVE_MODE_REQUEST,
                       response=PassivePms7003.ENTER_PASSIVE_MODE_RESPONSE)

    def sleep(self):   #睡眠
        self._send_cmd(request=PassivePms7003.SLEEP_REQUEST,
                       response=PassivePms7003.SLEEP_RESPONSE)

    def wakeup(self):  #唤醒
        self._send_cmd(request=PassivePms7003.WAKEUP_REQUEST, response=None)

    def read(self):   #读取数据
        self._send_cmd(
            request=PassivePms7003.READ_IN_PASSIVE_REQUEST, response=None)
        return super().read()
