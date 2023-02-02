# Made by Vadym Tilihuzov
# Date: 1.02.2023

"""
socket.recvfrom() returns a tuple (data, address)
socker.recv() returns data
"""

import socket
import threading
import asyncio


def connected (socket) -> bool: # TODO: recreate using my Packet class and Libuv
    try:
        socket.send(b'')
    except socket.error:
        return False
    return True

def existing_socket (socket) -> bool:
    try:
        socket.getsockname()
    except socket.error:
        return False
    return True

def get_port () -> int:
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
my_socket.bind(('', PORT)) # TODO: add ip handling
my_socket.listen()

# Function checking new connection # Useless
def check_for_connection(): # TODO: recreate using my Packet class and Libuv
    client, address = my_socket.accept()
    clients.append(client)
    print(f'Connected with {str(address)}')
    client.send('You are now connected.'.encode('utf-8'))

# Console loop, use yeild
def console():
    while True:
        cmd = input('Enter command: ')
        if cmd == 'exit':
            my_socket.close()
            exit()
        elif cmd == 'list':
            print(clients)
        elif cmd == 'help':
            print('Commands: list, exit')
        else:
            print('Unknown command')

# Listener loop, use yeild
def listener():
    while True:
        try:
            data, addr = my_socket.recvfrom(1024) # TODO: 1024 is buffer size
            print(data, data.decode())
            # print(f'From {addr[0]}:{addr[1]}: {data.decode()}')
        except:
            pass

# Main loop
def V8():
    print('Server started')
    while True:
        ...

if __name__ == '__main__':
    V8()