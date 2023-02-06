
class Packet:
    def __init__(self, data: bytes, flags: list):
        self.flags = flags
        self.seq = 0
        self.crc_16 = 0
        self.data = data
        return self.create_packet(self, data, flags)

    def create_packet(self, data: bytes, flags: list):
        
        return
    
    def undo_packet(self, packet: 'Packet'):
        ...

    def __str__(self):
        return f'Packet(data={self.data}, address={self.address})'

    def __repr__(self):
        return f'Packet(data={self.data}, address={self.address})'

    def __eq__(self, other):
        return self.data == other.data and self.address == other.address

    def __hash__(self):
        return hash((self.data, self.address))

    
def getHex(data: bytes):
    return ''.join(f'{x:02x}' for x in data)

def gethex(packet):

  data = bytes(packet).hex().upper()
  data = [data[i:i+2] for i in range(0, len(data), 2)]

  return data