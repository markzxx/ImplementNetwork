AF_INET = 2
SOCK_STREAM = 1
RECEIVED_BUFFER_SIZE = 1048576  # todo discuss the buffer size, currently 1GMb

import os
import random
import threading
import time
from pprint import pprint
import IP
from Exceptions import *
from TCP import *

buffer_list = {
    'listening': {},  # when server is listening, the key of the dict inside is the port of server.
    'connected': {
        'objects': {}
    # objcts is a dict that stores every connected tcpSocket object as its value while their remote_address is the key
    },  # when sockey (client or user) is connected, the key of the dict inside is the address of remote address
    'connecting': {},  # when client is connecting, put self here, the remote address is key, list is value
}

port_list = []
local_ip = None


class TCPsocket():
    # status
    CLOSED = 0
    LISTEN = 1
    SYN_RCVD = 2
    ESTABLISHED = 3
    CLOSE_WAIT = 4
    LAST_ACK = 5
    SYN_SENT = 6
    FIN_WAIT_1 = 7
    FIN_WAIT_2 = 8
    TIME_WAIT = 9

    # const
    TIME_INTERVAL = 100

    def __init__(self, local_address, remote_address=None, server_isn=None, client_isn=None, sample_RTT = None):
        self.__sent_but_not_acked = []  # a list of tuple, in the order of sending order. Each tuple contain a wanting ack number and data(NOT TCP OBJECT)
        self.__sample_RTT_to_record = {}  # a dict, the key of which is the wanting ack number, the value of which is the start_time (or None, indicating this message won’t count to sample_RTT).
        self.__sample_RTT = sample_RTT  # double
        self.__estimated_RTT = sample_RTT  # double
        self.__dev_RTT = 0  # double
        self.__window_buffer = []  # a list of tuples, a tuple is in the format of (sequence_number, data)
        self.__received_buffer = b''  # bytes, used to store complete infomation, which is also in order.
        self.__ack_to_be_sent = []
        self.__window_size = 5000
        self.__segment_size = 500
        self.__local_address = local_address
        self.__is_time_out = False  # init is_timeout
        self.__send_buffer = b''
        self.__time_out = 0  # todo init timeout
        self.__timer = threading.Thread()
        self.__timer_pid = 0  # helper variable for timer
        self.__duplicate_ack = 0  # init duplicate ack number
        local_ip = local_address[0]

        if server_isn:  # if the socket is build by server
            # pass sequence number and last_acked_number
            self.__next_sequence_number = server_isn
            self.__last_ack_received = server_isn  # SendBase
            self.__last_acked_sent = client_isn

            # init remote address and set up ip layer
            self.__remote_address = remote_address
            self.__ip = IP.IP(IP.PROTOCOL_TCP, self.__local_address[0], self.__remote_address[0])

            # start sending process
            self.__sending_process = threading.Thread(target=self._sending_thread)
            self.__sending_process.start()

            self.__time_out = self._get_new_timeout()




        else:
            self.__next_sequence_number = random.randint(0, 2147483645)

    def listen(self, backlog=None):
        """
                        listen([backlog])

                        Enable a server to accept connections.  If backlog is specified, it must be
                        at least 0 (if it is lower, it is set to 0); it specifies the number of
                        unaccepted connections that the system will allow before refusing new
                        connections. If not specified, a default reasonable value is chosen.
                        """
        if not self.__local_address:
            raise AddressNotSpecified("Did you bind address for this socket?")
        if self.__local_address[1] in buffer_list.keys():
            raise PortAlreadyInUse("Port is already in use.")

        # print('start listening')
        # open buffer for listening
        buffer_list['listening'][self.__local_address[1]] = {'queue': []}
        # print('create buffer_list')
        # print(buffer_list)

        # set up ip layer
        self.__ip = IP.IP(IP.PROTOCOL_TCP, self.__local_address[0])

    def accept(self):
        """accept() -> address tuple, server_isn int

        Wait for an incoming connection.  Return a new socket
        representing the connection, and the address of the client.
        For IP sockets, the address info is a pair (hostaddr, port).
        """
        # fd, addr = self._accept()
        # If our type has the SOCK_NONBLOCK flag, we shouldn't pass it onto the
        # new socket. We do not currently allow passing SOCK_NONBLOCK to
        # accept4, so the returned socket is always blocking.
        # type = self.type & ~globals().get("SOCK_NONBLOCK", 0)
        # sock = socket(self.family, type, self.proto, fileno=fd)
        # Issue #7995: if no default timeout is set and the listening
        # socket had a (non-zero) timeout, force the new socket in blocking
        # mode to override platform-specific socket flags inheritance.
        # if getdefaulttimeout() is None and self.gettimeout():
        #     sock.setblocking(True)
        # return address, server_isn

        # if not self.__address:
        #     raise AddressNotSpecified("Did you bind address for this socket?")

        # wait until one connected
        while buffer_list['listening'][self.__local_address[1]]['queue'] == []:
            continue

        # retrive first handshake
        data, (remote_ip, remote_port) = buffer_list['listening'][self.__local_address[1]]['queue'].pop()
        tcp = TCP()
        tcp.from_bytes(data)
        if not (tcp.SYN == 1 and tcp.ACK == 0):
            # print("wrong tcp package received, it's not the first handshake")
            return
        client_isn = tcp.sequence_number
        print('first handshake received')

        # reformat remote_address
        address = (remote_ip, tcp.src_port)

        # generate a inital server_isn
        server_isn = random.randint(0, 2147483645)

        # build a tcp with server_isn and client_isn + 1
        tcp = TCP()
        tcp.build(type=tcp.SEND_SYNACK,
                  src_port=self.__local_address[1],
                  dst_port=address[1],
                  sequence_number=server_isn,
                  acknowledgement_number=client_isn + 1)

        # send the second handshake and register a place for handshake
        tmp_ip = IP.IP(IP.PROTOCOL_TCP, self.__local_address[0], remote_ip)
        tmp_ip.send(bytes(tcp))
        buffer_list['connecting'][address] = []
        print('second handshake sent, waiting for the third handshake')

        # record the first time of send package
        fisrt_pacakge_sent_time = time.time()

        # wait until third handshake appear
        send_send_start_time = time.time()
        flag_3 = True
        flag_6 = False
        flag_12 = False
        while buffer_list['connecting'][address] == []:
            if flag_3 and (time.time() - send_send_start_time >= 2):
                print('waiting second hand time out, wait another 6s')
                tmp_ip.send(bytes(tcp))
                send_send_start_time = time.time()
                flag_3 = False
                flag_6 = True
                send_send_start_time =time.time()
            elif flag_6 and (time.time() - send_send_start_time >= 2):
                print('waiting second hand time out, wait another 12s')
                tmp_ip.send(bytes(tcp))
                send_send_start_time = time.time()
                flag_6 = False
                flag_12 = True
                send_send_start_time =time.time()
            elif flag_12 and (time.time() - send_send_start_time >= 2):
                print('waiting second hand time out, wait another 24s')
                tmp_ip.send(bytes(tcp))
                flag_6 = False
                flag_12 = False
                send_send_start_time =time.time()
            elif (time.time() - send_send_start_time >= 4):
                print('waiting second hand time out, wait another 6s')
                print('break')
                return

            continue

        # record the time of receiving second package
        self.__sample_RTT = time.time() - fisrt_pacakge_sent_time
        self.__estimated_RTT = self.__sample_RTT
        print('first sample RTT generated, it\'s {}'.format(self.__sample_RTT))

        # retrive the third handshake
        data, address = buffer_list['connecting'][address].pop()
        tcp = TCP()
        tcp.from_bytes(data)
        print('third handshake retrived')

        # check third handshake
        if not (tcp.sequence_number == client_isn + 1 and tcp.acknowledgement_number == server_isn + 1):
            print(
                'SYN {}, ACK{}, tcp.sequencenumber({}) ?= client_isn({}), tcp.acknowledgement_number({}) ?= server_isn({})'.format(
                    tcp.SYN, tcp.ACK, tcp.sequence_number, client_isn + 1, tcp.acknowledgement_number, server_isn + 1))
            print("wrong tcp package received, it's not the correct third handshake")
            return

        # update server_isn
        server_isn += 1

        # open a place for the newly connected socket
        buffer_list['connected'][address] = []

        # delete the original space
        buffer_list['connecting'].pop(address)

        # add data to the buffer if any

        # buffer_list['connected'][address].append(tcp.data)

        # Build a new tcpSocket
        tcpSocket = TCPsocket(self.__local_address, address, server_isn, client_isn + 1, self.__sample_RTT)

        # put the conneceted object in buffer
        buffer_list['connected']['objects'][address] = tcpSocket

        # add data if any
        if tcp.data != b'':
            tcpSocket._add_data(tcp.data)
        print('done with accept, returned address and server_isn')

        return address, tcpSocket

    def recv(self, buffersize, flags=None):  # real signature unknown; restored from __doc__
        """
        recv(buffersize[, flags]) -> data

        Receive up to buffersize bytes from the socket.  For the optional flags
        argument, see the Unix manual.  When no data is available, block until
        at least one byte is available or until the remote end is closed.  When
        the remote end is closed and all data is read, return the empty string.
        """
        while not self.__received_buffer:
            continue

        return_data = self.__received_buffer[:buffersize]
        self.__received_buffer = self.__received_buffer[buffersize:]
        return return_data

    def send(self, data, flags=None):  # real signature unknown; restored from __doc__
        """
                send(data[, flags]) -> count

                Send a data string to the socket.  For the optional flags
                argument, see the Unix manual.  Return the number of bytes
                sent; this may be less than len(data) if the network is busy.
                """

        # if self.__type != SOCK_STREAM:
        #     raise TypeNotRightException("type is not correct, is the socket assigned TCP protocol?")
        # NextSeqNum: int = 0

        self.__send_buffer += data

    def _sending_thread(self):
        # build empty tcp object
        tcp = TCP()
        tcp.build(type=tcp.SEND_DATA, src_port=self.__local_address[1], dst_port=self.__remote_address[1])
        tcp.sequence_number = self.__next_sequence_number
        tcp.acknowledgement_number = self.__last_acked_sent
        print('built empty tcp object')

        while 1:
            time.sleep(0.2)
            # print('sending thread begin')
            # detect whether there is act_to_be_sent
            if self.__ack_to_be_sent != []:
                tcp.ACK = 1
                tcp.acknowledgement_number = self.__ack_to_be_sent.pop()
                self.__last_acked_sent = tcp.acknowledgement_number
                print(
                    'detect there is ack_to_be_sent({}), added to current tcp object, last_acked_number updated'.format(
                        tcp.acknowledgement_number))

            # check time_out
            if self.__is_time_out:
                print('detect time out')

                # get first send_but_not_acked data in tcp.data
                try:
                    tcp_bytes = self.__sent_but_not_acked[0]


                    tcp = TCP()
                    tcp.from_bytes(tcp_bytes)

                    # modify tcp.sequence_number
                    # tcp.sequence_number = waiting_ack_number - len(tcp.data)

                    # double timeout
                    self.__time_out *= 2

                    if self.__time_out <= 1:
                        self.__time_out = 1

                    # cancel SampleRTT recording for this object
                    self.__sample_RTT_to_record[tcp.sequence_number + len(tcp.data)] = None

                    # Done with here
                    self.__is_time_out = False

                    self.__timer = threading.Thread()
                    self.__timer_pid = None

                    print(self.__time_out)
                except:
                    self.__is_time_out = False

                    self.__timer = threading.Thread()
                    self.__timer_pid = None
            else:
                # print('no timeout detected')

                # calculate the spare room in sent_but_not_acked
                spare_room_in_window = self.__window_size - (self.__next_sequence_number - self.__last_ack_received)

                if self.__send_buffer != b'' and spare_room_in_window != 0:  # specify squence number andNextSeqNum
                    NextSeqNum = self.__next_sequence_number

                    # prepare data
                    data = self.__send_buffer[:self.__segment_size]

                    # delete that data from send_buffer
                    self.__send_buffer = self.__send_buffer[self.__segment_size:]

                    # update tcp object
                    tcp.data = data
                    tcp.sequence_number = NextSeqNum

            # check tcp modified
            if tcp.data != b'' or tcp.ACK == 1:
                # set sequence number
                # tcp.sequence_number = self.__next_sequence_number

                # if data included, update next_sequence_number
                if tcp.data != b'':
                    self.__next_sequence_number += len(data)





                # if the tcp contains data
                if tcp.data != b'':
                    # check the data is first sent or not

                    # add current value to sent_but_not_acked
                    if bytes(tcp) not in self.__sent_but_not_acked:
                        self.__sent_but_not_acked.append(bytes(tcp))

                    if (tcp.sequence_number + len(tcp.data)) not in self.__sample_RTT_to_record.keys():
                        # it's first sent.

                        # record send time
                        send_time = time.time()
                        self.__sample_RTT_to_record[tcp.sequence_number + len(tcp.data)] = send_time
                        # print('----------')
                        # print('record time')
                        # print(self.__sample_RTT_to_record)
                        # print('----------')

                        # check whether there is already a tiemr
                        print('check timer', self.__timer.is_alive())
                        if not self.__timer.is_alive():
                            # there is no timer

                            # calculate a new time_out
                            self.__time_out = self._get_new_timeout()

                            # start a new timer
                            self.__timer = threading.Thread(target=self.__check_time,
                                                            args=(time.time(),
                                                                  self.__time_out))
                            self.__timer.start()
                    else:
                        # it's not first sent

                        # double timeout
                        print('detect not first send message, the sequence_number is {}, the ack_number is {}, content:{}'.format(tcp.sequence_number, tcp.acknowledgement_number, str(tcp)))
                        print(self.__sample_RTT_to_record)
                        self.__time_out *= 2
                        self.__timer = threading.Thread(target=self.__check_time,
                                                        args=(time.time(),
                                                              self.__time_out))
                        self.__timer.start()

                # send tcp object
                self.__ip.send(bytes(tcp))
                print(
                    'send tcp object with \tsequence number {} and \tacknowledge number {}.'.format(tcp.sequence_number,
                                                                                                    tcp.acknowledgement_number))
                print('content', str(tcp))

                # build new tcp object
                tcp = TCP()
                tcp.build(type=tcp.SEND_DATA, src_port=self.__local_address[1], dst_port=self.__remote_address[1])
                tcp.sequence_number = self.__next_sequence_number
                tcp.acknowledgement_number = self.__last_acked_sent
                # print('built empty tcp object')

    def _add_data(self, data):
        tcp = TCP()
        tcp.from_bytes(data)
        # print('retrived data from IP layer')

        # if has ack info
        if tcp.ACK == 1:
            # print("detect ACK info, it's", tcp.acknowledgement_number)
            if tcp.acknowledgement_number == self.__last_ack_received:
                # it's duplicated ack
                self.__duplicate_ack += 1
                print('detect {} duplicated ACK'.format(self.__duplicate_ack))
                if self.__duplicate_ack >= 3:
                    # fast retransmission

                    # stop timer and make timeout to be true
                    self.__timer = threading.Thread()
                    self.__timer_pid = None
                    self.__is_time_out = True
                    print('timer stoped, set timeout to be true, preparing for retransmission')
                    self.__duplicate_ack = 0
            else:
                self.__duplicate_ack = 0
                # it's not duplicated ack
                if tcp.acknowledgement_number > self.__last_ack_received:

                    print('current SendBase {}, updated to {}'.format(self.__last_ack_received,
                                                                      tcp.acknowledgement_number))

                    # update SendBase
                    self.__last_ack_received = tcp.acknowledgement_number
                    self.__next_sequence_number = tcp.acknowledgement_number


                    # calculating a new SampleRTT
                    # print('----------')
                    # print('receive time')
                    # print(self.__sample_RTT_to_record)
                    # print('tcp info:')
                    # print('sequence_number:{}, acknowledgement_number:{}, content:{}'.format(tcp.sequence_number, tcp.acknowledgement_number, str(tcp)))
                    # print('----------')
                    try:
                        self.__sample_RTT = time.time() - self.__sample_RTT_to_record[tcp.acknowledgement_number]
                    except:
                        pass

                    # remove self.__send_but_not_acked objects according to the ack number
                    print('updating sent_but_not_acked list')
                    remove_list = []
                    for tcp_bytes in self.__sent_but_not_acked:
                        tcp_ = TCP()
                        tcp_.from_bytes(tcp_bytes)
                        if tcp_.sequence_number + len(tcp_.data)<= tcp.acknowledgement_number:
                            remove_list.append(tcp_bytes)
                            print('removed waiting_ack_number:{}'.format(tcp_.sequence_number + len(tcp_.data)))
                    for item in remove_list:
                        self.__sent_but_not_acked.remove(item)
                    # print('updated')

                    # check whether a timer is running
                    if self.__timer.is_alive():
                        print('detect a timer still running')

                        # check whether there are still sent_but_not_acked
                        if self.__sent_but_not_acked:
                            print('detect there is still sent_but_not_acked:')
                            print(self.__sent_but_not_acked)
                            print('restart timer')
                            self.__time_out = self._get_new_timeout()
                            # restart timer
                            self.__timer = threading.Thread(target=self.__check_time,
                                                            args=(time.time(), self.__time_out))
                            self.__timer.start()
                        else:
                            # stop timer
                            self.__timer = threading.Thread()
                            self.__timer_pid = None
                            self.__is_time_out = False
                            self.__time_out = self._get_new_timeout()
                            print('no data in sent_but_note_acked, stopped timer')

        # if has data info:
        if tcp.data != b'':
            # check whether it's duplicate data
            if tcp.sequence_number < self.__last_acked_sent:
                print('the sequence_number({}) < last_acked_sent({}), omit it.'.format(tcp.sequence_number,
                                                                                       self.__last_acked_sent))
                # it's duplicate data
                tcp = TCP()
                tcp.build(type = tcp.SEND_ACK, src_port=self.__local_address[1], dst_port=self.__remote_address[1], acknowledgement_number=self.__last_acked_sent)
                print('duplicate data, send ack')
            else:
                # it's not duplicate data

                # put it in self.__window_buffer and sort
                print(tcp.data, 'has added to window buffer')
                self.__window_buffer.append((tcp.sequence_number, tcp.data))
                self.__window_buffer.sort(key=lambda x: x[0])

                # check tmp_buffer in-order data, if any, put it to recv_buffer

                while self.__window_buffer[0][0] == self.__last_acked_sent:
                    # retrive from window_buffer(tmp_buffer)
                    sequence_number, data = self.__window_buffer.pop()

                    # calculate and update last_ack_sent
                    self.__last_acked_sent += len(data)


                    # put data into recv_buffer
                    self.__received_buffer += data
                    print(
                        'put data with sequence_number {} out of tmp_buffer into recv_buffer, updated last_ack_sent, waiting to be sent later'.format(tcp.sequence_number))
                    if len(self.__window_buffer) == 0:
                        break

                # put last_ack_sent to ack_to_be_sent
                self.__ack_to_be_sent.append(self.__last_acked_sent)
                print('not duplicate, send ack', self.__last_acked_sent)


    def connect(self, remote_address):  # real signature unknown; restored from __doc__
        """
        connect(address)

        Connect the socket to a remote address.  For IP sockets, the address
        is a pair (host, port).
        """

        # init remote_address
        self.__remote_address = remote_address

        # connect to IP layer
        print('connecting to IP layer')
        self.__ip = IP.IP(IP.PROTOCOL_TCP, self.__local_address[0], dst_ip=remote_address[0])
        print('connected to IP layer')

        # generate client_isn
        self.__isn = random.randint(0, 2147483645)
        client_isn = self.__isn
        print('generated isn', self.__isn)

        # build a tcp object with SYN
        tcp = TCP()
        tcp.build(type=tcp.SEND_SYN,
                  src_port=self.__local_address[1],
                  dst_port=remote_address[1],
                  sequence_number=self.__isn)

        # sign a space in buffer_list
        buffer_list['connecting'][remote_address] = []

        # sent tcp object
        self.__ip.send(bytes(tcp))
        print('sent tcp object')

        # record first_package_sent_time
        first_package_sent_time = time.time()

        # wait for sencond hanshake
        print('waiting for sencond hanshake')
        star_time = time.time()
        flag_3 = True
        flag_6 = False
        flag_12 = False

        while buffer_list['connecting'][remote_address] == []:
            if flag_3 and time.time() - star_time >= 2:
                print('3s timeout')
                self.__ip.send(bytes(tcp))
                flag_3 = False
                flag_6 = True
                star_time = time.time()
            elif flag_6 and time.time() - star_time >= 2:
                print('6s timeout')
                self.__ip.send(bytes(tcp))
                flag_6 = False
                flag_12 = True
                star_time = time.time()
            elif flag_12 and time.time() - star_time >= 2:
                print('12s timeout')
                self.__ip.send(bytes(tcp))
                flag_12 = False
                star_time = time.time()
            elif time.time() - star_time >= 4:
                print('break')
                return
            continue

        self.status = 'established'
        # record first_package_receive_time
        self.__sample_RTT = time.time() - first_package_sent_time
        self.__estimated_RTT = self.__sample_RTT
        self._get_new_timeout()
        print('fisrt sampleRTT inited, it\'s', self.__sample_RTT)

        # retrive data
        data = buffer_list['connecting'][remote_address].pop()
        print('retrived')

        # parse tcp object
        tcp = TCP()
        tcp.from_bytes(data)

        # check tcp object is right
        if not (tcp.SYN == 1 and tcp.ACK == 1 and tcp.acknowledgement_number == client_isn + 1):
            print('the tcp object is not right. Connect failed')
            return

        # if it's right, update server_isn, client_isn
        server_isn = tcp.sequence_number
        client_isn += 1
        self.__next_sequence_number = client_isn
        print('client_isn sent', client_isn)
        self.__last_ack_received = tcp.acknowledgement_number

        # remove from buffer_list['connecting'], added to buffer_list['connected']
        buffer_list['connecting'].pop(remote_address)
        buffer_list['connected']['objects'][remote_address] = self

        # generate last_ack_sent and update ack_to_be_sent list, last_ack_received
        self.__last_acked_sent = server_isn + 1
        self.__ack_to_be_sent.append(self.__last_acked_sent)

        # start sending thread
        self.__sending_process = threading.Thread(target=self._sending_thread)
        self.__sending_process.start()
        print('connected')



    @staticmethod
    def push(data, remote_ip):
        # print
        # print('[static method]received data from ip, it\'s from', remote_ip)
        tcp = TCP()
        tcp.from_bytes(data)
        # print('current buffer_list is')
        # print(buffer_list)

        # print('src_port is', tcp.src_port, end=' ')
        # print('dst_port is', tcp.dst_port, end=' ')
        # print('content is', str(tcp))

        # print()
        # print basic info
        # names = ['CWR','ECE','URG','ACK','PSH','RST','SYN','FIN']
        # byte = tcp.flag_bits
        # byte = bin(int.from_bytes(byte, 'little'))[2:]
        # print(bytes)
        # for i in range(8):
        #     print("{}:{}".format(names[i], byte[i]))
        #
        # if tcp.SYN == 1 and tcp.ACK != 1:
        #     b
        remote_address = (remote_ip, tcp.src_port)
        if tcp.RST:
            raise ConnectionResetError
        try:
            if tcp.SYN == 1 and tcp.ACK == 1:
                print('detect second handshake')
                try:
                    buffer_list['connecting'][remote_address].append(data)
                except:
                    server_isn = tcp.sequence_number
                    client_isn = tcp.acknowledgement_number
                    remote_port = tcp.src_port
                    local_port = tcp.dst_port
                    tcp = TCP()
                    tcp.sequence_number = client_isn
                    tcp.acknowledgement_number = server_isn
                    tcp.src_port = local_port
                    tcp.dst_port = remote_port
                    tmp_ip = IP.IP(protocol=IP.PROTOCOL_TCP, src_ip=local_ip, dst_ip=remote_ip)
                    print('retransmitted', tcp.sequence_number, tcp.acknowledge_number)
                    print("str", str(tcp))
                    tmp_ip.send(bytes(tcp))

            elif tcp.SYN == 1:
                # it's first handshake
                print('detect first handshake')
                buffer_list['listening'][tcp.dst_port]['queue'].append((data, remote_address))
            else:
                # it's not first handshake

                # self.__last_acked_number = tcp.acknowledgement_number # todo update last_acked_number

                # check whether it's a third handshake
                if remote_address in buffer_list['connected']['objects'].keys():
                    print('detect normal message')
                    # it's not a third handshake
                    # buffer_list['connected'][remote_address].append((data, remote_address))

                    # get tcp object
                    obj = buffer_list['connected']['objects'][remote_address]

                    # let obj add data
                    obj._add_data(data)
                else:
                    # it's a third handshake
                    print('detect third handshake')
                    buffer_list['connecting'][remote_address].append((data, remote_address))
        except:
            local_port = tcp.dst_port
            remote_port = tcp.src_port
            sequence_number = tcp.acknowledgement_number
            acknowledge_number = tcp.sequence_number
            tcp = TCP()
            tcp.RST = 1
            tcp.ACK = 0
            tcp.src_port = local_port
            tcp.dst_port = remote_port
            tcp.sequence_number = sequence_number
            tcp.acknowledgement_number = acknowledge_number
            tmp_ip = IP.IP(protocol=IP.PROTOCOL_TCP, src_ip= local_ip, dst_ip=remote_ip)
            tmp_ip.send(bytes(tcp))


        # print()


    def _get_new_timeout(self):  # todo calculate a new time out
        if not self.__estimated_RTT:
            self.__estimated_RTT = self.__sample_RTT
        if not self.__dev_RTT:
            self.__dev_RTT = 0
        self.__estimated_RTT = 0.85 * self.__estimated_RTT + 0.125 * self.__sample_RTT
        self.__dev_RTT = 0.75 * self.__dev_RTT + 0.25 * abs(self.__sample_RTT - self.__estimated_RTT)
        self.__time_out = self.__estimated_RTT + self.__dev_RTT
        if self.__time_out == 0:
            self.__time_out = 1
        return self.__time_out


    def __check_time(self, start_time, time_interval):
        print('timer start')
        self.__timer_pid = os.getpid()
        pid = os.getpid()
        while 1:
            # print('ticking', time.time(), start_time, time_interval)
            time.sleep(time_interval * 0.1)
            if self.__timer_pid != pid:
                return
            current_time = time.time()
            if current_time - start_time > time_interval:
                self.__is_time_out = True
                self.timer_thread = threading.Thread()
                return

    def close(self):
        try:
            buffer_list['listening'].pop(self.__local_address[1])
        except:
            pass
        try:
            buffer_list['connecting'].pop(self.__remote_address)
        except:
            pass
        try:
            buffer_list['connected']['objects'][self.__remote_address]
        except:
            pass


    def __del__(self):
        pass