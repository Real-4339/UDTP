# Made by Vadym Tilihuzov
# Date: 1.02.2023

"""
socket.recvfrom() returns a tuple (data, address)
socker.recv() returns data
Need to create an event class or idk events that will handle 3-way handshake with timer and two more events for sending and receiving data
TODO: im using my_socket, but i need to use asyncio socket
TODO: reassign all events
Maybe i should use database for storing clients and maybe events
"""

from sys import stdin, stdout
from Packet import Packet, Flags
from Event import Event
from collections import defaultdict
import socket
import asyncio
from aioconsole import ainput


def connected(socket) -> bool:  # TODO: recreate using my Packet class and Libuv
    try:
        socket.send(b'')
    except socket.error:
        return False
    return True

def existing_socket(socket) -> bool:
    try:
        socket.getsockname()
    except socket.error:
        return False
    return True

async def get_port() -> int:
    port = int(await ainput('Enter port: '))
    if port < 49152 or port > 65535:
        print('Error: port must be in range 49152 - 65535')
        return await get_port()
    return port

# Output not working well, behaviar
# async def ainput(string: str) -> str:
#     await asyncio.get_event_loop().run_in_executor(
#             None, lambda s=string: stdout.write(s+' '))
#     return await asyncio.get_event_loop().run_in_executor(
#             None, stdin.readline)


# Basic information
loop = asyncio.get_event_loop()
PORT = loop.run_until_complete(get_port())
IP = socket.gethostbyname("localhost")
clients = []
events: dict[tuple[int, int], list[Event]] = defaultdict(list)


# Creating socket
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.bind((IP, PORT))  # TODO: add ip handling
my_socket.setblocking(False)


# Console loop, use yeild
async def console():
    while True:
        cmd = await ainput('Enter command: ')
        if cmd == 'exit':
            yield False
        elif cmd == 'list':
            print(clients)
        elif cmd == 'help':
            print('Commands: list, exit, new connection')
        elif cmd == 'new connection' or cmd == '3':
            yield 'new_connection'
        else:
            print('Unknown command')

# Listener loop, use yeild
async def listener(my_payload = 1488):
    loop = asyncio.get_event_loop()
    while True:
        try:
            data, addr = await loop.sock_recvfrom(my_socket, my_payload)
            packet = Packet.unpack(data = data, address_to = (IP, PORT), address_from = addr)
            yield packet
            
        except:
            yield None

# Creating new connection
async def create_connection():
    print('Creating new connection')
    ip = await ainput('Enter ip: ')
    port = await ainput('Enter port: ')
    try:
        payload = await ainput('Enter payload, max is 1488, min is 1: ')
        if payload < 1 or payload > 1488:
            print('Error: payload must be in range 1 - 1488, im taking you back, you moron')
            raise ValueError
    except ValueError:
        return False
    packet = Packet.pack(data = payload.encode(), flags = Flags(65), seq = 256, address_to=(ip, port), address_from=(IP, PORT))
    return packet


# Console handler
async def console_handler(string: str):
    if string == "new_connection":
        packet = await create_connection()
        if packet == False:
            return None
        else:
            event = Event(who = packet.address_to, function = "connection", timeout = "10", what_socket = my_socket, packet = packet, id = len(events)+1)
            events[event.who].append(event)
            return 


# Listener handler
async def listener_handler(packet: Packet or None): # TODO: events !!!
    if packet == None:
        return None
    if packet.address not in clients:
        clients.append(packet.address)
        event = Event(who = packet.address, function = "connection", timeout = "10", what_socket = my_socket, packet = packet, id = len(events)+1)
        events[event.who].append(event)
        return event
    else:
        if events[packet.address] is []: # check what client wants
            return # i will handle this later
        
        if packet.flags & Flags(1) == Flags(1) or packet.flags == Flags(Flags.SACK): # event.connection
            if Event(_,"connection", _, _, _, _) in events[packet.address]:
                index = events[packet.address].index(Event(_,"connection", _, _, _, _))
                event = events[packet.address][index]
                event.add_packet(packet)
            return
        
        if packet.data == b'': # event.send_data (me sending data to client)
            return
        
        if packet.flags == Flags(0): # event.receive_data (client sending data to me)
            return # i will handle this later



# Main loop
async def V6(): # Not as fast as V8 and not as good, but it works
    print('Server started')
    main_loop = asyncio.get_event_loop()
    while True:
        task1 = main_loop.create_task(console())
        task2 = main_loop.create_task(listener())

        await task1
        await task2

        if task1.result() == False: # end of program, i need to send FIN packet to all clients, rebuild this
            task1.cancel(
                    my_socket.close()
            )
            task2.cancel()
            main_loop.stop()
            main_loop.close()
            break

        if task1.result(): # two events, one for handshake, second for sending data
            cons_handler = main_loop.create_task(console_handler(task1.result()))
            await cons_handler
            cons_handler.cancel()
        if task2.result(): # only one event, for receiving data
            list_handler = main_loop.create_task(listener_handler(task2.result()))
            await list_handler
            list_handler.cancel()


if __name__ == '__main__':
    asyncio.run(V6())


# if packet == None:
#         ...
#     else:
#         # 3-way handshake:
#         if packet.address in clients and (packet.flags == Flags(1)):
#             answer = Packet(data = b'Ty sho durak?', flags = Flags(Flags.ACK))
#             my_socket.sendto(answer.header + answer.data, packet.address)
#         else:
#             if packet.flags == (Flags.SYN | Flags.ACK): # if he doesnt hear me, i will send him again
#                 if clients.count(packet.address) > 1:
#                     answer = Packet(data = b'', flags = Flags(Flags.SYN | Flags.ACK), seq = packet.seq)
#                     my_socket.sendto(packet.header + packet.data, packet.address)
#                     return
#                 else:
#                     answer = Packet(data = b'', flags = Flags(Flags.ACK), seq = packet.seq)
#                     my_socket.sendto(answer.header + answer.data, packet.address)
#                     return
        
#             if packet.flags & Flags.SYN == Flags.SYN: # first handshake
#                 clients.append(packet.address)
#                 if clients.count(packet.address) > 1:
#                     answer = Packet(data = b'', flags = Flags(Flags.SYN | Flags.ACK), seq = packet.seq)
#                     my_socket.sendto(packet.header + packet.data, packet.address)
#                     return
#                 else:
#                     answer = Packet(data = b'', flags = Flags(Flags.ACK), seq = packet.seq)
#                     my_socket.sendto(answer.header + answer.data, packet.address)
#                     return