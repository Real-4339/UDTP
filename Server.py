# Made by Vadym Tilihuzov
"""
Need to add thread that will be listening for new connections and connect them to the server
Alse that first thread need to send configs between server and clients and read commands from cmd

---
# dns_resolved_addr = socket.gethostbyname(host)
# print("DNS resolved address:", dns_resolved_addr)
---

"""
import socket
import sys
import threading
import time

COUNT_OF_CLIENTS_TO_CONNECT = 2

def server_listenig(): 
    # get the hostname
    host = socket.gethostname() # maybe need to use gethostbyname
    port = "51200" # private port of server
    port_int = int(port) 
    
    server_socket = socket.socket() # get instance
    server_socket.bind((host, port_int))  # bind host address and port together

    # configure how many client the server can listen
    server_socket.listen(COUNT_OF_CLIENTS_TO_CONNECT)
    conn, address = server_socket.accept()  # accept new connection

    print("accept", str(conn), str(address))

    while True:
        # receive data stream. it won't accept data packet greater than 1486 bytes
        data = conn.recv(1486).decode()
        if not data: # remake
            # if data is not received break
            break
        print("from connected user: " + str(data))
        data = input(' -> ')
        conn.send(data.encode())
    
    conn.close()  # close the connection
    

if __name__ == '__main__':
    server_listenig()
    