# Table of Contents

- [UDTP (UDP Reliable Transfer Protocol)](#udtp-udp-reliable-transfer-protocol)
- [UDP](#udp)
  * [Why UDP, but not TCP?](#why-udp-but-not-tcp)
  * [UDP Header](#udp-header)
- [General Information](#general-information)
    * [Implementation enviroment and basic tech-implementation information](#implementation-enviroment-and-basic-tech-implementation-information)
    * [Specification](#specification)
        + [IP and ports](#ip-and-ports)
- [Protocol](#protocol)
    * [Header Structure](#header-structure)
    * [Header specification](#header-specification)
        + [Flags](#flags)
            - [Notes](#notes)
        + [Checksum](#checksum)
            - [Example (CRC-16)](#example--crc-16-)
            - [UDP Checksum(RFC 1071)](#udp-checksum-rfc-1071-)
            - [Combined Checksum](#combined-checksum)
    * [Features](#features)
        + [Flow Control (TCP)](#flow-control--tcp-)
        + [Flow Control (UDTP)](#flow-control--udtp-)
- [Protocol rules and conventions](#protocol-rules-and-conventions)
    * [Connection Establishment](#connection-establishment)
    * [Keep Alive](#keep-alive)


# UDTP (UDP Reliable Transfer Protocol)

UDTP is a P2P protocol that provides reliable data transfer over UDP and that is easy to implement and understand.  

UDTP used for transferring files between systems in a local network.

It is designed to be used in situations where TFTP is not suitable, and FTP is too complicated and can not send as quick and as much data as UDTP, if we are talking about FTP on TCP. Also FTP is client-server. 

My protocol in a future can be updated and upgrated via some instructions i left in own repository. Read more about it in [Improvements.md](Improvements.md).

# UDP

Lets first look at udp, and why do i created another protocol on top of it.

UDP in general is a connectionless protocol, which means that there is no connection between the sender and the receiver before the actual data transfer happens. The sender sends data to the receiver without knowing whether the receiver is ready to receive the data. If the receiver is not ready to receive the data, the data is lost.

UDP is less usable in a network, its fast but not reliable. UDP does not provide any confirmation of packet delivery, any ordering of packets, or any protection against duplication. UDP is used in applications where speed is desirable and error correction is not necessary. For example, UDP is frequently used for live broadcasts and online games.

## Why UDP, but not TCP?

TCP is a connection-oriented protocol, but too much complicated, it has a lot of features, but in a case of file transfer, it is not the best choice. Minimum header size of TCP is 20 bytes, and maximum is 60 bytes. And also an IP header can take up to 60 bytes, so min aval. payload size is 1380 bytes, and max is 1460 bytes. UDP is always 8 bytes...

## UDP Header

Image from [Wikipedia](https://en.wikipedia.org/wiki/User_Datagram_Protocol)

# General Information

## Implementation enviroment and basic tech-implementation information

Protocol UDTP was implemented in Python 3 programming language with using following libraries:

- time
- socket
- threading
- netifaces
- selectors
- struct
- logging
- crcmod
- os

Why do i use those libraries?

| Name of lib | How do i use it? | Functionality |
|:-----------:|:----------------:|:-------------:|
| time | Get current time, for ttl and timeout | time.time() |
| socket | Create socket, send and receive data | socket.socket() |
| threading | Creted a thread for terminal | threading.Thread() |
| netifaces | Get IP addresses of the interfaces | netifaces.ifaddresses() |
| selectors | For gathering data from sockets | selectors.DefaultSelector() |
| struct | For packing and unpacking data | struct.pack() |
| logging | For logging | logging.basicConfig() |
| crcmod | For CRC16 checksum | crcmod.predefined.Crc('crc-ccitt-false') |
| os | For getting writing and reading files | os.path.exists(), etc. |

## Specification

This project was requested by my university, STU, FIIT. It was requested to create a protocol, which will be able to send and receive files, and also messages. It was requested to use UDP.

BUT, in the task also requested, not only to create a protocol, but also to create an application for it, which will be able to send and receive files and messages. 

The application i made is a CLI application, created on Linux, but it can be easily ported to Windows or MacOS, because i use only standard libraries, which are available on all platforms.

An app is asynchronous, it can send and receive data at the same time. I dont use any `threads` or any `async` libraries, i use 
`selectors` library, which is a part of Python 3.4 and higher.

For communication between apps, they have to know ip and ports of each other. 

### IP and ports

IP addresses are taken from the interfaces, so app can work only on existing interfaces. If there are no interfaces, app will not work.

Ports are taken randomly, but they are taken from a range of 49152-65535, because ports from 0-49151 are reserved for system use.

# Protocol

## Header Structure

Mine UDTP protocols header looks like so:

| Flags (1 byte) | CRC16 (2 bytes) | Sequence Number (1 byte) |
|:--------------:|:---------------:|:------------------------:|
|| Payload ||

And full with UDP header:

| Source Port (16) | Destination Port (16) | Length (16) | Checksum (16) | Flags (8) | CRC16 (16) | Sequence Number (8) |
|:----------------:|:---------------------:|:-----------:|:-------------:|:---------:|:----------:|:--------------------:|
|||| Payload ||||

## Header specification

### Flags

| Flag | Value | Description |
|:----:|:-----:|:-----------:|
| SYN | 0x01 | Synchronize |
| ACK | 0x02 | Acknowledge |
| SACK | 0x04 | Super Acknowledge |
| MSG | 0x08 | Message |
| FILE | 0x10 | File |
| SR | 0x20 | (Send/Receive) Number of Send/Receive objects in real time |
| WM | 0x40 | Window Multiplier |
| FIN | 0x80 | Finish |

#### Notes

There are things i wont to clarify about flags.

SACK - special flag i use in different situations, for example in keep alive packets, or in when i send a file, receiver uses SACK to acknowledge that he starts listening for a file. And many more.

WM - Window Multiplier, is a flag i use to tell receiver that i can use extended window size (64 packets), and i want to use it. Receiver can ignore it, and in return ill get basic ack, without WM flag, that means we agreed on basic one (16 packets). Or he can ack with WM flag, that means we agreed on extended window size.

I didnt use full potencial of this flag (bits), i could use it in a future for ack range, or smth like that, if ill get idea, how could i do that...

SR - Send/Receive, i use this metric to control what is thats packet conversation is goes to.

More about Flags in ...

### Checksum

CRC or Cyclic Redundancy Check, is a type of checksum algorithm that is used to 
detect errors in  data transmission  or storage. 
The basic idea behind a CRC algorithm is to generate a checksum, or a 
small amount of error-detecting code, based on the data being transmitted.  
When the data is received, the receiver can use the same CRC algorithm to generate a checksum based on the received data and compare it to the original checksum. If the two checksums match, the data is assumed to be error-free. 
If they do not match, it indicates that there was an error in transmission and the data may be corrupted.  

#### Example (CRC-16)

For example, lets say i have 1 GB file, i have packet len 1428B, that means ill have 700281 packets. There is a formula: (1 - error rate) ^ (packet count). That formula will give us the probability of a random error going undetected.

So lets find out crc16 error rate. CRC-16 is 16 bits, so it can have 65536 different values. So error rate is 1/65536 = 0.0000152587890625. Or 0.00152587890625%. The probability of a random error going undetected is (1 - 0.0000152587890625) ^ 700281 = 2.287372724887968e-05 or 0.00002287372724887968. So the probability of a random error going undetected is 0.002287372724887968%. And based on formula it gives us approximately 2 packets with errors might not be detected by CRC16.  

However, this is a theoretical estimation and actual results can vary based on various factors. Because work of CRC16 can catch some robust errors, so the percentage of undetected errors can be even lower.

#### UDP Checksum(RFC 1071)

The Internet Checksum (RFC 1071) is a simple checksum algorithm that is used in the Internet Protocol (IP), Transmission Control Protocol (TCP), and User Datagram Protocol (UDP). It is designed to provide a first line of defense against corrupted data, but it is not foolproof. 

The probability of an undetected error for a single bit in Internet Checksum (RFC 1071) is not explicitly defined in the RFC document. However, it’s important to note that the Internet Checksum is a simple sum of 16-bit words, and it can miss some types of errors that a more robust checksum or CRC might catch.

For example, if two bits in the same position in two different 16-bit words are flipped, the Internet Checksum will not detect this error. 

Im gonna estimate the probability of an undetected errors for the Internet checksum using similar approach:

- The checksum is 16 bits, so it can have 65536 different values. 
- Error rate is 1/65536 = 0.0000152587890625. Or 0.00152587890625%.
- The probability of a random error going undetected is (1 - 0.0000152587890625) ^ 700281 = 2.287372724887968e-05 or 0.00002287372724887968.

#### Combined Checksum

Combined = CRC-16 probability x Internet Checksum probability.

I can not really say what is the probability of an undetected error for the combined checksum, because i dont know how they work together, but i can say that even TCP uses modified RFC 1071, there are not the same, but they are similar. (RFC 1145)

So even TCP, can validate corrupted packets...

I could use CRC-32, but it is 2 times bigger than CRC-16, and it is slower. So i decided to use CRC-16.

## Features

- Flow control
- Fast retransmit
- Selective repeat
- Error simulation
- Retransmission timeout
- Reliable data transfer

### Flow Control (TCP)

About Flow Control, basically how it works in TCP? TCP uses a sliding window
protocol to control the flow of data between two hosts. The sender can only
send as much data as the receiver can receive. The receiver advertises the
size of its receive window in the TCP header. The sender can only send as
much data as the receiver's window size. The receiver's window size is
determined by the amount of free space in the receive buffer. The receive
buffer is a fixed size and is determined by the operating system. 

TCP uses a combination of the Go-Back-N and Selective Repeat mechanisms.  
This hybrid approach is known as Selective Repeat with Selective Acknowledgments (SACK).

- With SACK, the receiver can acknowledge individual out-of-order segments, allowing the sender to retransmit only the missing segments rather than the entire window.
    
- This improves efficiency compared to pure Go-Back-N, especially in the presence of network conditions causing occasional packet loss or reordering.

So, simple example:

Lets say the receiver's window size is 10 packets. 
- The sender sends 10 packets of data to the receiver.
- The receiver receives 1,2,3 and 6-10 packets and acknowledges them. Either with ACK or ACK with SACK.
- The receiver sends ACK3, SACK6-10. OR just ACK3

if no SACK is used, the sender will retransmit all packets from 4-10. If SACK is used, the sender will only retransmit packets 4 and 5.

But with SACK, as receiver can get up to 10 packets, and sender needs to retransmit only 2 packets, the sender can send 8 more new packets.  

In total always will be sent up to 10 packets.

### Flow Control (UDTP)

So basically, i only use Selective Repeat. Its slightly modifed, maybe, someone, maybe me, could create a more modifed version of Selective Repeat for my protocol with ack range, but thats not a priority and not a goal of this project.

So, how does it work?

Lets say the receiver's window size is 10 packets.

- The sender sends 10 packets of data to the receiver.
- The receiver receives 1,2,3 and 6-10 packets and acknowledges them.
ACK1, ACK2, ACK3, ACK6, ACK7, ACK8, ACK9, ACK10.
- The sender gets those and sends more 8 packets.
- Every packet have his own TTL, and If sender didnt get ACKs, for packets he sent, he will retransmit them after TTL.

So, the task of receiver is only to send ACKs on each packet he gets, and the task of sender is to send packets, and retransmit them if needed.

That means, if receiver got an corrupted packet, he discards it, and wont notify sender about it...

# Protocol rules and conventions

## Connection Establishment

Connection establishment is a process that is used to set up a connection between the peers. Starts same as TCP, with 3-way handshake, but it is slightly different.

- Peer A sends SYN packet to Peer B.
- Peer B sends SYN-ACK packet to Peer A.
- Peer A sends SYN-SACK packet to Peer B.

After that, connection is established, and peers can send data to each other.

1. If Peer B didnt recv SYN packet, Peer A with keep alive func, will resend SYN packet, until Peer B will get it.

2. If Peer B didnt recv SYN-SACK packet, Peer A with keep alive func, will resend SYN-SACK packet, until Peer B will get it.

For All that part of keep alive func, if they could connect in 3 seconds, they cuts off connection.

Without Connection Establishment, peers can not send data to each other.

## Keep Alive

Keep Alive is a function, which is used to keep connection alive, and to check if peer is still alive. If keep alive func in connection establishment part, and peers didnt be able to connect in 3 seconds, keep alive func will cut off connection.

If peers are connected and dont send or recv any data, keep alive func will send keep alive packets to each other, SYN-SACK packets. Keep alive timeout is `10` seconds, but all that kinda magic numbers can be set in config file* of the app.

If peer didnt get any packet in `30` seconds, keep alive func will cut off connection.

## Connection Termination

Connection termination is a process that is used to terminate a connection between the peers. If peer B get FIN flag with no data, it means that peer A wants to terminate connection. So peer B send FIN in responce. If Connection room isnt removed by garbage collector, and it still exists, if peer B answered with his FIN, but peer A didnt get it, and if peer A again send FIN, peer B will again send FIN, but if there isnt any more this connection room. Then room will be created answered with FIN and make that room dead.

But if data isnt empty that means that fin goes to transfer room. (Transfer is over). Read more in ...

# Anything more?

Yes, there are some NOT IMPORTANT things, but thats not what the chip says, right FIIT?

## Chaning of fragmet size.
