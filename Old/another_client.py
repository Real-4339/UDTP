import time
import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(1.0)

for pings in range(10):
    message = 'test 123'
    message = message.encode()
    addr = ("127.0.0.1", 12000)

    start = time.time()
    client_socket.sendto(message, addr)
    try:
        data, server = client_socket.recvfrom(1024)
        end = time.time()
        elapsed = end - start
        data = data.decode("utf-8")
        print(f'{data} {pings} {elapsed}')
    except socket.timeout:
        print('REQUEST TIMED OUT')