# About transfers

## Transfer types

There are two types of transfers: **Sender** and **Receiver**.

    When sending a file, the sender generates a unique transfer_flag and assigns it to the transfer.

    The transfer_flag is embedded in the data being sent. This allows the receiver to know which transfer the data corresponds to.

    The receiver reads the transfer_flag from the received data, associates it with a specific transfer, and processes the data accordingly.

This approach work well for managing multiple transfers between sender and receiver.

## Sender

The sender is responsible for creating a transfer and sending data.

    It generates a packet with File flag and sends it to the receiver with the data.
    Data are: name of a file, extension, and transfer_flag.

1. It waits, for SACK from the receiver, and if it receives it, it starts sending data.

    It generates a packet with transfer_flag as Flag and sends it to the receiver with the data.
    Data are: Raw data.

2. If it doesnt receive SACK, it resends the packet with File flag.

3. Sender, waits for ACK from the receiver, and if it receives it, it sends the next packet, 
    otherwise it resends the packets, or it does both, resends and if there more packets to send, it sends them.

4. When it sends the last packet, it waits for ACK from the receiver, and if it receives it, it sends the packet with FIN flag.

5. If it doesnt receive FIN in a certain amount of time, it resends the packet with FIN flag again.


## Receiver

The receiver is responsible for receiving data and sending ACKs. SACK and FIN.

    It receives a packet with File flag, and if it receives it, it sends SACK to the sender, with the transfer_flag in the data.

1. It receives a packet with transfer_flag as Flag, and if it receives it, it sends ACK to the sender, with the transfer_flag in the data.

2. When Receiver receives the packet with FIN flag, it sends FIN to the sender, with the transfer_flag in the data.

3. If it doesnt receive FIN in a certain amount of time, it resends the packet with FIN flag again.

4. In the end Receiver prints the name of the file, extension, and the size of the file and pull path.