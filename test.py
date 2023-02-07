import sys
from Packet import Flags


flags = Flags(61)
print(flags.__sizeof__())
print(sys.getsizeof(flags))

print(flags.to_bytes(1, 'big'))
print(flags.to_bytes(1, 'big').__sizeof__())

# declaring an integer value
integer_val = b'25'
print(integer_val)  
# converting int to bytes with length 
# of the array as 2 and byter order as big
#bytes_val = integer_val.to_bytes(1, 'big')
  
# printing integer in byte representation
#print(bytes_val)
#print(bytes_val.__sizeof__())
#print(sys.getsizeof(bytes_val))