# R-UDP header model

```C
header = struct.pack('!BHB', flags.value, crc16, seq_num)
```

<!-- This line creating a header for the packet. Which is a binary string of 2 unsigned byte values(`value1`, `value2`). The `!` is for network byte order (big-endian). `B` is for unsigned byte. `flags` is the first byte and `seq` is the second byte. -->