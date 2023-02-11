import asyncio
import sys
from Packet import Flags


class Test:
    def __init__(self, function) -> None:
        self.__function = function
        self.__call__()

    def prints(self):
        print('Hello Worllld!')

    def __call__(self):
        if self.__function == 'prints':
            self.prints()
        else:
            print("else")
            self.__function()
    
    def __repr__(self) -> str:
        return self.__function


# test = Test(lambda: print('He@llo World'))

# test = Test("prints")
# print(test, Test("prints"))

# flags = Flags(
#     Flags.SYN | Flags.WM | Flags.ACK
# )

# if flags & (Flags.SYN | Flags.WM) == (Flags.SYN | Flags.WM):
#     print('SYN and WM and more if there are any')

# if flags == (Flags.SYN | Flags.WM):
#     print('SYN and WM only')

# print(flags.__sizeof__())
# print(sys.getsizeof(flags))


# print(flags.to_bytes(1, 'big'))
# print(flags.to_bytes(1, 'big').__sizeof__())

# # declaring an integer value
# integer_val = b'25'
# print(integer_val)  
# converting int to bytes with length 
# of the array as 2 and byter order as big
#bytes_val = integer_val.to_bytes(1, 'big')
  
# printing integer in byte representation
#print(bytes_val)
#print(bytes_val.__sizeof__())
#print(sys.getsizeof(bytes_val))

async def waiter():
    task1 = asyncio.create_task(cook('pizza', 8)) 
    task2 = asyncio.create_task(cook('burger', 5))
    task3 = asyncio.create_task(cook('pasta', 3))

    food1 = await task1
    food2 = await task2
    food3 = await task3
    print(f'All food is ready: {food1}, {food2}, {food3}')


async def cook(food: str, time: int):
    a = '1488'.encode()
    print(a, a.decode())
    print(f'Cooking {food}, {time} seconds')
    await asyncio.sleep(time)
    print(f'{food} is ready!')
    return food

asyncio.run(waiter())