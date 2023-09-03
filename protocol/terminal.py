import logging
import threading

from host import Host

class Terminal:
    def __init__(self, host: Host, stop_event: threading.Event):
        self.__host = host
        self.__stop_event = stop_event
        self.running = False

    def start(self):
        self.running = True
        logging.basicConfig(level=logging.NOTSET)
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
            self.stop()
        elif command == 'help':
            self.display_help()
        
        elif command.startswith('log_level'):
            self.logging(command)

        elif command == 'my_address':
            print('My address is {}:{}'.format(self.__host.me.ip, self.__host.me.port))
        
        elif command.startswith('connect'):
            ip, port = command.split(' ')[1].split(':')
            
            if self.__host.validate_addr(ip, int(port)):
                print('Starting connection to {}:{}'.format(ip, port))
                self.__host.connect(ip, int(port))
            else:
                print('Invalid address: {}:{}'.format(ip, port))
            
        
        elif command.startswith('disconnect'):
            ip, port = command.split(' ')[1].split(':')
            
            if self.__host.validate_addr(ip, int(port)):
                print('Starting disconnection from {}:{}'.format(ip, port))
                self.__host.disconnect(ip, int(port))
            else:
                print('Invalid address: {}:{}'.format(ip, port))
        
        elif command == 'disconnect_all':

            print('Started disconnection from all hosts')
            self.__host.disconnect_all()
        
        elif command == 'list':
            self.__host.list_connections()
        
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
        print('  list_available: List available hosts') # TODO: Implement
        print('  detection_time <time>: Set the detection time of available hosts') # IDK if i want this
        print('  send_m <ip>:<port> <message>: Send a message to a host')
        print('  send_f <ip>:<port> <file>: Send a file to a host') # TODO: Implement
        print('  change_fragment_size <size>: Change the fragment size')
        print('  log_level <level>: Set the log level')
        print('  help: Display this help message')
        print('  exit: Exit the terminal')