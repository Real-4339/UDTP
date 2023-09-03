from enum import IntFlag


class Flags(IntFlag):
    SYN  = 0b00000001 # 1
    ACK  = 0b00000010 # 2
    SACK = 0b00000100 # 4 Super ACK
    MSG  = 0b00001000 # 8 Message
    INIT = 0b00010000 # 16 Init file transfer
    NONE = 0b00100000 # 32 None
    WM   = 0b01000000 # 64 Window Multiplier
    FIN  = 0b10000000 # 128