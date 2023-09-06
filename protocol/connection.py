import time
import logging

from go.time import Time
from packet import Packet
from go.flags import Flags
from typing import Callable
from go.status import Status
from go.adressinfo import AddressInfo


''' Global variables '''
LOGGER = logging.getLogger("Connection")


class ConnectionWith:
    def __init__(self, addr: AddressInfo, send_func: Callable):
        self._add_iterator = NotImplemented
        self.__keep_alive = Time.KEEPALIVE
        self.__packets: list[Packet] = []
        self.__last_time = time.time()
        self.__send_func = send_func
        self.__alive = Status.ALIVE
        self.__connecting = False
        self.__connected = False
        self.__owner = addr
    
    @property
    def last_time(self) -> float:
        return self.__last_time
    
    @property
    def alive(self) -> Status:
        return self.__alive
    
    @property
    def connected(self) -> bool:
        return self.__connected

    def get_addr(self) -> AddressInfo:
        return self.__owner

    def vadilate_packet(self, data: bytes) -> None:
        ''' Check if packet is valid and add it to the list '''
        
        if not Packet.is_valid(data):
            LOGGER.warning(f"Invalid packet from {self.__owner}")
            return
    
        LOGGER.info(f"Received packet from {self.__owner}")

        packet = Packet.deconstruct(data)
    
        if packet is None:
            LOGGER.warning(f"Failed to deconstruct packet from {self.__owner}")
            return

        self.__packets.append(packet)
        self.__last_time = time.time()

    def time_is_valid(self) -> bool:
        ''' Check if connection is still alive '''
        
        if time.time() - self.__last_time > self.__keep_alive:
            LOGGER.warning(f"Connection with {self.__owner} is dead")
            return False
        
        return True
    
    def connect(self):
        ''' Connect to host '''
        
        syn = Packet.construct(data = b"", flags = Flags.SYN)
        self.__connecting = True

        if syn is None:
            LOGGER.warning(f"Failed to construct syn to {self.__owner}")
            return

        self.__send_func(syn, self.__owner)

    def disconnect(self):
        ''' Disconnect from host '''
        
        self.__connected = False
        self.__connecting = False
        self.alive = Status.DEAD

    def _keep_alive(self) -> bool:
        ''' Keep connection alive '''
        
        if self.__alive == Status.DEAD:
            return False
        
        if self.__connecting and self.time_is_valid():
            ''' Resend syn '''
            self.connect()
            self.__last_time = time.time()
            return True
        
        if not self.time_is_valid():
            self.__alive = Status.DEAD
            return False

        if self.__connected:
            ''' Send syn | sack '''
            sack = Packet.construct(data = b"", flags = (Flags.SYN | Flags.SACK))

            self.__send_func(sack, self.__owner)
        
        return True

    def _iterator(self):
        ''' Analyze packets '''
        
        if not self._keep_alive():
            return Status.FINISHED
        
        for packet in self.__packets.copy():

            if packet.flags == Flags.SYN and not self.connected:
                ''' call syn function '''
                self._syn(packet)
            
            elif (
                packet.flags == (Flags.SYN | Flags.ACK) and
                self.__connecting or self.connected
            ):
                ''' call syn ack function '''
                self._syn_ack(packet)

            elif (
                packet.flags == (Flags.SYN | Flags.SACK) and 
                self.__connecting or self.connected
            ):
                ''' call syn sack function '''
                self._syn_sack(packet)

            else: 
                ''' call unknown function '''
                LOGGER.warning(f"Unknown packet from {self.__owner}")
                self.__packets.remove(packet)

        return Status.SLEEPING
    
    def _syn(self, packet: Packet):
        ''' Syn function '''
        
        LOGGER.info(f"Received syn from {self.__owner}")
        
        ''' Check ttl of a packet '''
        if not packet.time_is_valid():
            LOGGER.warning(f"Packet from {self.__owner} is dead")
            return
        
        ''' Send syn ack '''
        syn_ack = Packet.construct(data = b"", flags = Flags.SYN | Flags.ACK)

        if syn_ack is None:
            LOGGER.warning(f"Failed to construct syn ack to {self.__owner}")
            return

        self.__send_func(syn_ack, self.__owner)

        ''' Approve connection '''
        self.__connecting = True

        ''' Delete that packet '''
        self.__packets.remove(packet)

    def _syn_ack(self, packet: Packet):
        ''' Syn ack function '''
        
        LOGGER.info(f"Received syn ack from {self.__owner}")
        
        ''' Check ttl of a packet '''
        if not packet.time_is_valid():
            LOGGER.warning(f"Packet from {self.__owner} is dead")
            return
        
        ''' Send syn sack '''
        ack = Packet.construct(data = b"", flags = Flags.SYN | Flags.SACK)

        self.__send_func(ack, self.__owner)

        ''' Approved connection '''
        self.__connected = True
        self.__connecting = False

        ''' Delete that packet '''
        self.__packets.remove(packet)

        LOGGER.info(f"Connected to {self.__owner}")

    def _syn_sack(self, packet: Packet):
        ''' Syn sack function '''
        
        LOGGER.info(f"Received syn sack from {self.__owner}")
        
        ''' Check ttl of a packet '''
        if not packet.time_is_valid():
            LOGGER.warning(f"Packet from {self.__owner} is dead")
            return
        
        ''' Approved connection '''
        self.__connected = True
        self.__connecting = False
        LOGGER.info(f"Connected to {self.__owner}")

        ''' Delete that packet '''
        self.__packets.remove(packet)

    def __hash__(self) -> int:
        return hash((self.__owner, self.__connected))
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, ConnectionWith):
            return (
                self.__owner == other.__owner and
                self.__connected == other.__connected
            )
        return False
    
    def __repr__(self) -> str:
        return f"ConnectionWith({self.__owner}, {self.__connected})"
    
    def __str__(self) -> str:
        return f"ConnectionWith({self.__owner}, {self.__connected})"