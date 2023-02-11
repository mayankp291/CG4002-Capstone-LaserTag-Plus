# Ultra96 Server
from socket import *
import socketserver
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import multiprocessing
from multiprocessing import Process, Queue
import json
import paho.mqtt.client as mqtt
import time
import threading

client_queue = Queue()
viz_queue = Queue()


# TCP Server to receive data from the Relay Laptops
class Relay_Server(socketserver.BaseRequestHandler):
    def handle(self):
        cur_thread = threading.current_thread()
        while True:
            data = self.request.recv(1024).decode('utf-8')
            print("{} wrote:".format(self.client_address), data)
            # response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
            response = "{}: {}".format(cur_thread.name, data)
            # q.put(data)
            self.request.sendall(response.encode('utf-8'))

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
        
# Client to send data to the Evaluation Server
class Evaluation_Client(threading.Thread):
    
    IV = b'PLSPLSPLSPLSWORK'
    KEY = b'PLSPLSPLSPLSWORK'

    def __init__(self, ip, port, group) -> None:
        super().__init__()
        self.eval_ip = gethostbyname(ip)
        self.eval_port = port
        self.group = group
        
        try:
            self.clientSocket = socket(AF_INET, SOCK_STREAM)
            self.clientSocket.connect((self.eval_ip, self.eval_port))
            print('Connected to Evaluation Server', self.eval_ip, self.eval_port)
        except:
            print('Failed to connect to Evaluation Server', self.eval_ip, self.eval_port)
            self.clientSocket = None
    

    def run(self):
        f = open('test.json')
        j = json.load(f)
        for _ in range(10):
            self.send(json.dumps(j))
            self.receive()   
        self.close()


    @staticmethod
    def AES_Cipher():
        return AES.new(Evaluation_Client.KEY, AES.MODE_CBC, Evaluation_Client.IV)

    def send(self, message):
        if self.clientSocket is not None:
            try:
                encryted_message = self.encrypt_AES(message)
                len_info = str(len(encryted_message)) + "_"
                # send len_
                self.clientSocket.send(len_info.encode("utf-8"))
                self.clientSocket.send(encryted_message)
                print('Sent message to Evaluation Server', self.eval_ip, self.eval_port, message)
            except:
                print('Failed to send message to Evaluation Server', self.eval_ip, self.eval_port, message)
                self.clientSocket = None
    
    def receive(self):
        if self.clientSocket is not None:
            try:
                recv_message = self.clientSocket.recv(2048).decode("utf-8")
                print('Received message from Evaluation Server', self.eval_ip, self.eval_port, recv_message)
            except:
                print('Failed to receive message from Evaluation Server', self.eval_ip, self.eval_port)
                self.clientSocket = None

    def close(self):
        if self.clientSocket is not None:
            self.clientSocket.close()
            print('Closed connection to Evaluation Server', self.eval_ip, self.eval_port)
    
    def encrypt_AES(self, string):    
        msg = pad(string.encode("utf-8"), AES.block_size)
        encrypted_text = Evaluation_Client.AES_Cipher().encrypt(msg)
        ciphertext = base64.b64encode(self.IV + encrypted_text)
        return ciphertext


def main():
    eval_client = Evaluation_Client('localhost', 11001, 2)
    eval_client.daemon = True
    eval_client.start()

    HOST, PORT = "localhost", 11000
    server = ThreadedTCPServer((HOST, PORT), Relay_Server)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("Server loop running in thread:", server_thread.name)

    mqtt = MQTT_Client('test/cg4002', 'testpc', 2)
    mqtt.client.on_message = mqtt.receive
    f = open('test.json')
    j = json.load(f)
    for _ in range(3):
        mqtt.publish(json.dumps(j))
        time.sleep(1)
    mqtt.client.loop_forever()

if __name__ == "__main__":
    main()