import struct
import IP
import time
from Exceptions import *
# 1.  type=8 code=0 echo request; type=0 code=0 echo reply (ping)
# 2.  type=3 destination unreachable
#     a)  code=0 Destination network unreachable
#     b)  code=1 Destination host unreachable
#     c)  code=2 Destination protocol unreachable
#     d)  code=3 Destination port unreachable
# 3.  type=11 Time Exceeded; code=0 TTL expired in transit
request_time = 0
reply_ = 0

# class ICMP(object):
#
#     def __init__(self, src_ip, dst_ip):
#         self.IP = IP.IP(IP.PROTOCOL_ICMP, src_ip, dst_ip)
#
#     def send(self, icmp):
#         self.IP.send(icmp.pack())

class ICMP(object):
    
    def __init__(self, type, code):
        self.type = type
        self.code = code
    
    def pack(self):
        return pack(self.type,self.code)
    
    @staticmethod
    def send(src_ip, dst_ip, icmp):
        Network = IP.IP(IP.PROTOCOL_ICMP, src_ip, dst_ip)
        Network.send(icmp.pack())
        
def unpack(segment):
    type, code = struct.unpack('!BB', segment)
    return ICMP(type, code)

def pack(type, code):
    segment = struct.pack('!BB', type, code)
    return segment

def push(network):
    icmp = unpack(network.segment)
    if (icmp.type, icmp.code) in ICMP_dict:
        ICMP_dict[(icmp.type, icmp.code)](network)
    pass

def get_request(network):
    reply(network.dst_ip, network.src_ip)

def get_reply(network):
    global reply_
    print("reply from", network.src_ip, "time=", int((time.time()-request_time)*1000), "ms", "TTL=", network.ttl)
    reply_ = 0

def get_port_unreachable (network):
    raise PortUnreachableException

def get_host_unreachable (network):
    raise HostUnreachableException
def get_protocol_unreachable (network):
    raise ProtocolUnreachableException

def get_network_unreachable(network):
    pass

def get_ttl_expired (network):
    raise TTLExpiredException

def request(src_ip, dst_ip, times=4):
    global request_time, reply_
    for i in range(times):
        while reply_:
            pass
        request_time = time.time()
        send_ICMP(src_ip, dst_ip, 8, 0)
        print("send request")
        reply_ = 1

def reply(src_ip, dst_ip):
    print('reply request from', dst_ip)
    send_ICMP(src_ip, dst_ip, 0, 0)

def port_unreachable(src_ip, dst_ip):
    print('send port_unreachable')
    send_ICMP(src_ip, dst_ip, 3, 3)

def host_unreachable(src_ip, dst_ip):
    print('send host_unreachable')
    send_ICMP(src_ip, dst_ip, 3, 1)

def protocol_unreachable(src_ip, dst_ip):
    print('send protocol_unreachable')
    send_ICMP(src_ip, dst_ip, 3, 2)
    
def ttl_expired(src_ip, dst_ip):
    print('send ttl_expired')
    send_ICMP(src_ip, dst_ip, 11, 0)

def send_ICMP(src_ip, dst_ip, type, code):
    '''
    When there exists error while unpacking, the current forward will be shut down.
    And a new backward ICMP will be generated
    :param network: the existed unpacked network, we will use the src and dst ip
    :param type: ICMP type
    :param code: ICMP code
    :return:
    '''
    ICMP.send(src_ip, dst_ip, ICMP(type, code))

ICMP_dict = {
      (8, 0) : get_request
    , (0, 0) : get_reply
    , (3, 0) : get_network_unreachable
    , (3, 1) : get_host_unreachable
    , (3, 2) : get_protocol_unreachable
    , (3, 3) : get_port_unreachable
    , (11, 0) : get_ttl_expired
    }