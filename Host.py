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

# Creating socket
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.bind(('', PORT)) # TODO: add ip handling

# Main loop