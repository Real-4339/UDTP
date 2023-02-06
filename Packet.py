
class Packet:
    def __init__(self, data: bytes, address: tuple):
        self.data = data
        self.address = address

    def create_packet(self, data: bytes, address: tuple):
        print("in create_packet", "data:", data, "address:", address)
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

    def __bool__(self):
        return bool(self.data) and bool(self.address)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __contains__(self, item):
        return item in self.data

    def __add__(self, other):
        return Packet(self.data + other.data, self.address)

    def __sub__(self, other):
        return Packet(self.data - other.data, self.address)

    def __mul__(self, other):
        return Packet(self.data * other.data, self.address)

    def __truediv__(self, other):
        return Packet(self.data / other.data, self.address)

    def __floordiv__(self, other):
        return Packet(self.data // other.data, self.address)

    def __mod__(self, other):
        return Packet(self.data % other.data, self.address)

    def __divmod__(self, other):
        return Packet(divmod(self.data, other.data), self.address)

    def __pow__(self, power, modulo=None):
        return Packet(pow(self.data, power, modulo), self.address)

    def __lshift__(self, other):
        return Packet(self.data << other.data, self.address)

    def __rshift__(self, other):
        return Packet(self.data >> other.data, self.address)

    def __and__(self, other):
        return Packet(self.data & other.data, self.address)

    def __xor__(self, other):
        return Packet(self.data ^ other.data, self.address)

    def __or__(self, other):
        return Packet(self.data | other.data, self.address)