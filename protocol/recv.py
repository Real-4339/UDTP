import time
import logging

from go.time import Time
from go.size import Size
from packet import Packet
from go.flags import Flags
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
    def __init__(self, send_func: Callable, addr: AddressInfo, name: str = None, extention: str = None, own_transfer_flag: Flags = None):
        self.__name = name
        self.__client = addr
        self.__ext = extention
        self.__send_func = send_func
        self.__own_transfer_flag = own_transfer_flag
        
        self.__acks: set[int] = set()
        self.__packets: list[Packet] = []
        self.__processed: set[int] = set()
        
        self.__alive = Status.ALIVE
        self.__last_time = time.time()


    @property
    def name (self) -> str:
        return self.__name
    
    @property
    def ext(self) -> str:
        return self.__ext
    
    @property
    def own_transfer_flag(self) -> Flags:
        return self.__own_transfer_flag
    
    @property
    def client(self) -> AddressInfo:
        return self.__client
    
    def get_packets(self) -> list[Packet]:
        ''' Get packets '''
        
        return self.__packets

    def time_is_valid(self) -> bool:
        ''' Check if receiver is still alive '''
        
        if time.time() - self.__last_time > Time.TTL:
            return False
        
        return True

    def receive(self, packet: Packet) -> None:
        ''' Receive FILE, MSG, FIN '''

        if packet.flags == Flags.FILE:
            self._process_file(packet)
            
        elif packet.flags == Flags.MSG:
            return

        elif packet.flags == Flags.FIN:
            self._process_fin(packet)

    def receive_data(self, packet: Packet) -> None:
        ''' Receive data '''

        if not packet.is_valid():
            return

        if packet.seq_num not in self.__processed:
            self.__acks.add(packet.seq_num)
            self.__packets.append(packet)
            self.__processed.add(packet.seq_num)

            self.__last_time = time.time()

        else:
            ''' Resend ack '''
            ack = Packet.construct(data=b"", flags=Flags.ACK, seq_num=packet.seq_num)

    def kill(self) -> None:
        ''' Kill receiver '''

        self.__alive = Status.DEAD

    def _process_file(self, packet: Packet) -> None:
        ''' Process file '''

        data = packet.data.decode().split(":")
        
        name_ext, flag = data[0], int(data[1])
        name, ext = name_ext.split(".")

        self.name = name
        self.ext = ext
        self.own_transfer_flag = flag

    def _process_fin(self, packet: Packet) -> None:
        ''' Process FIN '''

        self.__alive = Status.DEAD

        if self.name is not None and self.ext is not None:
            ''' Create file from packets and save it '''
            file_data = Packet.merge(self.__packets)
            file_name = f"{self.__name}_{int(time.time())}.{self.__ext}"

            try:
                with open(file_name, "wb") as f:
                    f.write(file_data)
                LOGGER.info(f"Received file from {self.__client}")
                LOGGER.info(f"File name: {self.__name}_{int(time.time())}.{self.__ext}")
                LOGGER.info(f"File size: {len(self.__packets) * Size.FRAGMENT_SIZE} bytes")
            except Exception as e:
                LOGGER.error(f"Failed to save file: {e}")

        else:
            ''' Create message from packets and print it '''
            message = Packet.merge(self.__packets).decode()
            LOGGER.info(f"Received message from {self.__client} : {message}")

    def _acknowledge_data(self) -> None:
        ''' Acknowledge data '''
        
        if len(self.__acks) == 0:
            return
        
        for seq_num in self.__acks:
            ack = Packet.construct(data=b"", flags=Flags.ACK, seq_num=seq_num)
            self.__send_func(ack, self.__client)

        self.__acks.clear()
    
    def _iterate(self) -> Status:
        ''' Iterate over packets '''

        if self.__alive == Status.DEAD:
            return Status.FINISHED
        
        self._acknowledge_data()

        return Status.SLEEPING