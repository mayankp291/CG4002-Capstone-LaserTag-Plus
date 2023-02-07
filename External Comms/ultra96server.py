# Ultra96 Server
from socket import *
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import multiprocessing
from multiprocessing import Process, Queue
import json
import paho.mqtt.client as mqtt
import time

ai_queue = Queue()
client_queue = Queue()
viz_queue = Queue()



class Relay_Server(Process):
    def __init__(self, ip, port, group) -> None:
        self.relay_ip = gethostbyname(ip)
        self.relay_port = port
        self.group = group
        self.relaySocket = socket(AF_INET, SOCK_STREAM)
        self.relaySocket.bind((self.relay_ip, self.relay_port))
        self.relaySocket.listen(5)
        print('Relay Server started on', self.relay_ip, self.relay_port)
    
    def run(self):
        while True:
            connectionSocket, addr = self.relaySocket.accept()
            print('Connected to', addr)
            message = connectionSocket.recv(1024)
            print(message)
            connectionSocket.close()
    
    def send(self, message):
        pass

    
# MQTT Client to send data to AWS IOT Core
class MQTT_Client(Process):
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
        def on_message(client, userdata, message):
            print("Received message from", message.topic, message.payload)
        


class Evaluation_Client(Process):
    
    IV = b'PLSPLSPLSPLSWORK'
    KEY = b'PLSPLSPLSPLSWORK'

    def __init__(self, ip, port, group) -> None:
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
    eval_client = Evaluation_Client('localhost', 11000, 2)
    f = open('test.json')
    j = json.load(f)
    # for _ in range(10):
    #     eval_client.send(json.dumps(j))
    #     eval_client.receive()

    mqtt = MQTT_Client('test/cg4002', 'testpc', 2)
    mqtt.client.on_message = mqtt.receive
    for _ in range(3):
        mqtt.publish(json.dumps(j))
        time.sleep(1)
    mqtt.client.loop_forever()

if __name__ == "__main__":
    main()