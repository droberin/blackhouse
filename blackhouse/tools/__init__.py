#
# Copyright (C) 2002 by Micro Systems Marc Balmer
# Written by Marc Balmer, marc@msys.ch, http://www.msys.ch/
# This code is free software under the GPL

import struct, socket


def wake_on_lan(ethernet_address):

    # Construct a six-byte hardware address
    address_byte = ethernet_address.split(':')
    hardware_address = \
        struct.pack('BBBBBB',
                    int(address_byte[0], 16),
                    int(address_byte[1], 16),
                    int(address_byte[2], 16),
                    int(address_byte[3], 16),
                    int(address_byte[4], 16),
                    int(address_byte[5], 16)
        )

    # Build the Wake-On-LAN "Magic Packet"...
    message = b'xff' * 6 + hardware_address * 16

    # ...and send it to the broadcast address using UDP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.sendto(message, ('', 9))
    s.close()

# Example use
# WakeOnLan('0:3:93:81:68:b2')
