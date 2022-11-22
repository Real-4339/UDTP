# Made by Vadym Tilihuzov
"""
Problem: if client has more than one network card, then it will be problem with finding ip and mask
"""
import socket
import subprocess
import os
import nmap
import ifcfg


multiple_networks = False

def client_program():
    global multiple_networks

    # read from config file ip and port of server
    port = "51200"  # socket server port number
    port_int = int(port)

    try:
        # find ip and port of client
        out = subprocess.Popen(('ifconfig'), stdout=subprocess.PIPE)
        config = subprocess.check_output(('grep', 'broadcast'), stdin=out.stdout)
        out.wait()
        
        # get values
        ip = config.split()[1]
        mask = config.split()[3]
        # decoding ip and mask
        ip = ip.decode("utf-8")
        mask = mask.decode("utf-8")
        # make lists
        ip_list = ip.split(".")
        mask_list = mask.split(".")
        
        # find network address
        network = ""
        for a in range(4):
            if a == 3:
                network += str(int(ip_list[a]) & int(mask_list[a]))
            else:
                network += str(int(ip_list[a]) & int(mask_list[a])) + "."    
    except:
        print("Error with finding ip and mask")
        multiple_networks = True
    
    if multiple_networks == False:
        # find all ip in network
        devices = []
        for device in os.popen('arp -a'): a = device.split()[1]; devices.append(a[1:len(a)-1])
        # find ip of server
        host = ""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        print(s.getsockname()[0])
        s.close()
        return
        nm = nmap.PortScanner()
        for a in devices:
            nm.scan(a, port)
            print(nm.all_hosts())
            #print(nm[a]['tcp'][port_int]['state'])
        #     if nm[a].state() == "up":
        #         host = a
        #         break
        # print("Server ip:", host)
        
        return

        client_socket = socket.socket()  # instantiate
        client_socket.connect((host, port_int))  # connect to the server

        message = input(" -> ")  # take input

        while message.lower().strip() != 'bye':
            client_socket.send(message.encode())  # send message
            data = client_socket.recv(1486).decode()  # receive response

            print('Received from server: ' + data)  # show in terminal

            message = input(" -> ")  # again take input

        client_socket.close()  # close the connection
    else:
        ip = input("Enter ip of server: ")
        port = input("Enter port of server: ")

        client_socket = socket.socket()  # instantiate
        try:
            client_socket.connect((ip, port))  # connect to the server
        except:
            print("Error with connecting to server, try using ip and port of server... NERD")
            return
        

if __name__ == '__main__':
    client_program()