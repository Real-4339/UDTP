import time
import struct
import crcmod 
import logging
import binascii

from go.time import Time
from go.flags import Flags


''' Global variables '''
LOGGER = logging.getLogger("Packet")


class Packet:
    def __init__(self, data: bytes, flags: Flags = None, seq_num: int = 0):
        self.__time_to_live: int = time.time()
        self.__seq_num = seq_num
        self.__flags = flags
        self.__data = data

    @property
    def flags(self) -> Flags:
        return self.__flags
    
    @property
    def seq_num(self) -> int:
        return self.__seq_num
    
    @seq_num.setter
    def seq_num(self, value: int) -> None:
        self.__seq_num = value
    
    def time_is_valid(self) -> bool:
        ''' Check if packet is still alive '''
        
        if time.time() - self.__time_to_live > Time.TTL:
            return False
        
        return True

    @staticmethod
    def construct(data: bytes, flags: Flags, seq_num: int) -> bytes | None:
        ''' Construct packet in Bytes '''
        crc16_func = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
        crc16 = crc16_func(data)

        try:
            header = struct.pack('!BHB', flags.value, crc16, seq_num)
        except struct.error as e:
            LOGGER.error("Failed to pack header: %s", e)
            return None
        
        return header + data

    @staticmethod
    def deconstruct(data: bytes) -> 'Packet' or None:
        ''' Deconstruct bytes to packet '''
        if len(data) < 4:
            LOGGER.error("Packet is too short")
            return None
        
        try:
            flags, crc16, seq_num = struct.unpack('!BHB', data[:4])
        except struct.error as e:
            LOGGER.error("Failed to unpack header: %s", e)
            return None

        packet_data = data[4:]
        
        return Packet(packet_data, Flags(flags), seq_num)

    @staticmethod
    def is_valid(data: bytes) -> bool:
        ''' Check if packet is valid '''
        if len(data) < 4:
            LOGGER.error("Packet is too short")
            return False
        
        flags, crc16, seq_num = struct.unpack('!BHB', data[:4]) 
        packet_data = data[4:]

        crc16_func = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
        computed_crc16 = crc16_func(packet_data)

        if computed_crc16 != crc16:
            return False
        
        return True
    
    @staticmethod
    def devide(data: bytes, seq_num: int, fragment_size: int) -> list['Packet'] | None:
        ''' Devide data into packets '''
        packets = []
        data_size = len(data)
        packets_num = (data_size + fragment_size - 1) // fragment_size # Number of packets needed
        
        for i in range(packets_num):
            start_idx = i * fragment_size
            end_idx = (i + 1) * fragment_size
            packet_data = data[start_idx:end_idx]
        
        packet = Packet.construct(packet_data, Flags.NONE, seq_num + i)
        if packet is None:
            LOGGER.error("Failed to construct packet")
            return None
        
        packets.append(packet)
        
        return packets