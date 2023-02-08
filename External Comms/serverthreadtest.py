# # from socket import *
# # import json
# # import threading


# # class Relay_Server(threading.Thread):
# #     def __init__(self, ip, port, group) -> None:
# #         self.relay_ip = gethostbyname(ip)
# #         self.relay_port = port
# #         self.group = group
# #         self.relaySocket = socket(AF_INET, SOCK_STREAM)
# #         self.relaySocket.bind((self.relay_ip, self.relay_port))
# #         self.relaySocket.listen(5)
# #         print('Relay Server started on', self.relay_ip, self.relay_port)
    
# #     def run(self):
# #         connectionSocket, addr = self.relaySocket.accept()
# #         print('Connected to', addr)
# #         while True:
# #             try:   
# #                 message = connectionSocket.recv(1024)
# #                 print(message)
# #                 connectionSocket.send(message)
# #             except:
# #                 print('Error')
# #                 connectionSocket.close()
    
# #     def send(self, message):
# #         pass


# # class Relay_Client(threading.thread):
# #     def __init__(self, ip, port) -> None:
# #         self.relay_ip = gethostbyname(ip)
# #         self.relay_port = port
# #         self.relaySocket = socket(AF_INET, SOCK_STREAM)
# #         self.relaySocket.connect((self.relay_ip, self.relay_port))
# #         print('Connected to Relay Server', self.relay_ip, self.relay_port)


# # # serverName = gethostbyname('192.168.95.219')
# #     def send(self, message):
# #         self.relaySocket.send(message)
# #         print('Sent message to Relay Server', message)


# # def main():
# #     relay_client = Relay_Client('localhost', 11000)
# #     relay_client.send('Hello World'.encode())


# # r = Relay_Server('localhost', 11000, None)
# # r.run()




import socket
import threading
import socketserver
from multiprocessing import Queue
import paho.mqtt.client as mqtt
import time
import json

q = Queue()

class Relay_Server(socketserver.BaseRequestHandler):

    def handle(self):
        cur_thread = threading.current_thread()
        while True:
            data = str(self.request.recv(1024), 'ascii')
            print("{} wrote:".format(self.client_address), data)
            response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
            q.put(data)
            self.request.sendall(response)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

# MQTT Client to send data to AWS IOT Core
class MQTT_Client(threading.Thread):
    def __init__(self, topic, client_id, group) -> None:
        self.topic = topic
        self.client_id = client_id
        self.group = group
        self.client = mqtt.Client(client_id)
        self.client.connect("test.mosquitto.org", 1883, 60)
        print('MQTT Client started on', self.client_id)
        self.client.subscribe(self.topic)
    
    def publish(self, message):
        self.client.publish(self.topic, message)
        print('Published message to', self.topic, message)
    
    def receive(self, client, userdata, message):
        print("Received message from", message.topic, message.payload)


if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "localhost", 11000
    server = ThreadedTCPServer((HOST, PORT), Relay_Server)
    with server:
        ip, port = server.server_address
        f = open('test.json')
        j = json.load(f)
        mqtt = MQTT_Client('test/cg4002', 'testpc', 2)
        mqtt.client.on_message = mqtt.receive

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()
        print("Server loop running in thread:", server_thread.name)
        for _ in range(3):
            mqtt.publish(json.dumps(j))
            time.sleep(1)
        mqtt.client.loop_forever()
        # for i in range(100):
        #     client(ip, port, "Hello World" + str(i))
        #     # client(ip, port, "Hello World 2")
        #     # client(ip, port, "Hello World 3")



        while not q.empty():
            print(q.get())

        time.sleep(100)
        server.shutdown()



# # Ultra96 Server
# from socket import *
# from Crypto import Random
# from Crypto.Cipher import AES
# from Crypto.Util.Padding import pad, unpad
# import base64
# import multiprocessing
# from multiprocessing import Process, Queue
# import json
# import paho.mqtt.client as mqtt
# import time
# import threading

# ai_queue = Queue()
# client_queue = Queue()
# viz_queue = Queue()



# class Relay_Server(threading.Thread):
#     def __init__(self, ip, port) -> None:
#         super().__init__()
#         self.relay_ip = gethostbyname(ip)
#         self.relay_port = port
#         self.relaySocket = socket(AF_INET, SOCK_STREAM)
#         self.relaySocket.bind((self.relay_ip, self.relay_port))
#         print('Relay Server started on', self.relay_ip, self.relay_port)
    
#     def handle(self):
#         print("Waiting for connection...")
#         self.relaySocket.listen()
#         self.connectionSocket, self.addr = self.relaySocket.accept()
#         print('Connected to', self.addr)
        
#     def receive(self):
#             try:
#                 message = self.connectionSocket.recv(1024)
#                 print(message)
#                 self.connectionSocket.send(message)
#             except:
#                 print('Error')
#                 self.connectionSocket.close()

#     def run(self):
#         self.relaySocket.listen()
#         while True:
#             self.connectionSocket, self.addr = self.relaySocket.accept()
#             thread = threading.Thread(target=self.handle, args=(self.connectionSocket, self.addr))

