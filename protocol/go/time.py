from enum import IntFlag


class Time(IntFlag):
    """Time constants"""

    CONN_RESEND = 1
    TTL = 4
    RESEND = 5
    KEEPALIVE = 10
