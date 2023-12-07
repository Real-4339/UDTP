import os
import time
import logging

from go.time import Time
from go.size import Size
from packet import Packet
from go.flags import Flags
from typing import Callable
from go.status import Status
from go.adressinfo import AddressInfo


""" Global variables """
LOGGER = logging.getLogger("Receiver")


class Receiver:
    """
    Receiver class which will receive messages and files.
    Devide data into packets if needed.
    Handle sequence numbers.
    Have buffer for packets.
    """

    def __init__(
        self,
        send_func: Callable,
        addr: AddressInfo,
        name: str = None,
        extention: str = None,
        transfer_flag: int = None,
        fragment_size: int = 1468,
    ):
        self.__seq_num = 0
        self.__name = name
        self.__client = addr
        self.__ext = extention
        self.__send_func = send_func
        self.__fragment_size = fragment_size
        self.__own_transfer_flag = transfer_flag

        self.__acks: set[int] = set()
        self.__packets: set[Packet] = set()
        self.__size_of_all_data = 0
        self.__size_of_all_headers = 0

        self.__alive = Status.ALIVE
        self.__last_time = time.time()

        self.__started = None
        self.__ended = None

    @property
    def alive(self) -> Status:
        return self.__alive

    @property
    def name(self) -> str:
        return self.__name

    @property
    def ext(self) -> str:
        return self.__ext

    @property
    def own_transfer_flag(self) -> Flags:
        return self.__own_transfer_flag

    @property
    def fragment_size(self) -> int:
        return self.__fragment_size

    @property
    def client(self) -> AddressInfo:
        return self.__client

    def get_packets(self) -> set[Packet]:
        """Get packets"""

        return self.__packets

    def time_is_valid(self) -> bool:
        """Check if receiver is still alive"""

        if time.time() - self.__last_time > Time.KEEPALIVE:
            return False

        return True

    def kill(self) -> None:
        """Kill receiver"""

        self.__alive = Status.DEAD

    def receive(self, packet: Packet) -> None:
        """Receive FILE, MSG, FIN"""

        self.__size_of_all_data += len(packet.data) + 4
        self.__size_of_all_headers += 4

        if packet.flags == Flags.FILE:
            self._process_file(packet)

        elif packet.flags == Flags.MSG:
            self._send_sack()

        elif packet.flags == Flags.FIN:
            self._process_fin(packet)

        self.__seq_num += 1

    def receive_data(self, packet: Packet) -> None:
        """Receive data"""

        self.__size_of_all_data += len(packet.data) + 4
        self.__size_of_all_headers += 4

        if packet not in self.__packets:
            self.__seq_num += 1

            self.__acks.add(packet.seq_num)
            self.__packets.add(packet)
            self.__last_time = time.time()

        else:
            """Resend ack"""
            ack = Packet.construct(
                data=f"{self.own_transfer_flag}".encode(),
                flags=Flags.ACK,
                seq_num=packet.seq_num,
            )
            self.__send_func(ack, self.__client)
            self.__size_of_all_headers += 4
            self.__size_of_all_data += len(ack)

    def _send_sack(self) -> None:
        """Send SACK"""
        LOGGER.info(f"Sending SACK to {self.__client}")
        self.__send_func(
            Packet.construct(
                data=f"{self.own_transfer_flag}".encode(),
                flags=Flags.SACK,
                seq_num=self.__seq_num,
            ),
            self.__client,
        )
        self.__size_of_all_headers += 4
        self.__size_of_all_data += len(str(self.own_transfer_flag).encode()) + 4
        self.__started = time.time()

    def _process_file(self, packet: Packet) -> None:
        """Process file"""

        data = packet.data.decode().split(":")

        name_ext, flag = data[0], int(data[1])
        try:
            name, ext = name_ext.split(".")
        except ValueError:
            name, ext = name_ext, ""

        self.__name = name
        self.__ext = ext
        self.__own_transfer_flag = flag

        self._send_sack()

    def _process_fin(self, packet: Packet) -> None:
        """Process FIN"""

        self.__alive = Status.DEAD
        self.__ended = time.time()

        LOGGER.info(
            f"File transfer is finished from {self.__client} in {self.__ended - self.__started} seconds,"
            f"with number of packets: {len(self.__packets)}"
        )

        """ Send FIN """
        self.__send_func(
            Packet.construct(
                data=f"{self.own_transfer_flag}".encode(), flags=Flags.FIN, seq_num=3
            ),
            self.__client,
        )

        self.__size_of_all_headers += 4
        self.__size_of_all_data += len(str(self.own_transfer_flag).encode()) + 4

        LOGGER.info(
            f"In percentage: {(self.__size_of_all_headers / self.__size_of_all_data) * 100}",
        )

        LOGGER.info(f"{self.__size_of_all_data}, {self.__size_of_all_headers}")

        if self.name is not None and self.ext is not None:
            """Create file from packets and save it"""
            file_data = Packet.merge_new(self.__packets)
            file_name = f"{self.__name}_{int(time.time())}.{self.__ext}"
            if self.__ext == "":
                file_name = f"{self.__name}_{int(time.time())}"

            """ Construct fpath """
            script_dir = os.path.dirname(os.path.abspath(__file__))
            full_file_path = os.path.join(script_dir, "files", file_name)

            try:
                with open(full_file_path, "wb") as f:
                    f.write(file_data)
                LOGGER.info(f"Received file from {self.__client}")
                LOGGER.info(f"File name: {self.__name}_{int(time.time())}.{self.__ext}")
                LOGGER.info(
                    f"File size: {len(self.__packets) * self.fragment_size} bytes"
                )
            except Exception as e:
                LOGGER.error(f"Failed to save file: {e}")

        else:
            """Create message from packets and print it"""
            message = Packet.merge_new(self.__packets).decode()
            LOGGER.info(f"Received message from {self.__client} : {message}")

    def _acknowledge_data(self) -> None:
        """Acknowledge data"""

        if len(self.__acks) == 0:
            return

        for seq_num in self.__acks:
            ack = Packet.construct(
                data=f"{self.own_transfer_flag}".encode(),
                flags=Flags.ACK,
                seq_num=seq_num,
            )
            self.__send_func(ack, self.__client)
            self.__size_of_all_headers += 4
            self.__size_of_all_data += len(str(self.own_transfer_flag).encode())

        self.__acks.clear()

    def _iterator(self) -> Status:
        """Iterate over packets"""

        if self.__alive == Status.DEAD or not self.time_is_valid():
            self.__alive = Status.DEAD
            return Status.FINISHED

        self._acknowledge_data()

        return Status.SLEEPING
