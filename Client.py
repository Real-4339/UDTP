# Made by Vadym Tilihuzov

import socket, time


clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientSocket.settimeout(1.0)
message = b'test'

addr = ("127.0.0.1", 51200)
start = time.time()
clientSocket.sendto(message, addr)

try:
    data, server = clientSocket.recvfrom(1024)
    end = time.time()
    elapsed = end - start
    print(f'{data} {elapsed}')
except socket.timeout:
    print('REQUEST TIMED OUT')