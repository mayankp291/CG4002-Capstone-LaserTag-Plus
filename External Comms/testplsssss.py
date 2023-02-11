# import threading
 
# class c1(threading.Thread) :
#     def run(self) :
#         for _ in range (2) :
#             print(threading.currentThread().getName())
# obj= c1(name='Hello')
# obj1= c1(name='Bye')
# obj.start()
# obj1.start()

import socket

def client(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        sock.sendall(bytes(message, 'ascii'))
        response = str(sock.recv(1024), 'ascii')
        print("Received: {}".format(response))


for i in range(100):
    client("localhost", 11000, "Hello World" + str(i))
    # client(ip, port, "Hello World 2")
    # client(ip, port, "Hello World 3")