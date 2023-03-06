# Ultra96 Server
from socket import *
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
from multiprocessing import Process, Queue, Lock
import json
import paho.mqtt.client as mqtt
import threading
import random
import traceback




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
class Relay_Server(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))

    def run(self):
        self.server.listen(5)
        print("[RELAY SERVER] Listening for connections on host {} port {} \n".format(self.host, self.port))
        while True:
            client, address = self.server.accept()
            # TODO Add client to where it connected to
            print("[RELAY SERVER] Client connected from {} \n".format(address))
            client_handler = threading.Thread(
                target=self.handle_client,
                args=(client, address)
            )
            client_handler.start()

    def handle_client(self, request, client_address):
        try:
            while True:
                # receive data from client
                # (protocol) len(data)_TYPE_data
                data = b''
                while not data.endswith(b'_'):
                    _d = request.recv(1)
                    if not _d:
                        data = b''
                        break
                    data += _d
                if len(data) == 0:
                    print('no more data from the client')
                    request.close()

                # Get Length of data
                data = data.decode("utf-8")
                length = int(data[:-1])

                # Get TYPE of data
                data = b''
                while not data.endswith(b'_'):
                    _d = request.recv(1)
                    if not _d:
                        data = b''
                        break
                    data += _d 
                # TODO
                # ir_sent bullet -= 1
                # ir_recv health -= 10 and give 1 point to other player
                data_type = data.decode("utf-8")[:-1]                

                # Get data
                data = b''
                while len(data) < length:
                    _d = request.recv(length - len(data))
                    if not _d:
                        data = b''
                        break
                    data += _d
                if len(data) == 0:
                    print('no more data from the client')

                data = data.decode("utf8")  # Decode raw bytes to UTF-8
                # format string for length and type
                
                # print("[LENGTH] {}, [DATATYPE] {}".format(length, data_type))
                # print("[DATA]", data)                
                
                if length != len(data):
                    print("Error", data)
                    print('Error: packet length does not match, packet dropped')
                
                else:
                    print("====================================")
                    print("[RELAY SERVER] {} wrote:".format(client_address), data)
                    print("====================================\n")
                    # process incoming data
                    # playerid, data
                    imu_queue.put(data)

        except Exception as e:
            print("Client disconnected")
            request.close()
            print(e)
            traceback.print_exc()


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
                    viz_queue.put(('CHECK', 'grenadeInSight'))
                elif action == 'grenade_p2_hits':
                    player_state['p2']['hp'] -= 30
                elif action == 'grenade_p2_misses':
                    pass    
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
                    player_state['p2']['hp'] = 100
                    player_state['p2']['num_deaths'] += 1
                    player_state['p2']['bullets'] = 6
                    player_state['p2']['grenades'] = 2
                    player_state['p2']['num_shield'] = 3
                    player_state['p2']['shield_time'] = 0
                    player_state['p2']['shield_health'] = 0
                
                # print("[PLAYER STATE FROM GAME ENGINE]", player_state)
                if not action == 'grenade': 
                    viz_queue.put(('STATE', player_state)) 
                    eval_queue.put(player_state)


    def AI_random(self, imu_data):
        # TODO send through DMA
        # print(imu_data)
        AI_actions = ['reload', 'grenade', 'shield', 'shoot']
        # AI_actions = ['reload', 'shield', 'shoot']
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
            type, data = viz_queue.get()
            # print("[PUBLISH]", data)
            self.publish(type, data)

    def publish(self, type, data):
        try:
            data = str(data)
            message = str(len(data)) + '_' + type + '_' + data
            self.client.publish(self.pub_topic, message)
            print('====================================')
            print('[MQTT] Published message to visualiser at', self.pub_topic, message)
            print('====================================')
        except:
            print("Error: could not publish message")
    def receive(self, client, userdata, message):
        try:
            msg  = message.payload.decode("utf-8")
            # msg = message.payload	
            length = int(msg.split('_')[0])
            check = msg.split('_')[1]
            data = msg.split('_')[2]
            print('====================================')
            print("\n [MQTT] Received message from", message.topic, message.payload)
            print('====================================')
            if check == 'CHECK':
                # to update grenade damage for player 2
                if data == 'Visble':
                    print("[MQTT] Player 2 is in grenade range")
                    action_queue.put('grenade_p2_hits')
                else: 
                    print("[MQTT] Player 2 is not in grenade range")
                    action_queue.put('grenade_p2_misses')
        except:
            print('Error: message not in correct format')
            print(message.payload)
        
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
        try:
            while True:
                data = eval_queue.get()
                self.send(json.dumps(data)) 
                self.receive()
        except:
            print('Failed to send message to Evaluation Server', self.eval_ip, self.eval_port)
            self.close()


    # Initialise AES Cipher
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
                print('=====================================')
                print('[EVAL CLIENT] Sent message to Evaluation Server', self.eval_ip, self.eval_port, message)
                print('=====================================')
            except:
                print('[EVAL CLIENT] Failed to send message to Evaluation Server', self.eval_ip, self.eval_port, message)
                self.close()
    
    def receive(self):
        if self.clientSocket is not None:
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
                print('=====================================')
                print("[EVAL CLIENT] Received message from Evaluation Server", msg)
                print('=====================================')
            
            except:
                print('Failed to receive message from Evaluation Server', self.eval_ip, self.eval_port)
                self.close()


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

    mqtt = MQTT_Client('cg4002/gamestate', 'cg4002/visualizer', 'ultra96', 2)
    mqtt.daemon = True
    mqtt.start()

    HOST, PORT = "localhost", 11000
    server = Relay_Server(HOST, PORT)
    server.daemon = True
    server.start()

    mqtt.client.loop_forever()

if __name__ == "__main__":
    main()