import random
from urllib.request import urlopen

import ICMP
import IP
import UDP
from LinkLayer import *
from LinkLayer import util
from TCP import TCP

# get the WAN of current
WAN_ip = util.get_local_ipv4_address()
# NAT: key is lan value is wan
NAT_out = {}
# NAT: key is wan value is lan
NAT_in = {}
PROTOCOL_ICMP = 1
PROTOCOL_TCP = 2
PROTOCOL_UDP = 3
ACTION_PUSH = 1
ACTION_RETURN = 2
type = {'in':NAT_in, 'out':NAT_out}
# a designed network graph. Described by adjacent list
NETWORK = {}
# the forwarding table based on the network: key is every router value is the next hop router
forwarding_table = {}


def read(path):
    '''
    A private method to generate the network graph based on a file
    :param path: the file path
    :return: None
    '''
    global NETWORK
    with open(path, 'r') as f:
        for line in f:
            result = line.split()
            if result[0] not in NETWORK:
                NETWORK[result[0]] = [(result[1],int(result[2]))]
            else:
                NETWORK[result[0]].append((result[1],int(result[2])))
            if result[1] not in NETWORK:
                NETWORK[result[1]] = [(result[0], int(result[2]))]
            else:
                NETWORK[result[1]].append((result[0], int(result[2])))


def get_current_node(min_cost, notVisited):
    '''
    This function is a priavte method for dijkstra.
    :param min_cost is the min_cost dictionary
    :param notVisited is the set for not visited node
    :return: the not-visited node which has the min cost currently
    '''
    cost = float('Inf')
    min_node = None
    for key in min_cost:
        if key in notVisited:
            if min_cost[key][0] < cost:
                cost = min_cost[key][0]
                min_node = key
    if min_node == None:
        min_node = list(notVisited)[0]
    return min_node


def dijsktra():
    '''
    This function is to to generate a min cost path for a given start node and update the forwarding table
    :param startNode means the given start node
    :return: None
    '''
    global forwarding_table
    start_ip = util.get_local_ipv4_address()
    # Initialize visited list
    notVisited = set()
    for i in NETWORK:
        notVisited.add(i)
    # Initalize min_cost list
    min_cost = {}
    pre_node = None
    # the value of min_cost is a editable list, the first element is min_cost, the second is previous node
    for i in NETWORK:
        if not i == start_ip:
            min_cost[i] = [float('inf'),pre_node]
        else:
            min_cost[i] = [0,pre_node]
    # do dijsktra
    while notVisited:
        current_node = get_current_node(min_cost, notVisited)
        notVisited.remove(current_node)
        neighbor_set = NETWORK[current_node]
        for key in neighbor_set:
            if key[0] in notVisited:
                if min_cost[current_node][0] + key[1] < min_cost[key[0]][0]:
                    min_cost[key[0]][0] = min_cost[current_node][0] +key[1]
                    min_cost[key[0]][1] = current_node
    for key in min_cost:
        value = min_cost[key]
        path = []
        if value[0] == 0:
            path.append(key)
        # find path by back propagation
        while value[1] != None:
            path.append(value[1])
            value = min_cost[value[1]]
        path.reverse()
        path.append(key)
        if len(path)>1:
            forwarding_table[key] = path[1]
        elif len(path)==1:
            forwarding_table[key] = path[0]
        else:
            forwarding_table[key] = key
    print('pass')

def send(datagram, dst_ip, nat = False): # todo read from file
    '''
    This send method is for both end router and router in core
    :param datagram: sending content
    :param dst_ip: destination ip
    :param nat: a tune to remark current send is for end router or core router
    :return: None
    '''

    # [for present]
    import json
    with open('show.json', 'r') as f:
        dict_ = json.loads(f.read())
    nat = dict_['nat']
    if nat == 'True':
        nat = True
    elif nat == 'False':
        nat = False
    else:
        raise Exception("Wrong show.json")

    # [end]
    if nat:
        # for end router, do NAT first
        datagram = NAT(datagram,'out')
    dst_ip = forwarding_table[dst_ip]
    linklayer.sendto(util.ip2mac(dst_ip),datagram)


def unpack(datagram):
    '''
    Unpack the ip datagram into ip part and transport layer part
    :param datagram: given ip datagram
    :return: ip object and transport object
    '''
    network = IP.unpack(datagram)
    # check the ttl
    if network.ttl:
        network.ttl -= 1
    else:
        # ICMP send back:type=11 code=0 TTL expired in transit
        ICMP.ttl_expired(WAN_ip, network.src_ip)
        return None, None, ACTION_RETURN
    # # check host
    # if not is_reachable_host(network.dst_ip):
    #     # ICMP send back:type=3 code=1 Destination host unreachable
    #     network, transport = generate_ICMP(network, type=3, code=1)
    #     return network, transport

    # unpack into different format according to protocol type
    if network.protocol == PROTOCOL_UDP:
        transport = UDP.unpack(network.segment)
    elif network.protocol == PROTOCOL_TCP:
        transport = TCP.unpack(network.segment)
    elif network.protocol == PROTOCOL_ICMP:
        transport = ICMP.unpack(network.segment)
    else:
        # ICMP send back:type=3 code=2 Destination protocol unreachable
        ICMP.protocol_unreachable(network.dst_ip, network.src_ip)
        return None, None, ACTION_RETURN
    # # check port
    # if (network.protocol==PROTOCOL_UDP or network.protocol==PROTOCOL_TCP) \
    #         and (not is_reachable_port(network.dst_ip, transport.dst_port)):
    #     # ICMP send back:type=3 code=3 Destination port unreachable
    #     network, transport = generate_ICMP(network, type=3, code=3)
    #     return network, transport
    return network, transport, ACTION_PUSH


def pack(network, transport):
    '''
    Pack network part and transport part together
    Based on the protocol info, pack into different type and update ip segement part
    repack into a new datagram
    :param network: ip object
    :param transport: unknown type transport layer object
    :return: new ip datagram
    '''
    network.segment = transport.pack()
    return network.pack()


def NAT(datagram,t):
    '''
    This method is for update NAT ip and port info of current datagram
    :param datagram: un NAT datagram
    :param t: the type of NAT: into LAN or out LAN
    :return: updated datagram
    '''
    network, transport, _ = unpack(datagram)
    # Case1: current datagram is sending out of LAN, extract the WAN ip and assigned port,
    # if current key not exist, update it into the NAT_out table
    if t == "out" :
        if (network.src_ip, transport.src_port) not in NAT_out:
            update_table(network.src_ip, transport.src_port)
        network.src_ip, transport.src_port = NAT_out[(network.src_ip, transport.src_port)]
    # Case2: current datagram is sending into LAN, extract the LAN ip and corresponding port,
    elif t == 'in' :
        network.dst_ip, transport.dst_port = NAT_in[(network.dst_ip, transport.dst_port)]
    # pack into new datagram
    new_datagram = pack(network, transport)
    return new_datagram


def update_table(src_ip, src_port):
    '''
    A method for updating NAT table
    :param src_ip: raw source ip
    :param src_port: raw source port
    :return: None
    '''
    global NAT_out,NAT_in
    new_port = random.randrange(65535)
    # assign a new port number
    while (WAN_ip, new_port) in NAT_in:
        new_port = random.randrange(65535)
    # update both NAT_in and NAT_out
    NAT_out[(src_ip, src_port)] = (WAN_ip, new_port)
    NAT_in[(WAN_ip, new_port)] = (src_ip, src_port)


read("NetworkLayer/networks.txt")
dijsktra()


def callback(frame):
    '''
    The action after receiving datagram from link layer.
    First unpack datagram
    Case1: if the outside datagram is received by destination end router,
    it will first do NAT and update datgram, then push upward
    Case2; if the internal datagram is received by destination,
    no need for NAT, directly push upward
    Case3: if this datagram is received in core routers,
    find the next forwarding hop ip and convert into mac,
    then send it by linklayer
    :param frame: received datagram from linklayer
    :return: None
    '''
    network, transport, action = unpack(frame)
    if action == ACTION_PUSH:
        if network.dst_ip == util.get_local_ipv4_address():
            IP.push(frame)
        elif network.dst_ip in forwarding_table:
            forwarding_ip = forwarding_table[network.dst_ip]
            if forwarding_ip != WAN_ip:
                dst_ip = forwarding_ip
                
            else:
                dst_ip = network.dst_ip
            if dst_ip != forwarding_ip:
                print('forwaring to', forwarding_table[network.dst_ip])
            dst_mac = util.ip2mac(dst_ip)
            linklayer.sendto(dst_mac, frame)
        elif (network.dst_ip, transport.dst_port) in NAT_in :
            network.dst_ip, transport.dst_port = NAT_in[(network.dst_ip, transport.dst_port)]
            frame = pack(network, transport)
            IP.push(frame)
        else:
            ICMP.host_unreachable(WAN_ip, network.src_ip)

linklayer = LinkLayer(callback)


# def is_reachable_host(dst_ip):
#     '''
#     Private method for check if the current dst_ip is legal
#     :param dst_ip: dst_ip
#     :return: boolean
#     '''
#     ip_list = [util.get_local_ipv4_address()]
#     for ele in NAT_in.keys():
#         ip_list.append(ele[0])
#     if dst_ip not in forwarding_table.values() or ip_list:
#         return False
#     return True