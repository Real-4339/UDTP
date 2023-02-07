# Made by Vadym Tilihuzov
# Date: 1.02.2023

"""
socket.recvfrom() returns a tuple (data, address)
socker.recv() returns data
"""

import socket
import asyncio
from Packet import Packet


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


def get_port() -> int:
    port = int(input('Enter port: '))
    if port < 49152 or port > 65535:
        print('Error: port must be in range 49152 - 65535')
        return get_port()
    return port


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
        cmd = input('Enter command: ')
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
def create_connection():
    print('Creating new connection')
    ip = input('Enter ip: ')
    port = input('Enter port: ')
    payload = input('Enter payload: ')
    packet = Packet(payload.encode(), ['0', '1', '', '', '', '', '', '1'])
    



# Main loop
async def V8():
    print('Server started')
    main_loop = asyncio.get_event_loop()
    while True:
        task1 = main_loop.create_task(console())
        task2 = main_loop.create_task(listener())

        await task1
        await task2

        if task1.result() == False:
            task1.cancel(
                my_socket.close()
            )
            task2.cancel()
            main_loop.stop()
            main_loop.close()
            break

        if task1.result() == 'new_connection':
            create_connection()

        if task2.result() != None: # TODO: add packet handling
            print(task2.result())


if __name__ == '__main__':
    asyncio.run(V8())
