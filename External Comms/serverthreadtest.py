# from socket import *
# import json
# import threading


# class Relay_Server(threading.Thread):
#     def __init__(self, ip, port, group) -> None:
#         self.relay_ip = gethostbyname(ip)
#         self.relay_port = port
#         self.group = group
#         self.relaySocket = socket(AF_INET, SOCK_STREAM)
#         self.relaySocket.bind((self.relay_ip, self.relay_port))
#         self.relaySocket.listen(5)
#         print('Relay Server started on', self.relay_ip, self.relay_port)
    
#     def run(self):
#         connectionSocket, addr = self.relaySocket.accept()
#         print('Connected to', addr)
#         while True:
#             try:   
#                 message = connectionSocket.recv(1024)
#                 print(message)
#                 connectionSocket.send(message)
#             except:
#                 print('Error')
#                 connectionSocket.close()
    
#     def send(self, message):
#         pass


# class Relay_Client(threading.thread):
#     def __init__(self, ip, port) -> None:
#         self.relay_ip = gethostbyname(ip)
#         self.relay_port = port
#         self.relaySocket = socket(AF_INET, SOCK_STREAM)
#         self.relaySocket.connect((self.relay_ip, self.relay_port))
#         print('Connected to Relay Server', self.relay_ip, self.relay_port)


# # serverName = gethostbyname('192.168.95.219')
#     def send(self, message):
#         self.relaySocket.send(message)
#         print('Sent message to Relay Server', message)


# def main():
#     relay_client = Relay_Client('localhost', 11000)
#     relay_client.send('Hello World'.encode())


# r = Relay_Server('localhost', 11000, None)
# r.run()




import socket
import threading
import socketserver
from multiprocessing import Queue

q = Queue()

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = str(self.request.recv(1024), 'ascii')
        cur_thread = threading.current_thread()
        response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
        q.put(data)
        self.request.sendall(response)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def client(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        sock.sendall(bytes(message, 'ascii'))
        response = str(sock.recv(1024), 'ascii')
        print("Received: {}".format(response))

if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "localhost", 0

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    with server:
        ip, port = server.server_address

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()
        print("Server loop running in thread:", server_thread.name)

        for i in range(100):
            client(ip, port, "Hello World" + str(i))
            # client(ip, port, "Hello World 2")
            # client(ip, port, "Hello World 3")

        while not q.empty():
            print(q.get())

        server.shutdown()