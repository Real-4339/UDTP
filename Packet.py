import struct
from enum import IntFlag


class Flags(IntFlag):
    SYN  = 0b00000001 # 1
    ACK  = 0b00000010 # 2
    SACK = 0b00000100 # 4 Super ACK
    MSG  = 0b00001000 # 8 Message
    INIT = 0b00010000 # 16 Init file transfer
    KA   = 0b00100000 # 32 Keep alive
    WM   = 0b01000000 # 64 Window Multiplier
    FIN  = 0b10000000 # 128


class Packet:
    def __init__(self, data: bytes, flags: Flags = None, seq: int = 0, address_from: tuple = None, address_to: tuple = None): # TODO: add crc_16
        if flags is None:
            flags = Flags(0)
        self.__seq = seq
        self.__crc_16 = 0
        self.__address_from = address_from
        self.__address_to = address_to
        self.__flags = flags
        self.__data = data
        self.__header = self._create_header(flags, seq)

    # protected
    def _create_header(self, flags: Flags = None, seq: int = 0):
        upd_header = struct.pack('!BB', flags, seq)
        return upd_header

    # public, needs for creating packet
    def pack(self, data: bytes, flags: Flags = None, seq: int = 0, address_from: tuple = None, address_to: tuple = None) -> 'Packet':
        self.__init__(data, flags, seq, address_from, address_to)
    
    # public, needs for decrypting data to packet
    def unpack(self, data: bytes, address_to: tuple, address_from: tuple) -> 'Packet': # data = header + data, TODO: add crc_16
        udp_header = data[:2]
        flags, seq = struct.unpack('!BB', udp_header)
        self.__init__(data[2:], flags, seq, address_from, address_to)
    
    # public, needs for creating real packet with header
    def create_packet(self) -> bytes:
        return self.__header + self.__data

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

    @property
    def address_from(self) -> tuple:
        return self.__address_from
    
    @address_from.setter
    def address_from(self, address_from: tuple):
        self.__address_from = address_from
    
    @property
    def address_to(self) -> tuple:
        return self.__address_to
    
    @address_to.setter
    def address_to(self, address_to: tuple):
        self.__address_to = address_to

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