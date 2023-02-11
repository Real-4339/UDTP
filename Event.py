import asyncio
import time
from Packet import Flags, Packet

class Event:
    """Event class for handling events,
    such as connection, disconnection, sending and receiving packets full of data.
    :param who: tuple of ip and port of the client
    :param function: function that will be called when event is triggered
    :param timeout: timeout for the event
    :param socket: socket that will be used for sending and receiving packets
    :param packet: first packet we starting with
    :param id: id of the event
    :initiator: who initiated connection, client or server, default is None, client - not me, server - me
    """
    def __init__(self, who: tuple, function, timeout: str, socket, packet) -> None:
        self.loop = asyncio.get_event_loop()
        self.__who = who
        self.__msg = None
        self.__payload = None
        self.__window_size = None
        self.__initiator = None
        self.__timeout = timeout
        self.__socket = socket
        self.__packet = packet
        self.__function = function
        self.__result = None
        self.__array_of_packets = []
        self.__Roman = self.__call__()
    
    @property
    def who(self) -> tuple:
        return self.__who
    
    @property
    def initiator(self) -> int:
        return self.__initiator
    
    @property
    def function(self):
        return self.__function

    @property
    def result(self):
        return self.__result

    @property
    def payload(self):
        return self.__payload

    @property
    def window_size(self):
        return self.__window_size

    @property
    def Roman(self):
        return self.__Roman

    def connection(self):
        #self.loop.create_task(self.function(self.__packet))
        return self.loop.run_until_complete(self.__async__new_connection())
    
    async def __async__new_connection(self):
        # Setting up timer 
        start = time.time()
        tick = 0.1
        stages = ['syn', 'syn_ack', 'sack']
        end_time = int(start) + int(self.__timeout)
        # Decide who is initiator
        if self.__who == self.__packet.address_to:
            self.__initiator = "server"
        else:
            self.__initiator = "client"
        # Start 3-way handshake
        if self.__initiator == "server":
            # Send SYN
            self.loop.sock_sendto(self.__socket, self.__packet.create_packet(), self.__packet.address_to)
            # Me sending him my payload
            self.__payload = int(self.__packet.data.decode('utf-8'))
            # Wait for SYN | ACK
            while True:
                if int(time.time()) > end_time:
                    self.__result = False
                    self.loop.stop()
                    self.loop.close()
                    break
                # Get packet from array_of_packets
                if self.__array_of_packets:
                    packet = self.__array_of_packets.pop(0)
                    stages.pop(0)
                    if packet.flags == Flags(Flags.SYN | Flags.ACK):
                        # Get window size from packet
                        self.__window_size = packet.seq
                        # Send SACK
                        self.__packet = Packet.pack(data = b'Connection established', flags = Flags(Flags.SACK), seq = packet.seq, address_from = packet.address_to, address_to = packet.address_from)
                        self.loop.sock_sendto(self.__socket, self.__packet.create_packet(), self.__packet.address_to)
                        self.__result = True
                        self.loop.stop()
                        self.loop.close()
                        break
                else:
                    if stages[0] == 'syn' and int(time.time()) > start + tick:
                        tick += 0.1
                        self.loop.sock_sendto(self.__socket, self.__packet.create_packet(), self.__packet.address_to)

                
        else: # Client sends SYN
            # Answer with SYN | ACK
            self.__payload = int(self.__packet.data.decode('utf-8'))
            self.__window_size = self.__packet.seq
            self.__packet = Packet.pack(data = b'', flags = Flags(Flags.SYN | Flags.ACK), seq = self.__packet.seq, address_from = self.__packet.address_to, address_to = self.__packet.address_from)
            self.loop.sock_sendto(self.__socket, self.__packet.create_packet(), self.__packet.address_to)
            # Wait for SACK
            while True:
                if int(time.time()) > end_time:
                    self.__result = False
                    self.loop.stop()
                    self.loop.close()
                    break
                # Get packet from array_of_packets
                if self.__array_of_packets:
                    packet = self.__array_of_packets.pop(0)
                    if packet.flags == Flags(Flags.SACK):
                        self.__result = True
                        self.__msg = packet.data.decode('utf-8')
                        self.loop.stop()
                        self.loop.close()
                        break
                    else: # if he still sending SYN
                        self.loop.sock_sendto(self.__socket, self.__packet.create_packet(), self.__packet.address_to)
                else:
                    if int(time.time()) > start + tick:
                        tick += 0.1
                        self.loop.sock_sendto(self.__socket, self.__packet.create_packet(), self.__packet.address_to)

    # Function that will be called when packet is received and will be added to the event
    def add_packet(self, packet):
        self.__array_of_packets.append(packet)
        # if packet.flags == Flags(Flags.FIN | Flags.ACK):
        #     self.__result = True
        #     self.loop.stop()
        #     self.loop.close()


    async def __call__(self):
        if self.__function == 'connection':
            result = self.connection()
            return result

    async def __repr__(self) -> str:
        return self.__function

    


    