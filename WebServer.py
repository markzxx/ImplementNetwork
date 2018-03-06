# Import socket module
from mysocket import *
from LinkLayer import util
#I want to get ip address automatically rather than write it in code
#This function setup a UDP connection to a dns server, and get ip address from the head of protocol
# def get_host_ip():
#     try:
#         s = socket(AF_INET, SOCK_DGRAM)
#         s.connect(('114.114.114.114', 80))
#         ip = s.getsockname()[0]
#     finally:
#         s.close()
#     return ip

ip_addr = util.get_local_ipv4_address()
port = 80
serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.bind((ip_addr,port))
serverSocket.listen(1)
root=""
while True:
    print("Ready to serve, ip:{}, port:{}".format(ip_addr,port))
    connectionSocket, addr = serverSocket.accept()

    try:
        request_text = connectionSocket.recv(2048).decode()
        request_head = request_text.split()
        #split the request, the first part is method, the secnod is the path
        #check if the method is get or not
        if request_head and request_head[0] == "GET":
            path = request_head[1][1:]
            print(path)
            #open the file from path in binary, whatever type of file it is
            with open(root+path, 'rb') as f:
                header = b"HTTP/1.1 200 OK\r\n\r\n"
                content = f.read()
        else:
            #if method is not get, just retrun 200 OK tells client server is online
            header = b"HTTP/1.1 200 OK\r\n\r\n"

    except IOError:
        # Send HTTP response message for file not found
        header = b"HTTP/1.1 404 Not Found\r\n\r\n"
        content = b"<html><body><h1>404 Not Found</h1><body><html>"

    print(header)
    #send header and coontent , they are bytes, so need not encode
    connectionSocket.send(header+content)
    connectionSocket.close()