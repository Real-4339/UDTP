
- push all packet merge functionallity to another process, if somehow application(peer) is down, so every packet that was delivered 100% will be saved on pc. And also that merge process wont block peer from receiving packets.

- prepare packet func also can be redone by peer(app), it can devide file into 512 packets, and continuosly upload next packets, so the full file wont be stored in memory, and also peer(app) can remake this process, peer(app) can create some singleton class or some global object, so if two or more clients wanted to download the same file, they can share those memory and file wont be stored twice.

- encryption, and decryption, so if someone will sniff packets, he wont be able to read them.

- use CRC-32 instead of CRC-16. CRC-32 is more reliable, but it is 2 times bigger than CRC-16. Speed or reliability?

- IP header can take up to 60 bytes -> change max payload size from 1468 to 1428 bytes. Or dynamic payload size... 

- add back system analysis of working UDTP apps on same network, so if new UDTP is registered, it would already know if there are any other UDTPs on the same network, and it would be able to connect to them. Or over all interfaces.

- RangeACK, WM can be remade, like 0b01000000 can be used for WM, and from 0b01000001 to 0b01111111 can be used for RangeACK, so it would be possible to send 127 RangeACKs in one packet. For one Window.
(Hard) [Not sure is that can work at all.] I dont like acks system of UDTP, to many acks.