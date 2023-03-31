#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# Ultra96 Server
from socket import *
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
from multiprocessing import Process, Queue, Lock
import json
import paho.mqtt.client as paho
from paho import mqtt
from ast import literal_eval
import threading
import random
import time
import traceback
from copy import deepcopy
import numpy as np
# from scipy.stats import skew
# from scipy.fftpack import fft

# data = {"playerID": 1, 2, “beetleID”: 1-6, “sensorData”: {}}
# len_data

beetleID_mapping = {
    1: "IMU", #imu1
    2: "VEST", #VEST1
    3: "GUN", #GUN1
    4: "IMU", #IMU2
    5: "VEST", #vest2
    6: "GUN", #gun2
    7: "TEST"
}

MQTT_USERNAME = "capstonekillingus"
MQTT_PASSWORD = "capstonekillingus"
imu_queue = Queue()
action_p1_queue = Queue()
action_p2_queue = Queue()
viz_queue = Queue()
eval_queue = Queue()

reloadSendRelay = threading.Event()
reloadSendRelay.clear() 
grenadeSendRelay = threading.Event()
grenadeSendRelay.clear()
isPlayerOneActivated = threading.Event()
isPlayerOneActivated.clear()
isPlayerTwoActivated = threading.Event()
isPlayerTwoActivated.clear()
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

    ###
    # Data flow: get len, get msg, check len == len(msg), convert msg to dict
    ###
    def handle_client(self, request, client_address):
        try:
            while True:
                # receive data from client
                # (protocol) len(data)_data
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
                
                # check length of data
                if length != len(data):
                    print("Error", data)
                    print('Error: packet length does not match, packet dropped')
                
                else:
                    # convert data to dict {'playerID':, 'beetleID':, 'sensorData':}
                    data = literal_eval(data)
                    print("====================================")
                    print("[RELAY SERVER] {} wrote:".format(client_address), data)
                    print("====================================\n")
                    ### process incoming data
                    # playerid, data
                    beetleID = data["beetleID"]
                    data_device = beetleID_mapping[beetleID]

                    if data_device == "IMU":
                        # add an IMU PACKET to the queue (playerID, sensorData)
                        # imu_packet = (data["playerID"], data["sensorData"])
                        # imu_queue.put(imu_packet)
                        arr = data["sensorData"]
                        # convert string to numpy array of ints
                        # new_array = np.fromstring(arrayyy, dtype=float).reshape((40, 6))
                        new_array = np.frombuffer(base64.binascii.a2b_base64(arr), dtype=np.int32).reshape(40, 6)
                        print(new_array, new_array.shape)
                        imu_queue.put(new_array)
                        print("IMU RECV")
                        # grenadeSendRelay.set()
                    elif data_device == "VEST":
                        # got shot damage
                        # action_packet = (data["playerID"], "shoot_p2_hits")
                        # action_queue.put(action_packet)
                        print("VEST RECV")
                        action_p1_queue.put("shoot_p2_hits")

                    elif data_device == "GUN":
                        # shot by player
                        # action_packet = (data["playerID"], "shoot")
                        # action_queue.put(action_packet)
                        print("SHOOT RECV")
                        action_p1_queue.put("shoot")
                    elif data_device == "TEST":
                        action_p1 = data["sensorData"][0]
                        action_p2 = data["sensorData"][1]
                        action_p1_queue.put(action_p1)
                        action_p2_queue.put(action_p2)

                # RELOAD SEND TO RELAY
                if reloadSendRelay.is_set():
                    dic = {"playerId": 1, "action": "reload"}
                    dic = str(dic)
                    reloadSendRelay.clear()
                    request.sendall(dic.encode("utf8"))
                    print("RELOAD SENT")

                # GRENADE SEND TO RELAY
                if grenadeSendRelay.is_set():
                    dic = {"playerId": 1, "action": "grenade"}
                    dic = str(dic)
                    grenadeSendRelay.clear()
                    request.sendall(dic.encode("utf8"))
                    print("GRENADE SENT")

        except Exception as e:
            print("Client disconnected")
            request.close()
            print(e)
            traceback.print_exc()


class Game_Engine(threading.Thread):
    def __init__(self):
        super().__init__()
    
    def run(self):
        isPlayerOneShieldActivated = False
        isPlayerTwoShieldActivated = False
        isPlayerOneShootActivated = False
        isPlayerTwoShootActivated = False
        isPlayerTwoGrenadeActivated = False
        isPlayerOneGrenadeActivated = False
        startTimeOne = 0
        startTimeOneShoot = 0
        startTimeTwoShoot = 0
        startTimeTwo = 0
        viz_queue.put(('STATE', player_state))
        while True:
            if isPlayerOneShieldActivated:
                player_state['p1']['shield_time'] = 10 - (time.time() - startTimeOne)
                if player_state['p1']['shield_time'] <= 0:
                    player_state['p1']['shield_time'] = 0
                    player_state['p1']['shield_health'] = 0
                    isPlayerOneShieldActivated = False

            if isPlayerTwoShieldActivated:
                player_state['p2']['shield_time'] = 10 - (time.time() - startTimeTwo)
                if player_state['p2']['shield_time'] <= 0:
                    player_state['p2']['shield_time'] = 0
                    player_state['p2']['shield_health'] = 0
                    isPlayerTwoShieldActivated = False

            if isPlayerOneShootActivated:
                time_elapsed = time.time() - startTimeOneShoot
                if time_elapsed >= 3:
                    isPlayerOneShootActivated = False
                    action_p1_queue.put('shoot_p2_misses')
            
            if isPlayerTwoShootActivated:
                time_elapsed = time.time() -startTimeTwoShoot
                if time_elapsed >= 3:
                    isPlayerTwoShootActivated = False
                    action_p2_queue.put('shoot_p1_misses')

            if not imu_queue.empty():
                imu_data = imu_queue.get()
                self.AI_random(imu_data)

            if ((not action_p1_queue.empty()) and (not action_p2_queue.empty())) :
                action_p1 = action_p1_queue.get()
                action_p2 = action_p2_queue.get()
                print("[PLAYER_1_ACTION]", action_p1)
                print("[PLAYER_2_ACTION]", action_p2)
                # Update action for player 1
                if action_p1 != 'grenade_p2_hits' and action_p1 != 'grenade_p2_misses':
                    player_state['p1']['action'] = action_p1
                if action_p2 != 'grenade_p1_hits' and action_p2 != 'grenade_p1_misses':
                    player_state['p2']['action'] = action_p2
                
                # Update player 1 state (active player) 
                if action_p1 == 'reload':
                    if player_state['p1']['bullets'] <= 0:
                        player_state['p1']['bullets'] = 6
                elif action_p1 == 'grenade':
                    # update grenade for player 1
                    if player_state['p1']['grenades'] > 0:
                        player_state['p1']['grenades'] -= 1
                        isPlayerOneGrenadeActivated = True
                    # send check for player 2
                elif action_p1 == 'grenade_p2_hits':
                    if isPlayerTwoShieldActivated:
                        player_state['p2']['shield_health'] -= 30
                    else:
                        player_state['p2']['hp'] -= 30
                        print("[STATUS] ", player_state)       
                elif action_p1 == 'shield':
                    if player_state['p1']['num_shield'] > 0 and (not isPlayerOneShieldActivated):
                        player_state['p1']['num_shield'] -= 1
                        player_state['p1']['shield_time'] = 10
                        player_state['p1']['shield_health'] = 30
                        isPlayerOneShieldActivated = True
                        startTimeOne = time.time()
                elif action_p1 == 'shoot_p2_hits':
                    if isPlayerTwoShieldActivated:
                        player_state['p2']['shield_health'] -= 10
                    else:
                        player_state['p2']['hp'] -= 10
                    isPlayerOneShootActivated = False
                elif action_p1 == 'shoot_p2_misses':
                    pass
                elif action_p1 == 'shoot':
                    if player_state['p1']['bullets'] > 0:
                        player_state['p1']['bullets'] -= 1
                        isPlayerOneShootActivated = True
                        startTimeOneShoot = time.time()
                
                # Update player 2 state (active player) 
                if action_p2 == 'reload':
                    if player_state['p2']['bullets'] <= 0:
                        player_state['p2']['bullets'] = 6
                elif action_p2 == 'grenade':
                    # update grenade for player 1
                    if player_state['p2']['grenades'] > 0:
                        player_state['p2']['grenades'] -= 1
                        isPlayerTwoGrenadeActivated = True
                    # send check for player 2
                elif action_p2 == 'grenade_p1_hits':
                    if isPlayerOneShieldActivated:
                        player_state['p1']['shield_health'] -= 30
                    else:
                        player_state['p1']['hp'] -= 30
                        print("[STATUS] ", player_state)       
                elif action_p2 == 'shield':
                    if player_state['p2']['num_shield'] > 0 and (not isPlayerTwoShieldActivated):
                        player_state['p2']['num_shield'] -= 1
                        player_state['p2']['shield_time'] = 10
                        player_state['p2']['shield_health'] = 30
                        isPlayerTwoShieldActivated = True
                        startTimeTwo = time.time()
                elif action_p2 == 'shoot_p1_hits':
                    if isPlayerOneShieldActivated:
                        player_state['p1']['shield_health'] -= 10
                    else:
                        player_state['p1']['hp'] -= 10
                    isPlayerTwoShootActivated = False
                elif action_p2 == 'shoot_p2_misses':
                    pass
                elif action_p2 == 'shoot':
                    if player_state['p2']['bullets'] > 0:
                        player_state['p2']['bullets'] -= 1
                        isPlayerTwoShootActivated = True
                        startTimeTwoShoot = time.time()

                if player_state['p1']['shield_health'] <= 0:
                    isPlayerOneShieldActivated = False
                    player_state['p1']['hp'] += player_state['p1']['shield_health']
                    player_state['p1']['shield_health'] = 0
                    player_state['p1']['shield_time'] = 0
            
                if player_state['p2']['shield_health'] <= 0:
                    isPlayerTwoShieldActivated = False
                    player_state['p2']['hp'] += player_state['p2']['shield_health']
                    player_state['p2']['shield_health'] = 0
                    player_state['p2']['shield_time'] = 0
            
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

                # rebirth for player 1
                if player_state['p1']['hp'] <= 0:
                    # reset player 1 stats
                    player_state['p1']['hp'] = 100
                    player_state['p1']['num_deaths'] += 1
                    player_state['p1']['bullets'] = 6
                    player_state['p1']['grenades'] = 2
                    player_state['p1']['num_shield'] = 3
                    player_state['p1']['shield_time'] = 0
                    player_state['p1']['shield_health'] = 0
                
                # print("[PLAYER STATE FROM GAME ENGINE]", player_state)
                if ((action_p1 == 'shoot_p2_hits') or (action_p1 == 'shoot_p2_misses') or (action_p2 == 'shoot_p1_hits') or (action_p1 == 'shoot_p1_misses')) and (not isPlayerOneShootActivated) and (not isPlayerTwoShootActivated):
                    viz_queue.put(('CHECK', deepcopy(player_state)))
                    if (action_p1 == 'shoot_p2_hits') or (action_p1 == 'shoot_p2_misses'):
                        player_state['p1']['action'] = 'shoot'
                    if (action_p2 == 'shoot_p1_hits') or (action_p2 == 'shoot_p1_misses'):
                        player_state['p2']['action'] = 'shoot'
                    eval_queue.put(('CHECK', deepcopy(player_state)))
                elif ((action_p1 == 'grenade_p2_hits') or (action_p1 == 'grenade_p2_misses') or (action_p2 == 'grenade_p1_hits') or (action_p1 == 'grenade_p1_misses')) and (isPlayerOneGrenadeActivated or isPlayerTwoGrenadeActivated):
                    viz_queue.put(('CHECK', deepcopy(player_state)))
                    if (action_p1 == 'grenade_p2_hits') or (action_p1 == 'grenade_p2_misses'):
                        player_state['p1']['action'] = 'grenade'
                        isPlayerOneGrenadeActivated = False
                    if (action_p2 == 'grenade_p1_hits') or (action_p2 == 'grenade_p1_misses'):
                        player_state['p2']['action'] = 'grenade'
                        isPlayerTwoGrenadeActivated = False
                        if (action_p1 == 'grenade_p1_misses'):
                            player_state['p1']['hp'] -= 30
                            if (player_state['p1']['hp']) < 0:
                                player_state['p1']['hp'] = 100
                    eval_queue.put(('CHECK', deepcopy(player_state)))
                elif (action_p1 == 'shoot') or (action_p2 == 'shoot') or (action_p1 == 'grenade') or (action_p2 == 'grenade'):
                    viz_queue.put(('CHECK', deepcopy(player_state)))
                else:
                    viz_queue.put(('CHECK', deepcopy(player_state)))
                    eval_queue.put(('CHECK', deepcopy(player_state)))

    def AI_random(self, imu_data):
        # TODO send through DMA
        # print(imu_data)
        # AI_actions = ['shoot']
        # AI_actions = ['logout']
        AI_actions = ['reload', 'grenade', 'shield', 'shoot']
        # AI_actions = ['reload', 'shield', 'shoot']
        action = random.choice(AI_actions)
        players = ['p1', 'p2']
        player = random.choice(players)
        # action_queue.put(action)
        # action_queue.put((player, action))

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
        self.client = paho.Client(client_id, protocol=paho.MQTTv5)
        self.client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.connect("e56e6e3e03d54e70bf9cc69a2761fe4c.s1.eu.hivemq.cloud", 8883, 60)
        print('MQTT Client started on', self.client_id)
        self.client.subscribe(self.sub_topic)
        self.client.on_message = self.receive
    
    def start_loop(self):
        self.client.loop_forever()
        
    def run(self):
        # mqtt_loop_thread = threading.Thread(target=self.start_loop)
        # mqtt_loop_thread.start()
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
            # msg  = message.payload.decode("utf-8")
            # # msg = message.payload	
            # length = int(msg.split('_')[0])
            # check = msg.split('_')[1]
            # data = msg.split('_')[2]
            # print('====================================')
            # print("\n [MQTT] Received message from", message.topic, message.payload)
            # print('====================================')
            # if check == 'CHECK':
            #     # to update grenade damage for player 2
            #     if data == 'Visible':
            #         print("[MQTT] Player 2 is in grenade range")
            #         action_queue.put('grenade_p2_hits')
            #     else: 
            #         print("[MQTT] Player 2 is not in grenade range")
            #         action_queue.put('grenade_p2_misses')
            print("[MQTT] " + str(message.payload))
            if message.payload == b'14_CHECK_grenade_p2_hit':
                # to update grenade damage for player 2
                print("[MQTT] Player 2 is in grenade range")
                action_p1_queue.put('grenade_p2_hits') 
            elif message.payload == b'15_CHECK_grenade_p2_miss':
                print("[MQTT] Player 2 is not in grenade range")      
                action_p1_queue.put('grenade_p2_misses') 
                # action_queue.put('grenade_p2_misses')
            elif message.payload == b'14_CHECK_grenade_p1_hit':
                print("[MQTT] Player 1 is in grenade range")
                action_p2_queue.put('grenade_p1_hits') 
            elif message.payload == b'15_CHECK_grenade_p1_miss':
                print("[MQTT] Player 1 is not in grenade range")      
                action_p2_queue.put('grenade_p1_misses') 
            elif message.payload == b'6_CHECK_update':
                player_state_copy = deepcopy(player_state)
                player_state_copy['p1']['action'] = 'none'
                player_state_copy['p2']['action'] = 'none'
                viz_queue.put(('STATE', player_state_copy))
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
            global player_state
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
                recv_dict = literal_eval(msg)
                player_state = recv_dict
                recv_dict['p1']['action'] = 'none'
                recv_dict['p2']['action'] = 'none'
                viz_queue.put(('STATE', recv_dict))
                print('=====================================')
                print("[EVAL SERVER] Received message from Evaluation Server", msg)
                print('=====================================')
                print('=====================================')
                print("[EVAL UPDATE] Updated player state from Evaluation Server", player_state)
                print('=====================================')
                ### update event flags
                if player_state['p1']['action'] == 'grenade':
                    grenadeSendRelay.set()
                if player_state['p1']['action'] == 'reload':
                    reloadSendRelay.set()

            
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

    # mqtt = MQTT_Client('cg4002/gamestate', 'cg4002/visualizer', 'ultra96', 2)
    # mqtt.daemon = True
    # mqtt.start()
    mqtt_client = MQTT_Client('cg4002/gamestate', 'cg4002/visualizer', 'ultra96', 2)
    mqtt_client.daemon = True
    mqtt_client.start()

    HOST, PORT = "localhost", 11000
    server = Relay_Server(HOST, PORT)
    server.daemon = True
    server.start()
    # while True:
    #     pass
    # mqtt.client.loop_forever()
    mqtt_client.client.loop_forever()

if __name__ == "__main__":
    main()