from mysocket import *
from LinkLayer import util
ip = util.get_local_ipv4_address()
port = 5000
local_address = (ip, port)
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(local_address)
serverSocket.listen(1)
clientSocket, address = serverSocket.accept()
count = 0
while 1:
    raw_message = clientSocket.recv(2048)
    clientSocket.send(("response %d"%count).encode())
    print("\n---------------\n", raw_message.decode(), "\n---------------\n")
    count += 1
