import os
import logging
import threading

from host import Host


def is_file(path: str) -> bool:
    ''' Check if path is a file '''
    return os.path.isfile(path)


def get_name_and_extension(path: str) -> tuple[str, str]:
    ''' Get name and extension of the file '''
    
    path = os.path.basename(path)
    name, ext = os.path.splitext(path)

    return name, ext


def file_to_bytes(path: str) -> bytes | None:
    ''' Read file and return bytes '''
    
    if not is_file(path):
        print(f"File {path} does not exist")
        return None

    with open(path, "rb") as file:
        data = file.read()

    if data == b'':
        print(f"File {path} is empty")
        return None

    return data

class Terminal:
    def __init__(self, host: Host, stop_event: threading.Event):
        self.__host = host
        self.running = False
        self.__stop_event = stop_event
        
        logging.basicConfig(level=logging.NOTSET)

    def start(self):
        self.running = True
        while self.running:
            try:
                command = input('Try \'help\' >>> ')
            except EOFError:
                print()
            if self.__stop_event.is_set(): # KeyboardInterrupt
                self.stop()
                return
            self.handle_command(command)

    def stop(self):
        self.running = False

    def handle_command(self, command):
        if command == 'exit':
            self.__host.disconnect_all()
            self.__host.stop()
            print('Stopping host')
            self.stop()
        elif command == 'help':
            self.display_help()
        
        elif command.startswith('log_level'):
            self.logging(command)

        elif command == 'my_address':
            ip, port = self.__host.get_bounded_ip_port()
            print('My address is {}:{}'.format(ip, port))
        
        elif command.startswith('connect'):
            ip, port = command.split(' ')[1].split(':')
            
            if self.__host.validate_addr(ip, int(port)):
                print('Starting connection to {}:{}'.format(ip, port))
                self.__host.connect(ip, int(port))
            else:
                print('Invalid address: {}:{}'.format(ip, port))
        
        elif command == 'disconnect_all':

            print('Started disconnection from all hosts')
            self.__host.disconnect_all()
        
        elif command.startswith('disconnect'):
            ip, port = command.split(' ')[1].split(':')
            
            if self.__host.validate_addr(ip, int(port)):
                print('Starting disconnection from {}:{}'.format(ip, port))
                self.__host.disconnect(ip, int(port))
            else:
                print('Invalid address: {}:{}'.format(ip, port))

        elif command == 'list':
            self.__host.list_connections()

        elif command.startswith('send_f'):
            try:
                ip, port = command.split(' ')[1].split(':')
                file = command.split(' ')[2]
            except IndexError:
                print('Missing arguments')
                return
            
            data = file_to_bytes(file)

            if data is None:
                return
            
            if self.__host.validate_addr(ip, int(port)):
                
                print('Sending file to {}:{}'.format(ip, port))
                
                name, ext = get_name_and_extension(file)

                self.__host.send_file(ip, int(port), data, name, ext)
            else:
                print('Invalid address: {}:{}'.format(ip, port))
        
        elif command.startswith('send_m'):
            try:
                parts = command.split(' ')
                if len(parts) < 3:
                    raise IndexError

                ip_port = parts[1].split(':')
                if len(ip_port) != 2:
                    raise ValueError

                ip = ip_port[0]
                port = int(ip_port[1])
                message = ' '.join(parts[2:])
                
                if message == '' or message == ' ':
                    raise IndexError

            except IndexError:
                print('Missing or incorrect arguments')
            except ValueError:
                print('Invalid IP or port format')

            if self.__host.validate_addr(ip, int(port)):
                
                print('Sending message to {}:{}'.format(ip, port))

                message_bytes = message.encode('utf-8')
                
                self.__host.send_msg(ip, int(port), message_bytes)
            else:
                print('Invalid address: {}:{}'.format(ip, port))

        elif command.startswith('change_fragment_size'):
            try:
                size = int(command.split(' ')[1])
            except IndexError:
                print('Missing fragment size')
                return
            except ValueError:
                print('Invalid fragment size')
                return
            
            if size < 1 and size > 1468:
                print('Invalid fragment size: Allowed range is 1-1468')
                return
            
            self.__host.fragment_size = size
            print('Fragment size set to {}'.format(size))
            
        else:
            print('Unknown command: {}'.format(command))

    def logging(self, command):
        try:
            level = command.split(' ')[1]
        except IndexError:
            print('Missing log level')
            return
        
        level = level.upper()

        if not hasattr(logging, level):
            print('Unknown log level: {}'.format(level))
            logging.basicConfig(level=logging.NOTSET)
            return

        logging.basicConfig(level=getattr(logging, level))
        print('Log level set to {}'.format(level))


    def display_help(self):
        print('Available commands:')
        print('  my_address: Display the host\'s address')
        print('  connect <ip>:<port>: Connect to a host')
        print('  disconnect <ip>:<port>: Disconnect from a host')
        print('  disconnect_all: Disconnect from all hosts')
        print('  list: List connected hosts')
        print('  list_available: List available hosts')  # IDK if i want this
        print('  detection_time <time>: Set the detection time of available hosts') # IDK if i want this
        print('  send_m <ip>:<port> <message>: Send a message to a host')
        print('  send_f <ip>:<port> <file>: Send a file to a host')
        print('  change_fragment_size <size>: Change the fragment size')
        print('  log_level <level>: Set the log level')
        print('  help: Display this help message')
        print('  exit: Exit the terminal')