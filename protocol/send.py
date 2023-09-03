import time
import logging

from go.size import Size
from go.time import Time
from packet import Packet
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
    def __init__(self, send_func: Callable, addr: AddressInfo):
        self.__addr = addr
        self.__send_func = send_func
        self.__seq_num = 0
        self.__window_size = Size.WINDOW_SIZE
        self.__packets: list[Packet] = []

        self.__acks: list[Packet] = []
        self.__sent_packets: list[Packet] = []
        
        self.__last_time = time.time()
        self.__alive = Status.ALIVE

    def send_data(self, data: bytes) -> None:
        ''' Send data '''
        
        packets = Packet.devide(data, self.__seq_num, packet_size=Size.FRAGMENT_SIZE)
        
        self.__packets.extend(packets)

    def send_restof_data(self) -> None:
        ''' Send rest of data '''
        
        while self.__packets and self.__packets[0].seq_num - self.__seq_num < self.__window_size:
            packet = self.__packets.pop(0)
            packet = Packet.construct(packet.data, packet.flags, packet.seq_num)

            self.__send_func(packet)    

        # Update the sequence number after sending part of the data
        self.__seq_num += self.__window_size

    def receive_ack(self, data: bytes) -> None:
        ''' Receive ack '''
        
        if not Packet.is_valid(data):
            LOGGER.warning(f"Invalid packet from {self.__addr}")
            return
        
        LOGGER.info(f"Received packet from {self.__addr}")

        packet = Packet.deconstruct(data)
        
        if packet is None:
            LOGGER.warning(f"Failed to deconstruct packet from {self.__addr}")
            return

        if packet.flags == Flags.ACK:
            self.__alive = Status.ALIVE
            self.__last_time = time.time()
            return

        if packet.flags == Flags.NACK:
            self.__alive = Status.ALIVE
            self.__last_time = time.time()
            self.__seq_num = packet.seq_num
            return

        LOGGER.warning(f"Unexpected flags from {self.__addr}")

    def time_is_valid(self) -> bool:
        ''' Check if connection is still alive '''
        
        if time.time() - self.__last_time > Time.KEEPALIVE:
            LOGGER.warning(f"Connection with {self.__addr} is dead")
            return False
        
        return True
    
    def _iterator(self):
        ''' Handle packets '''