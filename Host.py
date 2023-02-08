# Made by Vadym Tilihuzov
# Date: 1.02.2023

"""
socket.recvfrom() returns a tuple (data, address)
socker.recv() returns data
"""

import socket
import asyncio
from sys import stdin, stdout
from Packet import Packet, Flags


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
        return get_port()
    return port

async def ainput(string: str) -> str:
    await asyncio.get_event_loop().run_in_executor(
            None, lambda s=string: stdout.write(s+' '))
    return await asyncio.get_event_loop().run_in_executor(
            None, stdin.readline)


# Basic information
PORT = get_port()
clients = []
# aliases = []


# Creating socket
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.bind(('', PORT))  # TODO: add ip handling

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
            print('Commands: list, exit')
        elif cmd == 'new_connection':
            yield 'new_connection'
        else:
            print('Unknown command')

# Listener loop, use yeild
async def listener():
    loop = asyncio.get_event_loop()
    while True:
        try:
            # TODO: 1024 is buffer size
            data, addr = await loop.sock_recvfrom(my_socket, 1024)
            packet = Packet(data, addr)
            yield packet.create_packet(data, addr)
            
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
    packet = Packet(payload.encode(), Flags(65))
    f_packet = packet.header + packet.data
    return f_packet



# Main loop
async def V8():
    print('Server started')
    main_loop = asyncio.get_event_loop()
    while True:
        task1 = main_loop.create_task(console())
        task2 = main_loop.create_task(listener())

        await task1
        await task2

        if task1.result() == False: # end of program
            task1.cancel(
                my_socket.close()
            )
            task2.cancel()
            main_loop.stop()
            main_loop.close()
            break

        if task1.result() == 'new_connection':
            packet = await create_connection()
            if packet != False:
                ...
            else:
                ...

        if task2.result() != None: # TODO: add packet handling
            print(task2.result())


if __name__ == '__main__':
    asyncio.run(V8())
