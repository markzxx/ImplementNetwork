from TCPsocket import TCPsocket
from UDPsocket import UDPsocket
import UDP
AF_INET = 1
SOCK_STREAM = 1
SOCK_DGRAM = 2

class socket(object):
    def __init__(self, family=AF_INET, type=SOCK_STREAM, proto=0, fileno=None):
        self.family = family
        self.type = type
        self.proto = proto
        self.fileno = fileno
        if self.type == SOCK_DGRAM:
            self.udp_socket = UDPsocket()
        pass
    
    def connect(self, address):
        self.tcp_socket.connect(address)
        
    def colse(self):
        if self.type == SOCK_STREAM:
            self.tcp_socket.close()
        if self.type == SOCK_DGRAM:
            self.udp_socket.close()
        
    def bind(self, local_address, remote_address = None, server_isn = None, client_isn = None):  # real signature unknown; restored from __doc__
        """
        bind(address)
        Bind the socket to a local address.  For IP sockets, the address is a
        pair (host, port); the host must refer to the local host. For raw packet
        sockets the address is a tuple (ifname, proto [,pkttype [,hatype]])
        """
        self.ip = local_address[0]
        self.port = local_address[1]
        local_address = (self.ip, self.port)
        if self.type == SOCK_STREAM:
            if server_isn:
                self.tcp_socket = TCPsocket(local_address, remote_address, server_isn, client_isn)
            else:
                self.tcp_socket = TCPsocket(local_address)
            # self.tcp.bind(address)
        elif self.type == SOCK_DGRAM:
            self.udp_socket = UDPsocket()
            self.udp_socket.bind(local_address)
        pass

    def listen (self, backlog=None):  # real signature unknown; restored from __doc__
        """
        listen([backlog])

        Enable a server to accept connections.  If backlog is specified, it must be
        at least 0 (if it is lower, it is set to 0); it specifies the number of
        unaccepted connections that the system will allow before refusing new
        connections. If not specified, a default reasonable value is chosen.
        """
        self.tcp_socket.listen(backlog)
        pass
    
    def accept(self):
        """accept() -> (socket object, address info)

        Wait for an incoming connection.  Return a new socket
        representing the connection, and the address of the client.
        For IP sockets, the address info is a pair (hostaddr, port).
        """
        while 1:
            try:
                address, tcp_socket = self.tcp_socket.accept()
                break
            except:
                pass
        
        # If our type has the SOCK_NONBLOCK flag, we shouldn't pass it onto the
        # new socket. We do not currently allow passing SOCK_NONBLOCK to
        # accept4, so the returned socket is always blocking.
        sock = socket(self.family, self.type, self.proto)
        sock.tcp_socket = tcp_socket
        # Issue #7995: if no default timeout is set and the listening
        # socket had a (non-zero) timeout, force the new socket in blocking
        # mode to override platform-specific socket flags inheritance.
        return sock, address
       
        

    def send (self, data, flags=None):  # real signature unknown; restored from __doc__
        """
        send(data[, flags]) -> count

        Send a data string to the socket.  For the optional flags
        argument, see the Unix manual.  Return the number of bytes
        sent; this may be less than len(data) if the network is busy.
        """
        self.tcp_socket.send(data)
        pass

    def sendto (self, data, address):  # real signature unknown; NOTE: unreliably restored from __doc__
        """
        sendto(data[, flags], address) -> count

        Like send(data, flags) but allows specifying the destination address.
        For IP sockets, the address is a pair (hostaddr, port).
        """
        self.udp_socket.sendto(data, address)
        pass
    
    def recv (self, buffersize, flags=None):  # real signature unknown; restored from __doc__
        """
        recv(buffersize[, flags]) -> data

        Receive up to buffersize bytes from the socket.  For the optional flags
        argument, see the Unix manual.  When no data is available, block until
        at least one byte is available or until the remote end is closed.  When
        the remote end is closed and all data is read, return the empty string.
        """
        return self.tcp_socket.recv(buffersize)
        pass

    def recvfrom (self, buffersize, flags=None):  # real signature unknown; restored from __doc__
        """
        recvfrom(buffersize[, flags]) -> (data, address info)

        Like recv(buffersize, flags) but also return the sender's address info.
        """
        return self.udp_socket.recvfrom(buffersize)
        pass