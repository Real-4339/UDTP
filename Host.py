# Made by Vadym Tilihuzov
# Date: 1.02.2023

import random
import socket


def connected (socket) -> bool:
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

# Function checking new connection
def check_for_connection():
    client, address = my_socket.accept()
    clients.append(client)
    print(f'Connected with {str(address)}')
    client.send('You are now connected.'.encode('utf-8'))

# Main loop