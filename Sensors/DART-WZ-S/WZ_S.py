import machine  # 导入引脚控制
import struct  # 导入格式化字符串模块 https://blog.csdn.net/qq_30638831/article/details/80421019
import time


class UartError(Exception):  # 定义一个异常类 继承得是Exception类
    pass


class WZ_S:

    START_BYTE = 0xFF

    GAS_NAME = 0
    UNITS = 1
    DECIMAL = 2
    MIC_HIGH = 3
    MIC_LOW = 4
    FULL_SCALE_HIGH = 5
    FULL_SCALE_LOW = 6
    CHECKSUM = 7

    def __init__(self, uart):  # 初始化串口
        self.uart = machine.UART(
            uart, baudrate=9600, bits=8, parity=None, stop=1)

    def __repr__(self):  # 打印实例  等同于__str__
        return "WZ-S({})".format(self.uart)

    @staticmethod
    def _assert_byte(byte, expected):  # 校验字节是否正确
        if byte is None or len(byte) < 1 or ord(byte) != expected:
            return False
        return True

    @staticmethod
    def _format_bytearray(buffer):  # 抛出异常的byte格式化方法
        return "".join("0x{:02x} ".format(i) for i in buffer)

    def _send_cmd(self, request, response):      # 发送请求的方法

        nr_of_written_bytes = self.uart.write(
            request)  # uart串口发送请求 返回request的长度

        if nr_of_written_bytes != len(request):   # 校验请求
            raise UartError('Failed to write to UART')  # 抛出异常

        if response:  # 校验应答是否正确
            time.sleep(2)
            buffer = self.uart.read(len(response))

            if buffer != response:
                raise UartError(
                    'Wrong UART response, expecting: {}, getting: {}'.format(
                        Pms7003._format_bytearray(
                            response), Pms7003._format_bytearray(buffer)
                    )
                )

    def read(self):  # 读取结果方法

        while True:

            # 读取一个字节判断是不是 Pms7003.START_BYTE_1 是则继续 否则从新读取
            first_byte = self.uart.read(1)
            if not self._assert_byte(first_byte, WZ_S.START_BYTE):
                continue

            # we are reading 30 bytes left
            read_bytes = self.uart.read(8)
            if len(read_bytes) < 8:
                continue

            # 读取第二个字节判断是不是 Pms7003.START_BYTE_2 是则继续读取后面30个字节
            second_byte = read_bytes[WZ_S.GAS_NAME]
            if not self._assert_byte(second_byte, 0x17):
                continue

            checksum = ~sum(read_bytes[:7])+1
            checksum &= 0xFF  # 强制截断后八位

            if checksum != read_bytes[WZ_S.CHECKSUM]:  # 判断校验和
                continue

            ppb = int(read_bytes[WZ_S.MIC_HIGH]) * \
                256+int(read_bytes[WZ_S.MIC_LOW])

            MIC = 0.00123*ppb  # 计算浓度 mg/m3

            return {'HCHO_MIC': MIC}


class PassiveWZ_S(WZ_S):  # 定义被动式应答方式的类   可以用中断或者采用定时器方式来读取结果 可以省电
    
    ENTER_PASSIVE_MODE_REQUEST = bytearray(  # 定义开启被动模式的请求字节流 返回bytearray(b'BM\xe1\x00\x00\x01p')
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2, 0xe1, 0x00, 0x00, 0x01, 0x70]
    )
    ENTER_PASSIVE_MODE_RESPONSE = bytearray(  # 定义开启被动模式的应答字节流
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2,
            0x00, 0x04, 0xe1, 0x00, 0x01, 0x74]
    )
    SLEEP_REQUEST = bytearray(  # 定义开启待机模式的请求字节流
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2, 0xe4, 0x00, 0x00, 0x01, 0x73]
    )
    SLEEP_RESPONSE = bytearray(  # 定义开启待机模式的应答字节流
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2,
            0x00, 0x04, 0xe4, 0x00, 0x01, 0x77]
    )
    # NO response
    WAKEUP_REQUEST = bytearray(  # 定义待机模式唤醒为正常模式的请求字节流
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2, 0xe4, 0x00, 0x01, 0x01, 0x74]
    )
    # data as response
    READ_IN_PASSIVE_REQUEST = bytearray(  # 定义索要测量结果的请求字节流
        [Pms7003.START_BYTE_1, Pms7003.START_BYTE_2, 0xe2, 0x00, 0x00, 0x01, 0x71]
    )

    def __init__(self, uart):
        super().__init__(uart=uart)
        # use passive mode pms7003   使用被动模式
        self._send_cmd(request=PassivePms7003.ENTER_PASSIVE_MODE_REQUEST,
                       response=PassivePms7003.ENTER_PASSIVE_MODE_RESPONSE)

    def sleep(self):  # 睡眠
        self._send_cmd(request=PassivePms7003.SLEEP_REQUEST,
                       response=PassivePms7003.SLEEP_RESPONSE)

    def wakeup(self):  # 唤醒
        self._send_cmd(request=PassivePms7003.WAKEUP_REQUEST, response=None)

    def read(self):  # 读取数据
        self._send_cmd(
            request=PassivePms7003.READ_IN_PASSIVE_REQUEST, response=None)
        return super().read()
