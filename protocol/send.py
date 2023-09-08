import time
import logging

from go.size import Size
from go.time import Time
from packet import Packet
from go.flags import Flags
from typing import Callable
from go.status import Status
from go.adressinfo import AddressInfo


''' Global variables '''
LOGGER = logging.getLogger("Sender")


class Sender:
    ''' 
        Sender class which will send messages and files.
        Devide data into packets if needed.
        Handle sequence numbers.
        Have buffer for packets.
    '''
    def __init__(self, send_func: Callable, addr: AddressInfo, type:str = "file", name: str = None, extention: str = None, transfer_flag: int = None):
        self.__seq_num = 1
        self.__type = type
        self.__name = name
        self.__client = addr
        self.__ext = extention
        self.__send_func = send_func
        self.__own_transfer_flag = transfer_flag

        self.__window_size = Size.WINDOW_SIZE
        self.__started = False

        self.__acks: set[int] = set()
        self.__all_packets: list[Packet] = []
        self.__sent_packets: list[Packet] = []

        self.__count_of_acks = 0
        self.__count_of_packets = 0

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
    def client(self) -> AddressInfo:
        return self.__client

    def prepare_data(self, data: bytes, flags: Flags) -> None:
        ''' Prepare data for sending '''
        
        packets = Packet.devide(data, self.__seq_num + 1, fragment_size=Size.FRAGMENT_SIZE, flags=flags)

        # LOGGER.info(f"Sending {len(packets)} packets to {self.__client}")
        
        self.__all_packets.extend(packets)

        self.__count_of_packets = len(self.__all_packets)

        # LOGGER.info(f"len(self.__all_packets): {len(self.__all_packets)}")

    def receive(self, packet: Packet) -> None:
        ''' Receive ack '''

        if packet.flags == Flags.ACK:
            # LOGGER.info(f"Received ACK from {self.__client}")
            self.__last_time = time.time()
            self.__acks.add(packet.seq_num)
            self.__count_of_acks += 1
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
        ''' Check if connection is still alive '''
        
        if time.time() - self.__last_time > Time.KEEPALIVE:
            return False
        
        return True
    
    def kill(self) -> None:
        ''' Kill connection '''
        self.__alive = Status.DEAD
    
    def _start(self) -> bool:
        ''' Only for waiting SACK to start sending data '''
        if not self.__started and not self.time_is_valid():
            LOGGER.info(f"Resending FILE/MSG to {self.__client}")
            if self.__type == "file":
                self.__send_func(Packet.construct(f"{self.name}.{self.ext}:{self.own_transfer_flag}".encode(), Flags.FILE, 0), self.__client)
            else:
                self.__send_func(Packet.construct(f"{self.own_transfer_flag}".encode(), Flags.MSG, 0), self.__client)
            return False
        if self.__started:
            return True

    def _send_restof_data(self, num_to_skip: int) -> None:
        ''' Send rest of data '''

        packets_to_send = []

        while self.__all_packets and len(packets_to_send) < self.__window_size - num_to_skip:
            packet = self.__all_packets.pop(0)
            packets_to_send.append(packet)
            self.__sent_packets.append(packet)
        
        for packet in packets_to_send:
            packet = Packet.packet_to_bytes(packet)
            self.__send_func(packet, self.__client)

        ''' Update sequence number '''
        # LOGGER.info(f"seq_num: {self.__seq_num}")
        self.__seq_num = (self.__seq_num + len(packets_to_send)) % (2 ** 32) # HACK: 32 bits
        # LOGGER.info(f"new seq_num: {self.__seq_num}")

        if self.__count_of_acks >= self.__count_of_packets:
            ''' Send FIN '''
            self.__seq_num += 1
            LOGGER.info(f"sending fin, seq: {self.__seq_num}")
            self.__send_func(Packet.construct(data = f"{self.own_transfer_flag}".encode(), flags = Flags.FIN, seq_num = self.__seq_num), self.__client)
            self.extended -= 1
            if self.extended == 0:
                self.__alive = Status.DEAD
    
    def _iterator(self):
        ''' Handle packets '''
        if self.__alive == Status.DEAD:
            return Status.FINISHED
        
        ''' Check if we can start '''
        if not self._start():
            LOGGER.info(f"Waiting for SACK from {self.__client}")
            return Status.SLEEPING
        
        if not self.time_is_valid():
            LOGGER.info(f"Transfer is not alive anymore")
            self.__alive = Status.DEAD
            return Status.FINISHED

        ''' Check for acknowledgments and remove acked packets from sent_packets'''
        self.__sent_packets = [packet for packet in self.__sent_packets if packet.seq_num not in self.__acks]

        count = len(self.__sent_packets)

        ''' Resend packets if needed '''
        for packet in self.__sent_packets:
            packet = Packet.packet_to_bytes(packet)
            self.__send_func(packet, self.__client)

        ''' Send rest of data '''
        self._send_restof_data(count)

        return Status.RUNNING