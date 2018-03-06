import struct
import Router
import UDP
import ICMP
import UDPsocket
from Exceptions import *
import TCPsocket

HEADER = 14
DEFAULT_TTL = 64 # todo read from file
# [for present]
import json
with open('show.json', 'r') as f:
    dict_ = json.loads(f.read())
DEFAULT_TTL = dict_['DEFAULT_TTL']
# [end]
PROTOCOL_ICMP = 1
PROTOCOL_TCP = 2
PROTOCOL_UDP = 3

'''
class IP contains the send functions for routers
for connectionless and connectin-oriented transport layer protocols,
network layer may not recv the dst_ip. Therefore, it contains two send methods
'''
class IP(object):
    def __init__(self, protocol, src_ip, dst_ip = None):
        '''
        :param protocol: the input protocol type, it can be ICMP, TCP and UDP
        :param src_ip: source ip
        :param dst_ip: if UDP, destination ip is None
        '''
        self.protocol = protocol
        self.src_ip = src_ip
        self.dst_ip = dst_ip

    def send(self, segment):
        '''
        This send method is for TCP. It will pack a TCP datagram into a IP datagram and send it to router.
        :param segment: transport layer datagram
        :return: None
        '''
        datagram = pack(self.src_ip, self.dst_ip, self.protocol, segment)
        Router.send(datagram, self.dst_ip)
        
    def sendto(self, dst_ip, segment):
        '''
        This sendto method is for UDP.
        By using the given dst_ip, it will pack a UDP datagram into a IP datagram and send it to router.
        :param dst_ip: The given dst_ip for UDP transmission
        :param segment: transport layer datagram
        :return: None
        '''
        datagram = pack(self.src_ip, dst_ip, self.protocol, segment)
        Router.send(datagram, dst_ip)

'''
class ip is only for pack datagram more conveniently 
because of bunches of parameters and headers in datagram
'''
class ip(object):
    def __init__(self, src_ip, dst_ip, protocol, ttl, segment):
        '''
        Receive the elements for generate a ip datagram
        :param src_ip: source ip
        :param dst_ip: destination ip
        :param protocol: upper layer protocol type
        :param ttl: time to live
        :param segment: transport layer datagram
        '''
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.protocol = protocol
        self.ttl = ttl
        self.segment = segment
    
    def pack(self):
        '''
        Based on the memeber variables, pack the datagram
        :return: the packed ip datagram
        '''
        return pack(self.src_ip, self.dst_ip, self.protocol, self.segment, self.ttl)
        
def pack(src_ip, dst_ip, protocol, segment, ttl=DEFAULT_TTL):
    '''
    A static tool method for packing ip datagram.
    First, pack it into an unchecked datagram with a void checksum.
    Then, calculate the checksum and repack it into a complete datagram
    :param src_ip: source ip
    :param dst_ip: destination ip
    :param protocol: upper layer protocol type
    :param ttl: time to live
    :param segment: transport layer datagram
    :return: A checksum-contained ip datagram
    '''
    src_ip = ip2byte(src_ip)
    dst_ip = ip2byte(dst_ip)
    payload_length = len(segment)
    uncheck_datagram = struct.pack('!4s4sBBHH%ds'%payload_length,src_ip,dst_ip,ttl,protocol,payload_length,0,segment)
    current_checksum = checksum(uncheck_datagram)
    check_datagram = struct.pack('!4s4sBBHH%ds'%payload_length,src_ip,dst_ip,ttl,protocol,payload_length,current_checksum,segment)
    return check_datagram

def unpack(datagram):
    '''
    Based on the ip datagram format, unpack it into headers and segment
    If there is uncorrect checksum, raise exception
    :param datagram: the ip datagram
    :return: a ip object with datagram info
    '''
    src_ip, dst_ip, ttl, protocol, payload_length, current_checksum = struct.unpack('!4s4sBBHH', datagram[:HEADER])
    checksum_ = checksum(datagram)
    if checksum_!=0:
        raise ChecksumErrorException
    segment = datagram[HEADER:]
    return ip(ip2Str(src_ip), ip2Str(dst_ip), protocol, ttl, segment)

def ip2byte(str_ip):
    '''
    A tool method for convert string ip address into byte
    :param str_ip: ip in string format
    :return: a byte format ip
    '''
    ipstr = str_ip.split('.')
    ipint = [int(str) for str in ipstr]
    return struct.pack('!BBBB',ipint[0],ipint[1],ipint[2],ipint[3])

def ip2Str(ip_byte):
    ip1,ip2,ip3,ip4 = struct.unpack('!BBBB', ip_byte)
    return '%d.%d.%d.%d'%(ip1,ip2,ip3,ip4)

def checksum(datagram):
    '''
    A tool method for calculate the checksum of ip datagram
    :param datagram: datagram needs checking
    :return: the chucksum
    '''
    datagram = datagram if len(datagram) % 2 == 0 else datagram + b'\x00'
    data_array = struct.unpack('!%dH'%(len(datagram)/2), datagram)
    s = 0
    for d in data_array:
        s += d
    s = (s & 0xFFFF) + (s >> 16)
    s += (s >> 16)
    return ~s & 0xFFFF

def push(datagram):
    '''
    Push the datagram into different upper layers based on the protocol type
    :param datagram: the datagram need pushing
    :return: None
    '''
    network = unpack(datagram)
    if network.protocol == PROTOCOL_TCP:
        TCPsocket.TCPsocket.push(network.segment, network.src_ip)
    elif network.protocol == PROTOCOL_UDP:
        UDPsocket.push(network.segment, network.src_ip)
    elif network.protocol == PROTOCOL_ICMP:
        ICMP.push(network)
    else:
        pass





