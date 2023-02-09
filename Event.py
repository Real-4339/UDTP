import asyncio
import time

class Event:
    """Event class for handling events,
    such as connection, disconnection, sending and receiving packets full of data.
    :param who: tuple of ip and port of the client
    :param function: function that will be called when event is triggered
    :param timeout: timeout for the event
    :param socket: socket that will be used for sending and receiving packets
    :param packet: first packet we starting with
    :param id: id of the event
    """
    def __init__(self, who: tuple, function, timeout: str, socket, packet, id) -> None:
        self.loop = asyncio.get_event_loop()
        self.__who = who
        self.__timeout = timeout
        self.__socket = socket
        self.__packet = packet
        self.__id = id
        self.__function = function
        self.__call__()
    
    @property
    def who(self) -> tuple:
        return self.__who
    
    @property
    def id(self) -> int:
        return self.__id
    
    @property
    def function(self):
        return self.__function

    def connection(self):
        #self.loop.create_task(self.function(self.__packet))
        return self.loop.run_until_complete(self.__async__new_connection())
    
    async def __async__new_connection(self):
        ...

    def __call__(self):
        if self.__function == 'connection':
            self.connection()
    
    
    async def __repr__(self) -> str:
        return f"Event(who = {self.who}, function = {self.function}, timeout = {self.__timeout}, what_socket = {self.__socket}, packet = {self.__packet}, id = {self.__id})"

    


    