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
    def __init__(self, send_func: Callable, addr: AddressInfo, name: str, extention: str, own_transfer_flag: Flags):
        self.__seq_num = 1
        self.__client = addr
        self.__send_func = send_func
        self.__name = name
        self.__ext = extention
        self.__started = False
        self.__own_transfer_flag = own_transfer_flag

        self.__window_size = Size.WINDOW_SIZE
        
        self.__acks: set[int] = set()
        self.__all_packets: list[Packet] = []
        self.__sent_packets: list[Packet] = []
        
        self.__alive = Status.ALIVE
        self.__last_time = time.time()

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
        
        packets = Packet.devide(data, self.__seq_num, packet_size=Size.FRAGMENT_SIZE, flags=flags)
        
        self.__all_packets.extend(packets)

    def receive_ack(self, packet: Packet) -> None:
        ''' Receive ack '''

        if packet.flags & Flags.ACK:
            self.__last_time = time.time()
            self.__acks.add(packet.seq_num)
            return
        
        if packet.flags == Flags.FIN:
            LOGGER.info(f"Received FIN from {self.__client}")
            self.__alive = Status.FINISHED
            return
        
        if packet.flags == Flags.SACK:
            LOGGER.info(f"Starting sending data to {self.__client}")
            self.__started = True
            return

        LOGGER.warning(f"Unexpected flags from {self.__client}")

    def time_is_valid(self) -> bool:
        ''' Check if connection is still alive '''
        
        if time.time() - self.__last_time > Time.KEEPALIVE:
            LOGGER.warning(f"Connection with {self.client} is dead")
            return False
        
        return True
    
    def start(self) -> bool:
        ''' Only for waiting SACK to start sending data '''
        if not self.__started:
            self.__send_func(Packet.construct(f"{self.name}.{self.ext}".encode(), self.own_transfer_flag, 0), self.__client)

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
        self.__seq_num = (self.__seq_num + len(packets_to_send)) % (2 ** 32) # HACK: 32 bits
    
    def _iterator(self):
        ''' Handle packets '''
        if self.__alive == Status.DEAD:
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

        return Status.SLEEPING