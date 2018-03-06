# import struct
# import UDP
# import UDPsocket
# from UDP import udp
HEADER = 8
# # a = b'\xff\xde\x0f\xc8\x00\x48\x2f\x7f\xad\xbc'
# # src_port, dst_port, length, checksum = struct.unpack('!HHH2s', a[:HEADER])
# src_port = 65502
# dst_port = 4040
# payload = bytes.fromhex('00ca0a000001000000000002029c40f8addc62c642c990f1cea1e942adb509000000000000000000000000000000000c00000000000100070072616d32303135')
# datagram = UDP.udp_pack(src_port, dst_port, payload)
# udp1 = UDP.udp_unpack(datagram)
# new = udp1.pack()
# newudp = UDP.udp_unpack(new)
# # frame = struct.pack('!HHH2s%ds' % len(payload), src_port, dst_port, length, checksum, payload)
# print(udp)
# print(newudp)
# UDP.buffer[100] = 1
# UDP.buffer[200] = 2
# us = UDPsocket.UDPsocket()
# us.bind(15, 10)
# print(UDP.buffer)
import queue
import threading
import test_udp2
import test_udp3
import time
a = queue.Queue()
a.put(1)
a.put(2)
class t(object):
    def __init__(self):
       pass
    # print(a.get())
    # print(__name__)
    def test(self):
        a.put(2)
        a.put(3)
    def print(self):
        while a:
            print(a.get())
    # if __name__ == '__main__':
def add():
    a.put(3)

test_udp2.add()
