import struct
from Exceptions import *
HEADER = 8
buffer = dict()

class udp(object):
    def __init__(self, src_port, dst_port, payload):
        self.src_port = src_port
        self.dst_port = dst_port
        self.payload = payload

    def pack(self):
        return pack(self.src_port, self.dst_port, self.payload)

    def __str__(self):
        return 'src: %(src_port)s\n' \
               'dst: %(dst_port)s\n' \
               'payload: %(payload)s}\n' % self.__dict__


def pack(src_port, dst_port, payload):
    length = len(payload) + HEADER
    uncheck_segment = struct.pack('!HHHH%ds' % len(payload), src_port, dst_port, length, 0, payload)
    checksum_ = checksum(uncheck_segment)
    segment = struct.pack('!HHHH%ds' % len(payload), src_port, dst_port, length, checksum_, payload)
    return segment

def unpack(segment):
    src_port, dst_port, length, checksum_ = struct.unpack('!HHHH', segment[:HEADER])
    payload = segment[HEADER:]
    checksum_ = checksum(segment)
    if checksum_ != 0:
        raise ChecksumErrorException
    return udp(src_port, dst_port, payload)

def checksum (data):
    data = data if len(data)%2 ==0 else data+b'\x00'
    data_array = struct.unpack('!%dH'%(len(data)/2), data)
    s = 0
    for d in data_array:
        s += d
    s = (s & 0xFFFF) + (s >> 16)
    s += (s >> 16)
    return ~s & 0xFFFF



# u = UDP()
# header = struct.pack('>H', 65502)+struct.pack('>H', 4040)+struct.pack('>H', 72)+b'\x2f\x7f'
# print(u.decode(b'\xff\xde\x0f\xc8\x00\x48\x2f\x7f'))