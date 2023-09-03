import time
import logging

from go.time import Time
from packet import Packet
from typing import Callable
from go.status import Status
from go.adressinfo import AddressInfo


''' Global variables '''
LOGGER = logging.getLogger("Receiver")


class Receiver:
    ''' 
        Receiver class which will receive messages and files.
        Devide data into packets if needed.
        Handle sequence numbers.
        Have buffer for packets.
    '''
    def __init__(self, send_func: Callable, addr: AddressInfo):
        self.__addr = addr
        self.__seq_num = 0    
        self.__window_size = 16        
        self.__alive = Status.ALIVE
        self.__send_func = send_func
        self.__last_time = time.time()
        self.__buffer: list[bytes] = []
        self.__packets: list[Packet] = []
        
    @property
    def alive(self) -> Status:
        return self.__alive

    def send(self, data: bytes) -> None:
        ''' Send data '''
        
        packets = Packet.devide(data, self.__seq_num)
        
        if packets is None:
            LOGGER.error("Failed to devide data")
            return
        
        for packet in packets:
            self.__send_func(packet)
        
        self.__seq_num += len(packets)

    def receive(self, data: bytes) -> None:
        ''' Receive data '''
        
        if not Packet.is_valid(data):
            LOGGER.warning(f"Invalid packet from {self.__addr}")
            return
        
        LOGGER.info(f"Received packet from {self.__addr}")

        packet = Packet.deconstruct(data)
        
        if packet is None:
            LOGGER.warning(f"Failed to deconstruct packet from {self.__addr}")
            return

        self.__packets.append(packet)
        self.__last_time = time.time()

    def get_packets(self) -> list[Packet]:
        ''' Get packets '''
        
        return self.__packets

    def pop_packets(self) -> list[Packet]:
        ''' Pop packets '''
        
        packets = self.__packets
        self.__packets = []
        return packets

    def time_is_valid(self) -> bool:
        ''' Check if receiver is still alive '''
        
        if time.time() - self.__last_time > Time.TTL:
            return False
        
        return True
    
    def _iterate(self):
        ''' Iterate through packets '''
        
        for packet in self.__packets:
            if packet.seq_num == self.__seq_num:
                self.__seq_num += 1
                yield packet.data
            else:
                break