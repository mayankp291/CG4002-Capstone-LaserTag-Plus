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
eval_queue = Queue()



player_state = {
    "p1":
    {
        "hp": 100,
        "action": "none",
        "bullets": 6,
        "grenades": 2,
        "shield_time": 0,
        "shield_health": 0,
        "num_deaths": 0,
        "num_shield": 3
    },
    "p2":
    {
        "hp": 100,
        "action": "none",
        "bullets": 6,
        "grenades": 2,
        "shield_time": 0,
        "shield_health": 0,
        "num_deaths": 0,
        "num_shield": 3
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
                # self.request.sendall(response.encode('utf-8'))

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class Game_Engine(threading.Thread):
    def __init__(self):
        super().__init__()
    
    def run(self):
        while True:
            if not imu_queue.empty():
                imu_data = imu_queue.get()
                self.AI_random(imu_data)

            if not action_queue.empty():
                action = action_queue.get()
                print("[ACTION]", action)
                # Update action for player 1
                if action != 'grenade_p2_hits':
                    player_state['p1']['action'] = action
                # Update player 1 state (active player) and player 2 state (passive player)
                if action == 'reload':
                    player_state['p1']['bullets'] = 6
                elif action == 'grenade':
                    # update grenade for player 1
                    player_state['p1']['grenades'] -= 1
                    # send check for player 2
                    viz_queue.put('check_grenade')
                elif action == 'grenade_p2_hits':
                    player_state['p2']['hp'] -= 30
                elif action == 'shield':
                    player_state['p1']['num_shield'] -= 1
                    player_state['p1']['shield_time'] = 10
                    player_state['p1']['shield_health'] = 30
                elif action == 'shoot':
                    player_state['p1']['bullets'] -= 1
                    # TODO check if player 2 is in shield
                    player_state['p2']['hp'] -= 10
                
                # rebirth for player 2
                if player_state['p2']['hp'] <= 0:
                    # reset player 2 stats
                    player_state['p2']['hp'] = 0
                    player_state['p2']['num_deaths'] += 1
                    player_state['p2']['bullets'] = 6
                    player_state['p2']['grenades'] = 2
                    player_state['p2']['num_shield'] = 3
                    player_state['p2']['shield_time'] = 0
                    player_state['p2']['shield_health'] = 0
                
                # print("[PLAYER STATE FROM GAME ENGINE]", player_state)
                viz_queue.put(player_state) 
                eval_queue.put(player_state)


    def AI_random(self, imu_data):
        print(imu_data)
        # AI_actions = ['reload', 'grenade', 'shield', 'shoot']
        AI_actions = ['reload', 'shield', 'shoot']
        action = random.choice(AI_actions)
        action_queue.put(action)

    def eval_check(self, player_State):
        pass

# MQTT Client to send data to AWS IOT Core
class MQTT_Client(threading.Thread):
    def __init__(self, pub_topic, sub_topic, client_id, group) -> None:
        super().__init__()
        self.pub_topic = pub_topic
        self.sub_topic = sub_topic
        self.client_id = client_id
        self.group = group
        self.client = mqtt.Client(client_id)
        self.client.connect("test.mosquitto.org", 1883, 60)
        print('MQTT Client started on', self.client_id)
        self.client.subscribe(self.sub_topic)
        self.client.on_message = self.receive
    
    def run(self):
        while True:
            data = viz_queue.get()
            # print("[PUBLISH]", data)
            self.publish(str(data))

    def publish(self, message):
        self.client.publish(self.pub_topic, message)
        print('Published message to', self.pub_topic, message)
    
    def receive(self, client, userdata, message):
        print("Received message from", message.topic, message.payload)
        if message.payload == b'grenade':
            # to update grenade damage for player 2
            action_queue.put('grenade_p2_hits') 
        
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
        while True:
            data = eval_queue.get()
            self.send(json.dumps(data)) 
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
        # if self.clientSocket is not None:
        #     try:
        #         recv_message = self.clientSocket.recv(2048)
        #         print('Received message from Evaluation Server', self.eval_ip, self.eval_port, recv_message)
        #     except:
        #         print('Failed to receive message from Evaluation Server', self.eval_ip, self.eval_port)
        #         self.clientSocket = None
        # try:
        #     len_info = self.clientSocket.recv(2048)
        #     len_info = int(len_info.decode("utf-8").split("_")[0])
        #     recv_message = self.clientSocket.recv(len_info)
        #     print('Received message from Evaluation Server', self.eval_ip, self.eval_port, recv_message.decode("utf-8"))
        # except:
        #     print('Failed to receive message from Evaluation Server', self.eval_ip, self.eval_port)
        #     self.clientSocket = None
        try:
            # recv length followed by '_' followed by cypher
            data = b''
            while not data.endswith(b'_'):
                _d = self.clientSocket.recv(1)
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from the client')
                self.stop()

            data = data.decode("utf-8")
            length = int(data[:-1])

            data = b''
            while len(data) < length:
                _d = self.clientSocket.recv(length - len(data))
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from the client')
                self.stop()
            msg = data.decode("utf8")  # Decode raw bytes to UTF-8
            print("[RECEIVED]", msg)
        
        except:
            print('Failed to receive message from Evaluation Server', self.eval_ip, self.eval_port)
            # self.clientSocket = None


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

    mqtt = MQTT_Client('cg4002/gamestate', 'cg4002/visualiser', 'testpc', 2)
    mqtt.daemon = True
    mqtt.start()

    HOST, PORT = "localhost", 11000
    server = ThreadedTCPServer((HOST, PORT), Relay_Server)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("Server loop running in thread:", server_thread.name)

    mqtt.client.loop_forever()

if __name__ == "__main__":
    main()