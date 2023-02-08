import struct
from enum import IntFlag


class Flags(IntFlag):
    SYN  = 0b00000001 # 1
    ACK  = 0b00000010 # 2
    SACK = 0b00000100 # 4
    MSG  = 0b00001000 # 8
    INIT = 0b00010000 # 16
    KA   = 0b00100000 # 32
    WM   = 0b01000000 # 64
    FIN  = 0b10000000 # 128


class Packet:
    def __init__(self, data: bytes, flags: Flags = None, seq: int = 0):
        if flags is None:
            flags = Flags(0)
        self.__seq = seq
        self.__crc_16 = 0
        self.__flags = flags
        self.__data = data
        self.__header = self.create_packet()

    # protected
    def _create_header(self, flags: Flags = None, seq: int = 0):
        upd_header = struct.pack('!BB', flags, seq)
        return upd_header
    
    # protected
    def _undo_packet(self, packet: 'Packet'):
        ...

    @property
    def data(self) -> bytes:
        return self.__data
    
    @data.setter
    def data(self, data: bytes):
        self.__data = data

    @property
    def seq(self) -> int:
        return self.__seq
    
    @seq.setter
    def seq(self, seq: int):
        self.__seq = seq

    @property
    def header(self) -> bytes:
        return self.__header

    @property
    def flags(self) -> Flags:
        return self.__flags
    
    @flags.setter
    def flags(self, flags: Flags):
        self.__flags = flags

    @property
    def crc_16(self) -> int:
        return self.__crc_16

    @crc_16.setter
    def crc_16(self, crc_16: int):
        self.__crc_16 = crc_16

    def __str__(self):
        return f'Packet(data={self.data}, address={self.address})'

    def __repr__(self):
        return f'Packet(data={self.data}, address={self.address})'

    def __eq__(self, other):
        return self.data == other.data and self.address == other.address

    def __hash__(self):
        return hash((self.data, self.address))

    def __bool__(self):
        return bool(self.data) and bool(self.address)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __contains__(self, item):
        return item in self.data

    def __add__(self, other):
        return Packet(self.data + other.data, self.address)

    def __sub__(self, other):
        return Packet(self.data - other.data, self.address)

    def __mul__(self, other):
        return Packet(self.data * other.data, self.address)

    def __truediv__(self, other):
        return Packet(self.data / other.data, self.address)

    def __floordiv__(self, other):
        return Packet(self.data // other.data, self.address)

    def __mod__(self, other):
        return Packet(self.data % other.data, self.address)

    def __divmod__(self, other):
        return Packet(divmod(self.data, other.data), self.address)

    def __pow__(self, power, modulo=None):
        return Packet(pow(self.data, power, modulo), self.address)

    def __lshift__(self, other):
        return Packet(self.data << other.data, self.address)

    def __rshift__(self, other):
        return Packet(self.data >> other.data, self.address)

    def __and__(self, other):
        return Packet(self.data & other.data, self.address)

    def __xor__(self, other):
        return Packet(self.data ^ other.data, self.address)

    def __or__(self, other):
        return Packet(self.data | other.data, self.address)