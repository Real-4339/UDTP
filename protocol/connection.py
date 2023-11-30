import time
import logging

from send import Sender
from go.time import Time
from packet import Packet
from recv import Receiver
from go.flags import Flags
from typing import Callable
from go.status import Status
from go.adressinfo import AddressInfo


""" Global variables """
LOGGER = logging.getLogger("Connection")


class ConnectionWith:
    def __init__(self, addr: AddressInfo, send_func: Callable, frag_size: int):
        self._add_iterator = NotImplemented
        self.__send_func = send_func
        self.__frag_size = frag_size

        self.__alive = Status.ALIVE
        self.__connecting = False
        self.__connected = False
        self.__owner = addr

        self.__resend_time = None
        self.__last_time = time.time()
        self.__keep_alive = Time.KEEPALIVE
        self.__last_transfer = Flags.SR - 1

        self.__transfers: dict[int, Sender | Receiver] = {}
        self.__packets: list[Packet] = []

    @property
    def last_time(self) -> float:
        return self.__last_time

    @property
    def alive(self) -> Status:
        return self.__alive

    @property
    def connected(self) -> bool:
        return self.__connected

    @property
    def frag_size(self) -> int:
        return self.__frag_size

    def get_addr(self) -> AddressInfo:
        return self.__owner

    def vadilate_packet(self, data: bytes) -> None:
        """Check if packet is valid and add it to the list"""

        if not Packet.is_valid(data):
            LOGGER.warning(f"Invalid packet from {self.__owner}")
            return

        # LOGGER.info(f"Received packet from {self.__owner}")

        packet = Packet.deconstruct(data)
        if packet is None:
            return

        self.__packets.append(packet)
        self.__last_time = time.time()
        self.__resend_time = time.time()

    def time_is_valid(self) -> bool:
        """Check if connection is still alive"""

        if time.time() - self.__last_time > self.__keep_alive:
            # LOGGER.warning(f"Connection with {self.__owner} is almost dead")
            return False

        return True

    def connect(self):
        """Connect to host"""

        syn = Packet.construct(data=b"", flags=Flags.SYN, seq_num=0)
        self.__connecting = True

        self.__send_func(syn, self.__owner)

    def disconnect(self):
        """Disconnect from host"""

        for transfer in self.__transfers.values():
            transfer.kill()

        self.__connected = False
        self.__connecting = False
        self.__alive = Status.DEAD

        """ Build fin packet """
        fin = Packet.construct(data=b"", flags=Flags.FIN, seq_num=3)
        self.__send_func(fin, self.__owner)

    def send_file(self, data: bytes, name: str, ext: str) -> None:
        """Send file to host"""

        """ Get last transfer """
        if self.__last_transfer + 1 >= Flags.WM:
            LOGGER.warning(f"Too many transfers from {self.__owner}")
            return

        """ Update last transfer"""
        transfer_flag = self.__last_transfer + 1
        self.__last_transfer = transfer_flag

        """ Create transfer """
        transfer = Sender(
            self.__send_func,
            self.__owner,
            type="file",
            name=name,
            extention=ext,
            transfer_flag=transfer_flag,
            fragment_size=self.frag_size,
        )
        transfer.prepare_data(data, transfer_flag)

        """ Add transfer to the list """
        self._add_transfer(transfer, transfer_flag)

        """ Add iterator to the list """
        self._add_iterator(transfer._iterator)

        """ Send init packet with file name, extension and transfer flag number """
        init_packet = Packet.construct(
            data=f"{name}{ext}:{transfer_flag}".encode(), flags=Flags.FILE, seq_num=0
        )
        self.__send_func(init_packet, self.__owner)

    def send_msg(self, message: bytes) -> None:
        """Send message to host"""

        """ Get last transfer """
        if self.__last_transfer + 1 >= Flags.WM:
            LOGGER.warning(f"Too many transfers from {self.__owner}")
            return

        """ Update last transfer"""
        transfer_flag = self.__last_transfer + 1
        self.__last_transfer = transfer_flag

        """ Create transfer """
        transfer = Sender(
            self.__send_func,
            self.__owner,
            type="msg",
            transfer_flag=transfer_flag,
            fragment_size=self.frag_size,
        )
        transfer.prepare_data(message, transfer_flag)

        """ Add transfer to the list """
        self._add_transfer(transfer, transfer_flag)

        """ Add iterator to the list """
        self._add_iterator(transfer._iterator)

        """ Send init packet with transfer flag number """
        init_packet = Packet.construct(
            data=f"{transfer_flag}".encode(), flags=Flags.MSG, seq_num=0
        )
        self.__send_func(init_packet, self.__owner)

    def _add_transfer(self, transfer: Sender | Receiver, transfer_flag: int) -> None:
        """Add transfer to the dict"""

        self.__transfers[transfer_flag] = transfer

    def _check_for_avaliable_transfer(self) -> bool:
        """Check if there connection can have more transfers"""

        if self.__last_transfer + 1 >= Flags.WM:
            LOGGER.warning(f"Too many transfers from {self.__owner}")
            return False

        return True

    def _keep_alive(self) -> bool:
        """Keep connection alive"""

        if self.__resend_time is None:
            self.__resend_time = time.time()

        def can_i_do_smth() -> bool:
            if time.time() - self.__resend_time > Time.RESEND:
                return False
            return True

        if self.__alive == Status.DEAD:
            return False

        if self.__connecting:
            if not can_i_do_smth():
                self.__connecting = False

            if Time.CONN_RESEND < time.time() - self.__resend_time:
                """Resend syn"""
                LOGGER.info(f"Resending syn to {self.__owner}")
                self.connect()
                self.__last_time = time.time()
                return True

        if not can_i_do_smth() and self.__connected:
            if not self.time_is_valid():
                self.__alive = Status.DEAD
                return False

            """Resend (syn | sack) - Keep alive"""
            sack = Packet.construct(data=b"", flags=(Flags.SYN | Flags.SACK), seq_num=2)
            self.__send_func(sack, self.__owner)
            self.__last_time = time.time()
            self.__resend_time = time.time()

        return True

    def _iterator(self):
        """Analyze packets"""

        if not self._keep_alive():
            return Status.FINISHED

        """ Check for dead transfers """
        for transfer_flag, transfer in self.__transfers.copy().items():
            if transfer.alive == Status.DEAD:
                self.__transfers.pop(transfer_flag)

        """ Go through all packets """
        for packet in self.__packets.copy():
            if packet.flags == Flags.SYN and not self.connected:
                """call syn function"""
                self._syn(packet)

            elif packet.flags == Flags.SYN and self.connected:
                """call syn sack function"""
                self._syn_sack(packet)

            elif packet.flags == (Flags.SYN | Flags.ACK) and (
                self.__connecting or self.connected
            ):
                """call syn ack function"""
                self._syn_ack(packet)

            elif packet.flags == (Flags.SYN | Flags.SACK) and (
                self.__connecting or self.connected
            ):
                """call syn sack function"""
                self._syn_sack(packet)

            elif not self.connected:
                """call fin function"""
                self.disconnect()
                LOGGER.warning(
                    f"Not connected, can not recv that packet from {self.__owner}"
                )
                self.__packets.remove(packet)

            elif packet.flags == Flags.FIN and packet.data == b"":
                """call fin function"""
                self.disconnect()
                LOGGER.info(f"Disconnected from {self.__owner}")
                self.__packets.remove(packet)

            elif packet.flags == Flags.FILE:
                """Create transfer"""

                """ Check transfer overloading """
                if not self._check_for_avaliable_transfer():
                    self.__packets.remove(packet)
                    continue

                data = packet.data.decode().split(":")

                if len(data) != 2:
                    LOGGER.warning(
                        f"Received file init from {self.__owner} with invalid data"
                    )
                    self.__packets.remove(packet)
                    continue

                name_ext, flag = data[0], int(data[1])
                try:
                    name, ext = name_ext.split(".")
                except ValueError:
                    name, ext = name_ext, ""

                transfer = Receiver(
                    self.__send_func, self.__owner, name, ext, flag, self.frag_size
                )
                self._add_transfer(transfer, flag)

                """ Add iterator to the list """
                self._add_iterator(transfer._iterator)

                """ call transfer function """
                transfer.receive(packet)

                """ Delete that packet """
                self.__packets.remove(packet)

            elif packet.flags == Flags.MSG:
                """Create transfer"""

                """ Check transfer overloading """
                if not self._check_for_avaliable_transfer():
                    self.__packets.remove(packet)
                    continue

                data = packet.data.decode()

                if not data.isdigit():
                    LOGGER.warning(
                        f"Received msg from {self.__owner} with invalid data"
                    )
                    self.__packets.remove(packet)
                    continue

                flag = int(data)

                transfer = Receiver(
                    self.__send_func,
                    self.__owner,
                    transfer_flag=flag,
                    fragment_size=self.frag_size,
                )
                self._add_transfer(transfer, flag)

                """ Add iterator to the list """
                self._add_iterator(transfer._iterator)

                """ call transfer function """
                transfer.receive(packet)

                """ Delete that packet """
                self.__packets.remove(packet)

            elif packet.flags >= Flags.SR and packet.flags < Flags.WM:
                """Handle transfer"""

                transfer_flag = packet.flags
                if transfer_flag in self.__transfers:
                    """call transfer function"""
                    self.__transfers[transfer_flag].receive_data(packet)
                    self.__packets.remove(packet)
                else:
                    LOGGER.warning(
                        f"Received packet from {self.__owner} with unknown transfer_flag"
                    )
                    self.__packets.remove(packet)

            elif (
                packet.flags == Flags.ACK
                or packet.flags == Flags.SACK
                or packet.flags == Flags.FIN
            ):
                transfer_flag = packet.data.decode().split(":")

                if len(transfer_flag) != 1:
                    LOGGER.warning(
                        f"Received packet from {self.__owner} with invalid data"
                    )
                    self.__packets.remove(packet)
                    continue

                transfer_flag = transfer_flag[0]

                if transfer_flag.isdigit():
                    transfer_flag = int(transfer_flag)
                    if transfer_flag in self.__transfers:
                        """call ack function"""
                        self.__transfers[transfer_flag].receive(packet)
                        self.__packets.remove(packet)
                    else:
                        LOGGER.warning(
                            f"Received pack from {self.__owner} with unknown transfer_flag"
                        )
                        self.__packets.remove(packet)
                else:
                    LOGGER.warning(
                        f"Received pack from {self.__owner} with invalid transfer_flag"
                    )
                    self.__packets.remove(packet)

            else:
                """call unknown function"""
                LOGGER.info(f"{packet.flags} is/are unknown")
                LOGGER.warning(f"Unknown packet from {self.__owner}")
                self.__packets.remove(packet)

        return Status.SLEEPING

    def _syn(self, packet: Packet):
        """Syn function"""

        # LOGGER.info(f"Received syn from {self.__owner}")

        """ Delete that packet """
        self.__packets.remove(packet)

        """ Check ttl of a packet """
        if not packet.time_is_valid():
            LOGGER.warning(f"Packet from {self.__owner} is dead")
            return

        """ Send syn ack """
        syn_ack = Packet.construct(data=b"", flags=Flags.SYN | Flags.ACK, seq_num=1)

        self.__send_func(syn_ack, self.__owner)

        """ Approve connection """
        self.__connecting = True

    def _syn_ack(self, packet: Packet):
        """Syn ack function"""

        # LOGGER.info(f"Received syn ack from {self.__owner}")

        """ Delete that packet """
        self.__packets.remove(packet)

        """ Check ttl of a packet """
        if not packet.time_is_valid():
            LOGGER.warning(f"Packet from {self.__owner} is dead")
            return

        """ Send syn sack """
        ack = Packet.construct(data=b"", flags=Flags.SYN | Flags.SACK, seq_num=2)

        self.__send_func(ack, self.__owner)

        """ Approved connection """
        self.__connected = True
        self.__connecting = False

        LOGGER.info(f"Connected to {self.__owner}")

    def _syn_sack(self, packet: Packet):
        """Syn sack function"""

        # LOGGER.info(f"Received syn sack from {self.__owner}")

        """ Delete that packet """
        self.__packets.remove(packet)

        """ Check ttl of a packet """
        if not packet.time_is_valid():
            LOGGER.warning(f"Packet from {self.__owner} is dead")
            return

        if self.connected:
            """Keep alive"""
            self.__last_time = time.time()
            LOGGER.info(f"Got keep alive from {self.__owner}")
            return

        """ Approved connection """
        self.__connected = True
        self.__connecting = False
        LOGGER.info(f"Connected to {self.__owner}")

    def __hash__(self) -> int:
        return hash((self.__owner, self.__connected))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ConnectionWith):
            return (
                self.__owner == other.__owner and self.__connected == other.__connected
            )
        return False

    def __repr__(self) -> str:
        return f"ConnectionWith({self.__owner}, {self.__connected})"

    def __str__(self) -> str:
        return f"ConnectionWith({self.__owner}, {self.__connected})"
