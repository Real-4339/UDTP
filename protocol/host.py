import socket
import logging
import threading

from typing import Callable
from go.status import Status
from connection import ConnectionWith
from go.adressinfo import AddressInfo
from selectors import DefaultSelector, EVENT_READ


''' Global variables '''
LOGGER = logging.getLogger("Host")


class Host:
    def __init__(self, ip: str, port: int):
        self.__connections: list[ConnectionWith] = []
        self.__connections_lock = threading.Lock()
        self.__iterators: list[Callable] = []
        self.__selector = DefaultSelector()
        self.__me = AddressInfo(ip, port)
        self.__socket = NotImplemented
        self.__binded = False

    @property
    def me(self) -> AddressInfo:
        return self.__me

    def get_connection(self, addr: AddressInfo) -> ConnectionWith | None:
        ''' Get connection '''
        
        with self.__connections_lock:
            for connection in self.__connections:
                if connection.get_addr() == addr:
                    return connection
        return None
    
    def list_connections(self) -> None:
        ''' List all connections '''
        
        with self.__connections_lock:
            for connection in self.__connections:
                print(connection)

    def validate_addr(self, ip: str, port: int) -> bool:
        ''' Check if address is valid '''
        
        ''' Except spoofed packets '''
        if ip == self.__me.ip and port == self.__me.port:
            return False
        
        ''' check ip with socket.inet_aton and port with range '''
        try:
            socket.inet_aton(ip)
            if port < 49152 or port > 65535:
                return False
        except socket.error:
            return False
        
        return True

    def connect(self, ip: str, port: int):
        ''' Connect to host '''
        
        addr = AddressInfo(ip, port)
        connection = self.get_connection(addr)
        
        if connection is None:
            connection = ConnectionWith(addr, self._send)

            with self.__connections_lock:
                self.__connections.append(connection)
            self._add_iterator(connection._iterator)

            connection._add_iterator = self._add_iterator

            connection.connect()
        else:
            LOGGER.warning('Connection to {}:{} already exists'.format(ip, port))

    def disconnect(self, ip: str, port: int):
        ''' Disconnect from host '''
        
        addr = AddressInfo(ip, port)
        connection = self.get_connection(addr)
        
        if connection is not None:
            connection.disconnect()
        else:
            LOGGER.warning('Connection to {}:{} does not exist'.format(ip, port))

    def disconnect_all(self):
        ''' Disconnect from all hosts '''
        
        with self.__connections_lock:
            for connection in self.__connections:
                connection.disconnect()

        LOGGER.info('Disconnected from all hosts')

    def _send(self, data: bytes, addr: AddressInfo):
        ''' Send data to addr '''
        
        self.__socket.sendto(data, addr.values())

    def _add_iterator(self, iterator: Callable):
        self.__iterators.append(iterator)

    def _iterator(self):
        ''' Get packets '''
        
        for key, _ in self.__selector.select(timeout=0.1):
            data, addr = self.__socket.recvfrom(1472)
            
            ''' Ignore spoofed packets '''
            if addr[0] == self.__me.ip:
                continue

            ''' Check if connection already exists '''
            
            connected_with = self.get_connection(AddressInfo(*addr))
            
            if connected_with is None:
                
                LOGGER.info(f"New connection with {addr}")
                connected_with = ConnectionWith(AddressInfo(*addr), self._send)

                with self.__connections_lock:
                    self.__connections.append(connected_with)

                connected_with._add_iterator = self._add_iterator

                self._add_iterator(connected_with._iterator)
                    
            connected_with.vadilate_packet(data)
            
            return Status.RUNNING # BUG: processes only one packet per iteration
        return Status.SLEEPING # HACK

    def _v4(self):
        ''' Run all iterators and check results '''
        
        for iterator in self.__iterators.copy():
            result = iterator()
            if result is Status.FINISHED:
                self.__iterators.remove(iterator)
            elif result is Status.RUNNING or Status.SLEEPING:
                continue

    def _endless_loop(self):
        i = 0
        while self.__binded:
            if i == 2:
                self.del_dead_connections()
                i = 0 
            self._v4()
            i += 1

    def del_dead_connections(self):
        ''' Delete dead connections '''
        
        with self.__connections_lock:
            for connection in self.__connections.copy():
                if connection.alive is Status.DEAD:
                    self.__connections.remove(connection)

    def register(self):
        ''' Bind socket '''
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__socket.bind(self.__me.values())
        self.__socket.setblocking(False)

        self.__connections = []
        self.__iterators = []

        self._add_iterator(self._iterator)
        self.__selector.register(self.__socket, EVENT_READ)

        self.__binded = True

        LOGGER.info('Host registered')

    def unregister(self):
        ''' Unbind socket '''
        self.__binded = False
        self.__selector.unregister(self.__socket)
        self.__socket.close()

        LOGGER.info('Host unregistered')
    
    def run(self):
        self._endless_loop()