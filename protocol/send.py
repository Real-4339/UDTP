import time
import logging

from go.size import Size
from go.time import Time
from packet import Packet
from go.flags import Flags
from typing import Callable
from go.status import Status
from go.adressinfo import AddressInfo


""" Global variables """
LOGGER = logging.getLogger("Sender")


class Sender:
    """
    Sender class which will send messages and files.
    Devide data into packets if needed.
    Handle sequence numbers.
    Have buffer for packets.
    """

    def __init__(
        self,
        send_func: Callable,
        addr: AddressInfo,
        type: str = "file",
        name: str = None,
        extention: str = None,
        transfer_flag: int = None,
        fragment_size: int = 1468,
    ):
        self.__seq_num = 0
        self.__type = type
        self.__name = name
        self.__client = addr
        self.__ext = extention
        self.__send_func = send_func
        self.__fragment_size = fragment_size
        self.__own_transfer_flag = transfer_flag

        self.__window_size = Size.WINDOW_SIZE
        self.__started = False

        self.__acks: set[int] = set()
        self.__all_packets: list[Packet] = []
        self.__sent_packets: list[Packet] = []

        # self.__count_of_acks = 0
        # self.__count_of_packets = 0

        self.__alive = Status.ALIVE
        self.__last_time = time.time()

        self.extended = 2

    @property
    def alive(self) -> Status:
        return self.__alive

    @property
    def ext(self) -> str:
        return self.__ext

    @property
    def name(self) -> str:
        return self.__name

    @property
    def own_transfer_flag(self) -> Flags:
        return self.__own_transfer_flag

    @property
    def fragment_size(self) -> int:
        return self.__fragment_size

    @property
    def client(self) -> AddressInfo:
        return self.__client

    def prepare_data(self, data: bytes, flags: Flags) -> None:
        """Prepare data for sending"""

        packets = Packet.devide(
            data, self.__seq_num, fragment_size=self.fragment_size, flags=flags
        )

        # LOGGER.info(f"Sending {len(packets)} packets to {self.__client}")

        self.__all_packets.extend(packets)

        # self.__count_of_packets = len(self.__all_packets)
        # LOGGER.info(f"len(self.__all_packets): {len(self.__all_packets)}")

    def receive(self, packet: Packet) -> None:
        """Receive ack"""

        if packet.flags == Flags.ACK:
            # LOGGER.info(f"Received ACK from {self.__client}, time: {time.time()}")
            self.__last_time = time.time()
            self.__acks.add(packet.seq_num)
            # self.__count_of_acks += 1
            return

        if packet.flags == Flags.FIN:
            LOGGER.info(f"File transfer is finished from {self.__client}")
            self.__alive = Status.DEAD
            return

        if packet.flags == Flags.SACK:
            LOGGER.info(f"Starting sending data to {self.__client}")
            self.__last_time = time.time()
            self.__started = True
            return

    def time_is_valid(self) -> bool:
        """Check if connection is still alive"""
        if time.time() - self.__last_time > Time.KEEPALIVE:
            return False

        return True

    def time_to_resend(self) -> bool:
        if time.time() - self.__last_time > Time.RESEND:
            return True

        return False

    def kill(self) -> None:
        """Kill connection"""
        self.__alive = Status.DEAD

    def _start(self) -> bool:
        """Only for waiting SACK to start sending data"""
        if not self.__started and self.time_to_resend():
            LOGGER.info(f"Resending FILE/MSG to {self.__client}")
            if self.__type == "file":
                self.__send_func(
                    Packet.construct(
                        f"{self.name}{self.ext}:{self.own_transfer_flag}".encode(),
                        Flags.FILE,
                        0,
                    ),
                    self.__client,
                )
            else:
                self.__send_func(
                    Packet.construct(
                        f"{self.own_transfer_flag}".encode(), Flags.MSG, 0
                    ),
                    self.__client,
                )
            return False
        if self.__started:
            return True

        return False

    def _send_restof_data(self, num_to_skip: int) -> None:
        """Send rest of data"""

        packets_to_send = []

        while (
            self.__all_packets
            and len(packets_to_send) < self.__window_size - num_to_skip
        ):
            if self.__all_packets[0].seq_num == 0 and self.__sent_packets != []:
                break
            packet = self.__all_packets.pop(0)
            packets_to_send.append(packet)
            self.__sent_packets.append(packet)

        for packet in packets_to_send:
            packet = Packet.packet_to_bytes(packet)
            self.__send_func(packet, self.__client)

        """ Update sequence number """
        # LOGGER.info(f"seq_num: {self.__seq_num}")
        self.__seq_num = (self.__seq_num + len(packets_to_send)) % (
            2**8
        )  # HACK: 8 bits
        # LOGGER.info(f"new seq_num: {self.__seq_num}")

        if self.__all_packets == []:  # self.__count_of_acks >= self.__count_of_packets:
            """Send FIN"""
            LOGGER.info(f"sending fin, seq: {self.__seq_num}")
            self.__send_func(
                Packet.construct(
                    data=f"{self.own_transfer_flag}".encode(),
                    flags=Flags.FIN,
                    seq_num=self.__seq_num,
                ),
                self.__client,
            )
            self.extended -= 1
            self.__seq_num += 1
            if self.extended == 0:
                self.__alive = Status.DEAD

    def _iterator(self):
        """Handle packets"""
        if self.__alive == Status.DEAD:
            return Status.FINISHED

        """ Check if we can start """
        if not self._start():
            LOGGER.info(f"Waiting for SACK from {self.__client}")
            return Status.SLEEPING

        if not self.time_is_valid():
            LOGGER.info(f"Transfer is not alive anymore")
            self.__alive = Status.DEAD
            return Status.FINISHED

        # for pack in self.__sent_packets:
        #     LOGGER.info(f"packet: {pack}")

        # LOGGER.info(f"len(self.__sent_packets), before: {len(self.__sent_packets)}")

        """ Check for acknowledgments and remove acked packets from sent_packets"""
        self.__sent_packets = [
            packet
            for packet in self.__sent_packets
            if packet.seq_num not in self.__acks
        ]

        # LOGGER.info(f"len(self.__sent_packets), after: {len(self.__sent_packets)}")

        """ Find packets which ttl is expired """
        expired_packets = [
            packet for packet in self.__sent_packets if packet.time_is_valid() == False
        ]

        # LOGGER.info(f"exp_packs: {len(expired_packets)}")

        """ Resend packets if needed """
        for packet in expired_packets:
            packet = Packet.packet_to_bytes(packet)
            self.__send_func(packet, self.__client)

        """ Send rest of data """
        count = len(self.__sent_packets) - len(expired_packets)
        self._send_restof_data(count)

        self.__acks.clear()

        return Status.RUNNING
