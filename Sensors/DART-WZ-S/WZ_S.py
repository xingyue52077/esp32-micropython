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
                return False

            checksum = ~sum(read_bytes[:7])+1
            checksum &= 0xFF  # 强制截断后八位

            if checksum != read_bytes[WZ_S.CHECKSUM]:  # 判断校验和
                return False

            ppb = int(read_bytes[WZ_S.MIC_HIGH]) * \
                256+int(read_bytes[WZ_S.MIC_LOW])

            mic = 0.00123*ppb  # 计算浓度 mg/m3

            return {'HCHO_MIC': mic}


class PassiveWZ_S(WZ_S):  # 定义被动式应答方式的类   可以用中断或者采用定时器方式来读取结果 可以省电

    ENTER_PASSIVE_MODE_REQUEST = bytearray(  # 定义开启被动模式的请求字节流
        [WZ_S.START_BYTE,  0x01, 0x78, 0x41, 0x00, 0x00, 0x00, 0x00, 0x46]
    )
    STOP_PASSIVE_MODE_RESPONSE = bytearray(  # 定义关闭被动模式的应答字节流
        [WZ_S.START_BYTE,  0x01, 0x78, 0x40, 0x00, 0x00, 0x00, 0x00, 0x47]
    )
    # data as response
    READ_IN_PASSIVE_REQUEST = bytearray(  # 定义索要测量结果的请求字节流
        [WZ_S.START_BYTE,  0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79]
    )

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
                        WZ_S._format_bytearray(
                            response), WZ_S._format_bytearray(buffer)
                    )
                )

    def __init__(self, uart):
        super().__init__(uart=uart)
        # use passive mode pms7003   使用被动模式
        self._send_cmd(request=PassiveWZ_S.ENTER_PASSIVE_MODE_REQUEST,
                       response=None)

    def stoppassive(self):  # 唤醒
        self._send_cmd(
            request=PassiveWZ_S.STOP_PASSIVE_MODE_RESPONSE, response=None)

    def _read(self):
        super().read()

    def passiveread(self):  # 读取数据
        self._send_cmd(
            request=PassiveWZ_S.READ_IN_PASSIVE_REQUEST, response=None)
        
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
            second_byte = read_bytes[0]
            if not self._assert_byte(second_byte, 0x86):
                return False

            checksum = ~sum(read_bytes[:7])+1
            checksum &= 0xFF  # 强制截断后八位

            if checksum != read_bytes[WZ_S.CHECKSUM]:  # 判断校验和
                return False

            ppb = int(read_bytes[5]) * \
                256+int(read_bytes[6])

            mic = 0.00123*ppb  # 计算浓度 mg/m3

            return {'HCHO_MIC': mic}
