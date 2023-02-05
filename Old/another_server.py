import random
import socket
from Packet import Packet

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('', 12000))

while True:
    rand = random.randint(0, 10)
    message, address = server_socket.recvfrom(1024)
    packet = Packet(message, address)
    packet.create_packet(message, address)
    if rand >= 4:
        server_socket.sendto(message, address)