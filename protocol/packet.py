from __future__ import annotations

import time
import struct
import crcmod
import logging

from go.time import Time
from go.flags import Flags


""" Global variables """
LOGGER = logging.getLogger("Packet")


class Packet:
    def __init__(self, data: bytes, flags: Flags = None, seq_num: int = 0):
        self.__time_to_live: int = time.time()
        self.__time_stamp: int = time.perf_counter()
        self.__seq_num = seq_num
        self.__flags = flags
        self.__data = data

    @property
    def flags(self) -> Flags:
        return self.__flags

    @property
    def seq_num(self) -> int:
        return self.__seq_num

    @property
    def data(self) -> bytes:
        return self.__data

    @property
    def time_stamp(self) -> int:
        return self.__time_stamp

    @seq_num.setter
    def seq_num(self, value: int) -> None:
        self.__seq_num = value

    def time_is_valid(self) -> bool:
        """Check if packet is still alive"""

        if time.time() - self.__time_to_live > Time.TTL:
            return False

        return True

    @staticmethod
    def construct_packet(data: bytes, flags: Flags, seq_num: int) -> Packet | None:
        """Construct packet"""
        if data is None:
            LOGGER.error("Data is None")
            return None
        if flags is None:
            LOGGER.error("Flags is None")
            return None
        if seq_num is None:
            LOGGER.error("Seq_num is None")
            return None
        return Packet(data, flags, seq_num)

    @staticmethod
    def packet_to_bytes(packet: Packet) -> bytes | None:
        """Convert packet to bytes"""
        if packet is None:
            LOGGER.error("Packet is None")
            return None
        if not isinstance(packet, Packet):
            LOGGER.error("Packet is not instance of Packet")
            return None
        return Packet.construct(packet.__data, packet.__flags, packet.__seq_num)

    @staticmethod
    def packet_to_bytes_broken_crc(packet: Packet) -> bytes | None:
        """Convert packet to bytes, Test purpose only"""
        if packet is None:
            LOGGER.error("Packet is None")
            return None
        if not isinstance(packet, Packet):
            LOGGER.error("Packet is not instance of Packet")
            return None
        return Packet.construct_broken_crc(
            packet.__data, packet.__flags, packet.__seq_num
        )

    @staticmethod
    def construct(data: bytes, flags: Flags, seq_num: int) -> bytes | None:
        """Construct packet in Bytes"""
        crc16_func = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
        crc16 = crc16_func(data)

        try:
            header = struct.pack("!BHB", flags, crc16, seq_num)
        except struct.error as e:
            LOGGER.error("Failed to pack header: %s", e)
            return None

        return header + data

    @staticmethod
    def construct_broken_crc(data: bytes, flags: Flags, seq_num: int) -> bytes | None:
        """Construct packet in Bytes, Test purpose only !!!"""
        crc16_func = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
        crc16 = crc16_func(data)

        try:
            header = struct.pack("!BHB", flags, crc16 + 1, seq_num)
        except struct.error as e:
            LOGGER.error("Failed to pack header: %s", e)
            return None

        return header + data

    @staticmethod
    def deconstruct(data: bytes) -> Packet | None:
        """Deconstruct bytes to packet"""
        if len(data) < 4:
            LOGGER.error("Packet is too short")
            return None

        try:
            flags, crc16, seq_num = struct.unpack("!BHB", data[:4])
        except struct.error as e:
            LOGGER.error("Failed to unpack header: %s", e)
            return None

        packet_data = data[4:]

        return Packet(packet_data, Flags(flags), seq_num)

    @staticmethod
    def is_valid(data: bytes) -> bool:
        """Check if packet is valid"""
        if len(data) < 4:
            LOGGER.error("Packet is too short")
            return False

        flags, crc16, seq_num = struct.unpack("!BHB", data[:4])
        packet_data = data[4:]

        crc16_func = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
        computed_crc16 = crc16_func(packet_data)

        if computed_crc16 != crc16:
            LOGGER.error("CRC16 is not valid")
            return False

        return True

    @staticmethod
    def devide(
        data: bytes, seq_num: int, fragment_size: int, flags: Flags
    ) -> list[Packet] | None:
        """Devide data into packets"""
        packets = []
        data_size = len(data)
        packets_num = (
            data_size + fragment_size - 1
        ) // fragment_size  # Number of packets needed

        # LOGGER.debug(f"Packets num: {packets_num}")

        current_seq_num = 0

        for i in range(packets_num):
            start_idx = i * fragment_size
            end_idx = min(start_idx + fragment_size, data_size)
            packet_data = data[start_idx:end_idx]

            """ Calculate the seq_num with wrap around """
            current_seq_num = (seq_num + i) % (2**8)  # HACK: 8 bits for seq_num
            # LOGGER.debug(f"Current seq_num: {current_seq_num}")

            packet = Packet.construct_packet(packet_data, flags, current_seq_num)

            packets.append(packet)

        return packets

    @staticmethod
    def merge(packets: list[Packet]) -> bytes | None:
        """Merge packets into one"""
        if not packets:
            LOGGER.error("Packets list is empty")
            return None

        data = b""
        expected_seq_num = packets[0].seq_num
        original_len = len(packets)

        # ''' Testing with slising packets '''
        # packets[13].__time_stamp = packets[13].__time_stamp + 0.0783
        # packets[14].__time_stamp = packets[14].__time_stamp + 0.0783
        # packets[15].__time_stamp = packets[15].__time_stamp + 0.0783
        # packets = packets[0:13] + packets[16: 210] + packets[13:16] + packets[210:]

        start = packets[0].time_stamp
        arr: list[tuple] = []

        count_of_255_packets = len(packets) // 255

        for i in range(1, count_of_255_packets + 1):
            end = packets[(i * 255) + (i - 1)].time_stamp
            arr.append((start, end))
            start = packets[(i * 255) + (i - 1) + 1].time_stamp

        if count_of_255_packets * 255 < len(packets):
            arr.append((start, packets[-1].time_stamp))

        timestamp_ranges = {}
        for start, end in arr:
            small_list = [
                packet for packet in packets if start <= packet.time_stamp <= end
            ]
            small_list = sorted(small_list, key=lambda packet: packet.seq_num)
            timestamp_ranges[end] = small_list

        timestamp_ranges = dict(sorted(timestamp_ranges.items()))

        merged_packets = []
        for value in timestamp_ranges.values():
            merged_packets.extend(value)

        packets = merged_packets

        for packet in packets:
            if packet.seq_num != expected_seq_num:
                LOGGER.debug(
                    "Packet seq is not expected, num, expeted: %s: %s",
                    packet.seq_num,
                    expected_seq_num,
                )
                return None

            data += packet.data
            expected_seq_num = (expected_seq_num + 1) % (2**8)

        if original_len != len(packets):
            LOGGER.error("Packets are missing")
            return None

        return data

    @staticmethod
    def merge_new(packets: set[Packet]) -> bytes | None:
        """Merge packets into one"""
        if not packets:
            LOGGER.error("Packets list is empty")
            return None

        packets = sorted(packets, key=lambda packet: packet.time_stamp)

        data = b""
        original_len = len(packets)

        start = 0
        arr: list[tuple] = []

        count_of_255_packets = len(packets) // 255

        for i in range(1, count_of_255_packets + 1):
            end = (i * 255) + (i - 1)
            arr.append((start, end))
            start = (i * 255) + (i - 1) + 1

        if count_of_255_packets * 255 < len(packets):
            arr.append((start, len(packets) - 1))

        for start, end in arr:
            small_list = packets[start : end + 1]
            small_list = sorted(small_list, key=lambda packet: packet.seq_num)
            packets[start : end + 1] = small_list

        expected_seq_num = packets[0].seq_num

        for packet in packets:
            if packet.seq_num != expected_seq_num:
                LOGGER.debug(
                    "Packet seq is not expected, num, expeted: %s: %s",
                    packet.seq_num,
                    expected_seq_num,
                )
                return None

            data += packet.data
            expected_seq_num = (expected_seq_num + 1) % (2**8)

        if original_len != len(packets):
            LOGGER.error("Packets are missing")
            return None

        return data

    def __repr__(self) -> str:
        return f"Packet({self.__flags}, {self.__seq_num}, {self.__time_stamp})"

    def __str__(self) -> str:
        return f"Packet({self.__flags}, {self.__seq_num}, {self.__time_stamp})"

    def __hash__(self) -> int:
        return hash((self.__data, self.__flags, self.__seq_num))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Packet):
            return NotImplemented
        return (
            self.__data == other.__data
            and self.__flags == other.__flags
            and self.__seq_num == other.__seq_num
        )
