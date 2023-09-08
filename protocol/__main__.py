import time
import socket
import threading
import netifaces

from host import Host
from terminal import Terminal

def get_available_ips() -> list:
    ip_addresses = []
    try:
        for interface in netifaces.interfaces():
            if netifaces.AF_INET in netifaces.ifaddresses(interface):
                for link in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
                    ip_addresses.append(link['addr'])
    except ValueError:
        pass

    return ip_addresses

def get_new_ip() -> str:

    ip_addresses = get_available_ips()
    print('Available IPs: {}'.format(ip_addresses))
    
    ip = input('IP >>> ')
    try:
        socket.inet_aton(ip)
        if ip not in ip_addresses:
            print('Invalid IP')
            return None
    except socket.error:
        print('Invalid IP')
        return None
    
    return ip

def get_new_port() -> int:

    print('Port range: 49152 - 65535')

    port = input('Port >>> ')
    try:
        port = int(port)
    except ValueError:
        print('Invalid port')
        return None
    
    if port < 49152 or port > 65535:
        print('Error: port must be in range 49152 - 65535')
        return None
    
    return port

def main():
    
    stop_event = threading.Event()

    ip = None
    port = None
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    ''' Get ip and port '''
    while True:
        ip = get_new_ip()
        port = get_new_port()
        if ip is not None and port is not None:
            ...
        else:
            continue
        try:
            sock.bind((ip, port))
            print('Successfully binded , so ip and port are available')
            break
        except OSError:
            print('Address already in use')
            continue
        except socket.error:
            print('Error: cannot bind to {}:{}'.format(ip, port))
            continue

    sock.close()
    
    host = Host(ip, port)
    terminal = Terminal(host, stop_event)

    host.register()

    terminal_thread = threading.Thread(target=terminal.start)
    terminal_thread.start()

    try:
        host.run()
    except KeyboardInterrupt:
        stop_event.set()
        terminal_thread.join()
        print('KeyboardInterrupted at {}'.format(time.time()))
    

if __name__ == '__main__':
    main()