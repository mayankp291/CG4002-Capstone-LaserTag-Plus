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
import random


imu_queue = Queue()
action_queue = Queue()
viz_queue = Queue()

player_state = {
    "p1": {
        "hp": 100,
        "action": 'none',
        "bullets": 6,
        "grenades": 2,
        "shield_time": 0,
        "shield_health": 0,
        "num_shield": 3,
        "num_deaths": 0
        }
}

# TCP Server to receive data from the Relay Laptops
class Relay_Server(socketserver.BaseRequestHandler):
    def handle(self):
        cur_thread = threading.current_thread()
        while True:
            data = self.request.recv(1024).decode('utf-8')
            # process data from client
            data = data.strip()
            data = data.split('_')
            length = int(data[0])
            

            if length != len(data[2]):
                print("Error", data)
                print('Error: packet length does not match, packet dropped')
            
            else:
                print("{} wrote:".format(self.client_address), data[2])
                # process incoming data
                imu_queue.put(data[2])
                # if data[1] == 'action' and data[2] != 'none':
                #     client_queue.put(data[2])
                # elif data[1] == 'IMU':
                #     imu_queue.put(data[2])
                # response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
                response = "{}: {}".format(cur_thread.name, data[2])
                # todo add function to change json
                self.request.sendall(response.encode('utf-8'))

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class Game_Engine(threading.Thread):
    def __init__(self):
        super().__init__()
        # imu_queue.put("test")
        # action_queue.put("test")
        # viz_queue.put("test")
    
    def run(self):
        while True:
            if not imu_queue.empty():
                imu_data = imu_queue.get()
                self.AI_random(imu_data)

            if not action_queue.empty():
                action = action_queue.get()
                print("[ACTION]", action)
                if action == 'reload':
                    player_state['p1']['bullets'] = 6
                elif action == 'grenade':
                    player_state['p1']['grenades'] -= 1
                elif action == 'shield':
                    player_state['p1']['num_shield'] -= 1
                    player_state['p1']['shield_time'] = 10
                    player_state['p1']['shield_health'] = 30
                elif action == 'shoot':
                    player_state['p1']['bullets'] -= 1
                # print("[PLAYER STATE FROM GAME ENGINE]", player_state)
                viz_queue.put(player_state) 
            # if not viz_queue.empty():
            #     viz_data = viz_queue.get()
            #     print("viz data", viz_data)


    def AI_random(self, imu_data):
        print(imu_data)
        AI_actions = ['reload', 'check_grenade', 'shield', 'shoot']
        action = random.choice(AI_actions)
        if action == 'check_grenade':
            # pass to MQTT to check if player is visible
            viz_queue.put('check_grenade')
            # action_queue.put(action)
        else:
            action_queue.put(action)

    def eval_check(self, player_State):
        pass

# MQTT Client to send data to AWS IOT Core
class MQTT_Client(threading.Thread):
    def __init__(self, topic, client_id, group) -> None:
        super().__init__()
        self.topic = topic
        self.client_id = client_id
        self.group = group
        self.client = mqtt.Client(client_id)
        self.client.connect("test.mosquitto.org", 1883, 60)
        print('MQTT Client started on', self.client_id)
        self.client.subscribe(self.topic)
        self.client.on_message = self.receive
    
    def run(self):
        # while not viz_queue.empty():
        while True:
            data = viz_queue.get()
            print("[PUBLISH]", data)
            self.publish(str(data))
        # self.client.loop_forever()

    def publish(self, message):
        self.client.publish(self.topic, message)
        print('Published message to', self.topic, message)
    
    def receive(self, client, userdata, message):
        print("Received message from", message.topic, message.payload)
        if message.payload == b'grenade':
            action_queue.put('grenade') 
        
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

    game_engine = Game_Engine()
    game_engine.daemon = True
    game_engine.start()

    mqtt = MQTT_Client('test/cg4002', 'testpc', 2)
    mqtt.daemon = True
    mqtt.start()

    HOST, PORT = "localhost", 11000
    server = ThreadedTCPServer((HOST, PORT), Relay_Server)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("Server loop running in thread:", server_thread.name)


    # mqtt.client.on_message = mqtt.receive
    # f = open('test.json')
    # j = json.load(f)
    # for _ in range(3):
    #     mqtt.publish(json.dumps(j))
    #     time.sleep(1)
    mqtt.client.loop_forever()

if __name__ == "__main__":
    main()