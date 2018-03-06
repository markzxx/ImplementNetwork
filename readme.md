# Implement Network

## Structure of Files

```
.
├── Exceptions.py
├── ICMP.py
├── IP.py
├── LinkLayer
│   ├── __init__.py
│   ├── error.py
│   ├── ether.py
│   └── util
│       ├── __init__.py
│       ├── frame.py
│       └── ip_mac.py
├── NetworkLayer
│   ├── __init__.py
│   └── networks.txt
├── Router.py
├── TCP.py
├── TCPsocket.py
├── UDP.py
├── UDPsocket.py
├── mysocket.py
└── rout.py
```

## dependency

- python3.6
	- struct
	- threading
	- os
	- time
	- random
	- urllib
	- json

## Usage

We build mysocket the same shape of socket. It provide interfaces of

- `bind(local_address, remote_address = None)`
	bind ip and address for future use.
- `close()`
	close socket.
- `listen()`
	if the socket is build for TCP connection, it can listen.
- `accept()`
	if the socket is listening, it can accpet a client. If a client is acccept, a new mysocket with connection to the client is returned.
- `send(data, flags = None)`
	if the socket is built for TCP connection and the connection is eatablished. You can call the method to send data to the remote end.
- `sendto(data, flags = None)`
	if the socket is built for UDP connection, you can call this method to send data to specified address.
- `recv(buffersize)`
	if the socket is built for TCP conenction, you can receive data. The method will be blocked if there is no data in buffer, and return until it has data in buffer.
- `recvfrom(buffersize)`
	if the socket is built for UDP connection, you can call this method to retrive data.

Here is an example code.

__TCP_server_demo.py__:
```python
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
```

__TCP_client_demo.py__:
```python
from mysocket import *
from LinkLayer import util
ip = util.get_local_ipv4_address()
port = 5000
local_address = (ip, port)
remote_address = ('10.21.108.47', 5000)
ClientSocket = socket(AF_INET, SOCK_STREAM)
ClientSocket.bind(local_address)
ClientSocket.connect(remote_address)
for i in range(10):
    ClientSocket.send("{}".format(i).encode())
    raw_message = ClientSocket.recv(2048)
    print("\n---------------\n", raw_message.decode(), "\n----------------\n")
```


We also provide more test files in this [github page](https://github.com/BorisChenCZY/ImplementTheNetwork)

You can find them of names:

- `WechatServer.py`
	UDP chat server.

- `WechatClient.py`
	UDP chat client.

- `icmp_demo.py`
	ICMP test


## MIT License

MIT License

Copyright (c) 2018 Xinxun Zeng, Shiqi Zhang, Zhenyu Chen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
