from enum import IntFlag


class Time(IntFlag):
    TTL = 4
    RESEND = 5
    KEEPALIVE = 10
