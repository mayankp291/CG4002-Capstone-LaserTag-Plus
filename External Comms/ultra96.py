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
from scipy.stats import skew
from scipy.fftpack import fft
from pynq import Overlay
from pynq import allocate


# data = {"playerID": 1, 2, “beetleID”: 1-6, “sensorData”: {}}
# len_data

prediction_array = []
NUM_OUTPUT = 1
NUM_FEATURES = 8
NUM_INPUT = NUM_FEATURES * 6
SAMPLE_SIZE = 40

# DMA BUFFER CONFIG
ol = Overlay('design_1_wrapper.bit')
dma = ol.axi_dma_0
input_buffer = allocate(shape=(NUM_INPUT), dtype=np.int32)
output_buffer = allocate(shape=(NUM_OUTPUT,), dtype=np.int32)



beetleID_mapping = {
    1: "IMU1", #imu1
    2: "VEST1", #VEST1
    3: "GUN1", #GUN1
    4: "IMU2", #IMU2
    5: "VEST2", #vest2
    6: "GUN2", #gun2
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
# isPlayerOneActivated = threading.Event()
# isPlayerOneActivated.clear()
# isPlayerTwoActivated = threading.Event()
# isPlayerTwoActivated.clear()
shootGrenadeActivated = threading.Event()
shootGrenadeActivated.clear()
evalServerConnected = threading.Event()
evalServerConnected.clear()
isPlayerOneGrenadeActivated = threading.Event()
isPlayerOneGrenadeActivated.clear()
isPlayerTwoGrenadeActivated = threading.Event()
isPlayerTwoGrenadeActivated.clear()
isPlayerOneShootActivated = threading.Event()
isPlayerOneShootActivated.clear()
isPlayerTwoShootActivated = threading.Event()
isPlayerOneShootActivated.clear()
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
                    

                    ### process incoming data
                    # playerid, data
                    beetleID = data["beetleID"]
                    data_device = beetleID_mapping[beetleID]

                    if not data_device=="IMU":
                        print("====================================")
                        print("[RELAY SERVER] {} wrote:".format(client_address), data)
                        print("====================================\n")

                    if data_device == "IMU1" or data_device == "IMU2":
                        # add an IMU PACKET to the queue (playerID, sensorData)
                        # imu_packet = (data["playerID"], data["sensorData"])
                        # imu_queue.put(imu_packet)
                        arr = data["sensorData"]
                        # convert string to numpy array of ints
                        new_array = np.frombuffer(base64.binascii.a2b_base64(arr), dtype=np.int32).reshape(SAMPLE_SIZE, 6)
                        # print(new_array, new_array.shape)
                        ### TODO ADD PLAYER IDENTIFIER
                        if data_device == "IMU1":
                            imu_queue.put(new_array)
                            print("IMU 1 RECV")
                        else:
                            imu_queue.put(new_array)
                            print("IMU 2 RECV")
                        
                        # grenadeSendRelay.set()
                    
                    elif data_device == "VEST1":
                        print("VEST 1 RECV")
                        action_p1_queue.put("shoot_p2_hits")
                        isPlayerOneShootActivated.clear()
                    
                    elif data_device == "VEST2":
                        print("VEST 2 RECV")
                        action_p2_queue.put("shoot_p1_hits")
                        isPlayerTwoShootActivated.clear()

                    elif data_device == "GUN1":
                        # shot by player
                        # action_packet = (data["playerID"], "shoot")
                        # action_queue.put(action_packet)
                        print("GUN 1 RECV")
                        action_p1_queue.put("shoot")

                    elif data_device == "GUN2":
                        print("GUN 2 RECV")
                        action_p2_queue.put("shoot")
                    
                    elif data_device == "TEST":
                        action_p1 = data["sensorData"][0]
                        action_p2 = data["sensorData"][1]
                        if action_p1 == 'shoot_p2_hits':
                            isPlayerOneShootActivated.clear()
                        if action_p1 == 'grenade_p2_hits':
                            isPlayerOneGrenadeActivated.clear()
                        if action_p2 == 'shoot_p1_hits':
                            isPlayerTwoShootActivated.clear()
                        if action_p2 == 'grenade_p1_hits':
                            isPlayerTwoGrenadeActivated.clear()
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

            if isPlayerOneShootActivated.is_set():
                time_elapsed = time.time() - startTimeOneShoot
                if time_elapsed >= 3:
                    action_p1_queue.put('shoot_p2_misses')
                    isPlayerOneShootActivated.clear()
                    print('P1', action_p1_queue.qsize())

            
            if isPlayerTwoShootActivated.is_set():
                time_elapsed = time.time() - startTimeTwoShoot
                if time_elapsed >= 3:
                    action_p2_queue.put('shoot_p1_misses')
                    isPlayerTwoShootActivated.clear()
                    print('P2', action_p2_queue.qsize())

            if not imu_queue.empty():
                imu_data = imu_queue.get()
                # self.AI_random(imu_data)
                a = self.AI_actual(imu_data)
                # print("[AI]", a)

            if ((not action_p1_queue.empty()) and (not action_p2_queue.empty())):
                action_p1 = 'none'
                action_p2 = 'none'
                if shootGrenadeActivated.is_set():
                    if not action_p1_queue.empty():
                        action_p1 = action_p1_queue.get()
                    if not action_p2_queue.empty():
                        action_p2 = action_p2_queue.get()
                else:
                    action_p1 = action_p1_queue.get()
                    action_p2 = action_p2_queue.get()
                print("[PLAYER_1_ACTION]", action_p1)
                print("[PLAYER_2_ACTION]", action_p2)
                # Update action for player 1
                if action_p1 != 'none':
                    player_state['p1']['action'] = action_p1
                if action_p2 != 'none':
                    player_state['p2']['action'] = action_p2
                
                # Update player 1 state (active player) 
                if action_p1 == 'reload':
                    if player_state['p1']['bullets'] <= 0:
                        player_state['p1']['bullets'] = 6
                        reloadSendRelay.set()
                elif action_p1 == 'grenade':
                    # update grenade for player 1
                    if player_state['p1']['grenades'] > 0:
                        player_state['p1']['grenades'] -= 1
                        isPlayerOneGrenadeActivated.set()
                        shootGrenadeActivated.set()
                    # send check for player 2
                elif action_p1 == 'grenade_p2_hits':
                    if isPlayerTwoShieldActivated:
                        player_state['p2']['shield_health'] -= 30

                    else:
                        player_state['p2']['hp'] -= 30
                        grenadeSendRelay.set()
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
                elif action_p1 == 'shoot_p2_misses':
                    pass
                elif action_p1 == 'shoot':
                    if player_state['p1']['bullets'] > 0:
                        player_state['p1']['bullets'] -= 1
                        isPlayerOneShootActivated.set()
                        startTimeOneShoot = time.time()
                
                # Update player 2 state (active player) 
                if action_p2 == 'reload':
                    if player_state['p2']['bullets'] <= 0:
                        player_state['p2']['bullets'] = 6
                elif action_p2 == 'grenade':
                    # update grenade for player 1
                    if player_state['p2']['grenades'] > 0:
                        player_state['p2']['grenades'] -= 1
                        isPlayerTwoGrenadeActivated.set()
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
                elif action_p2 == 'shoot_p2_misses':
                    pass
                elif action_p2 == 'shoot':
                    if player_state['p2']['bullets'] > 0:
                        player_state['p2']['bullets'] -= 1
                        isPlayerTwoShootActivated.set()
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
                if shootGrenadeActivated.is_set():
                    player_state_cp = deepcopy(player_state)
                    if ((action_p1 == 'shoot_p2_hits') or (action_p1 == 'shoot_p2_misses') or (action_p2 == 'shoot_p1_hits') or (action_p1 == 'shoot_p1_misses')) and (not isPlayerOneShootActivated) and (not isPlayerTwoShootActivated):
                        if (action_p1 == 'shoot_p2_hits') or (action_p1 == 'shoot_p2_misses'):
                            player_state['p1']['action'] = 'shoot'
                        else:
                            player_state_cp['p1']['action'] = 'none'
                        if (action_p2 == 'shoot_p1_hits') or (action_p2 == 'shoot_p1_misses'):
                            player_state['p2']['action'] = 'shoot'
                        else:
                            player_state_cp['p2']['action'] = 'none'
                    if ((action_p1 == 'grenade_p2_hits') or (action_p1 == 'grenade_p2_misses') or (action_p2 == 'grenade_p1_hits') or (action_p1 == 'grenade_p1_misses')) and (isPlayerOneGrenadeActivated or isPlayerTwoGrenadeActivated):
                        if (action_p1 == 'grenade_p2_hits') or (action_p1 == 'grenade_p2_misses'):
                            player_state['p1']['action'] = 'grenade'
                        else:
                            player_state_cp['p1']['action'] = 'none'
                        if (action_p2 == 'grenade_p1_hits') or (action_p2 == 'grenade_p1_misses'):
                            player_state['p2']['action'] = 'grenade'
                        else:
                            player_state_cp['p2']['action'] = 'none'
                    viz_queue.put(('CHECK', player_state_cp))
                    eval_queue.put(deepcopy(player_state))
                    shootGrenadeActivated.clear()
                elif (action_p1 == 'shoot') or (action_p2 == 'shoot') or (action_p1 == 'grenade') or (action_p2 == 'grenade'):
                    viz_queue.put(('CHECK', deepcopy(player_state)))
                    shootGrenadeActivated.set()
                else:
                    viz_queue.put(('CHECK', deepcopy(player_state)))
                    eval_queue.put(deepcopy(player_state))

    def eval_check(self, player_State):
        pass

    def extract_features(self, input):

        mean_acc_x = np.mean(input[0])
        mean_acc_y = np.mean(input[1])
        mean_acc_z = np.mean(input[2])
        mean_gyro_x = np.mean(input[3])
        mean_gyro_y = np.mean(input[4])
        mean_gyro_z = np.mean(input[5])

        sd_acc_x = np.std(input[0])
        sd_acc_y = np.std(input[1])
        sd_acc_z = np.std(input[2])
        sd_gyro_x = np.std(input[3])
        sd_gyro_y = np.std(input[4])
        sd_gyro_z = np.std(input[5])

        max_acc_x = np.amax(input[0])
        max_acc_y = np.amax(input[1])
        max_acc_z = np.amax(input[2])
        max_gyro_x = np.amax(input[3])
        max_gyro_y = np.amax(input[4])
        max_gyro_z = np.amax(input[5])

        min_acc_x = np.amin(input[0])
        min_acc_y = np.amin(input[1])
        min_acc_z = np.amin(input[2])
        min_gyro_x = np.amin(input[3])
        min_gyro_y = np.amin(input[4])
        min_gyro_z = np.amin(input[5])

        rms_acc_x = np.sqrt(np.mean(input[0] ** 2))
        rms_acc_y = np.sqrt(np.mean(input[1] ** 2))
        rms_acc_z = np.sqrt(np.mean(input[2] ** 2))
        rms_gyro_x = np.sqrt(np.mean(input[3] ** 2))
        rms_gyro_y = np.sqrt(np.mean(input[4] ** 2))
        rms_gyro_z = np.sqrt(np.mean(input[5] ** 2))

        skew_acc_x = skew(input[0])
        skew_acc_y = skew(input[1])
        skew_acc_z = skew(input[2])
        skew_gyro_x = skew(input[3])
        skew_gyro_y = skew(input[4])
        skew_gyro_z = skew(input[5])

        mag_acc_x = np.amax(np.abs(fft(input[0])))
        mag_acc_y = np.amax(np.abs(fft(input[1])))
        mag_acc_z = np.amax(np.abs(fft(input[2])))
        mag_gyro_x = np.amax(np.abs(fft(input[3])))
        mag_gyro_y = np.amax(np.abs(fft(input[4])))
        mag_gyro_z = np.amax(np.abs(fft(input[5])))

        phase_acc_x = np.amax(np.angle(fft(input[0])))
        phase_acc_y = np.amax(np.angle(fft(input[1])))
        phase_acc_z = np.amax(np.angle(fft(input[2])))
        phase_gyro_x = np.amax(np.angle(fft(input[3])))
        phase_gyro_y = np.amax(np.angle(fft(input[4])))
        phase_gyro_z = np.amax(np.angle(fft(input[5])))

        return np.array([mean_acc_x, mean_acc_y, mean_acc_z, mean_gyro_x, mean_gyro_y, mean_gyro_z, sd_acc_x,
                               sd_acc_y, sd_acc_z, sd_gyro_x, sd_gyro_y, sd_gyro_z,
                               max_acc_x, max_acc_y, max_acc_z, max_gyro_x, max_gyro_y, max_gyro_z,
                               min_acc_x, min_acc_y, min_acc_z, min_gyro_x, min_gyro_y, min_gyro_z,
                               rms_acc_x, rms_acc_y, rms_acc_z, rms_gyro_x, rms_gyro_y, rms_gyro_z,
                               skew_acc_x, skew_acc_y, skew_acc_z, skew_gyro_x, skew_gyro_y, skew_gyro_z,
                               mag_acc_x, mag_acc_y, mag_acc_z, mag_gyro_x, mag_gyro_y, mag_gyro_z,
                               phase_acc_x, phase_acc_y, phase_acc_z, phase_gyro_x, phase_gyro_y, phase_gyro_z]).astype(np.int32)


    def detect_start_of_move(self, imu_data):

        # define threshold values as hard-coded values
        x_thresh = 18000
        y_thresh = 12000
        z_thresh = 21000

        np_imu_data = np.array(imu_data)

        # compare each data point in window to threshold
        for j in range(np_imu_data.shape[0]):
            acc_vals = np_imu_data[j, :3]

            if (abs(acc_vals[0]) > x_thresh) or (abs(acc_vals[1]) > y_thresh) or (abs(acc_vals[2]) > z_thresh):
                # potential start of move action identified
                # check next few data points to confirm start of move action
                for k in range(j+1, j+4):
                    try:
                        next_acc_vals = np_imu_data[k, :3]

                    except IndexError:
                        # if index is out of range, move to next window
                        break

                    if not ((abs(next_acc_vals[0]) > x_thresh) or (abs(next_acc_vals[1]) > y_thresh) or (abs(next_acc_vals[2]) > z_thresh)):
                        # not the start of move action, move to next window
                        break
                else:
                    # confirmed start of move action
                    np_imu_data = np_imu_data[j:]

                    return np_imu_data.T

        return None


    def AI_actual(self, imu_data):
        global prediction_array, ol,dma, input_buffer, output_buffer, NUM_INPUT
        
        parsed_imu_data = self.detect_start_of_move(imu_data)

        if parsed_imu_data is None:
            return None

        mapping = {0: 'logout', 1: 'shield', 2: 'reload', 3: 'grenade', 4: 'idle'}
        features = self.extract_features(parsed_imu_data)

        for i in range(NUM_INPUT):
            input_buffer[i] = features[i]

        run = True

        while run:
            try:
                dma.sendchannel.transfer(input_buffer)
                dma.recvchannel.transfer(output_buffer)
                dma.sendchannel.wait()
                dma.recvchannel.wait()

                action = output_buffer[0]

                prediction_array.append(action)
                print('Predicted class:', action, mapping[action])
                
                run = False
                if not mapping[action] == 'idle':
                    action_queue.put(mapping[action])

            except RuntimeError as e:
                print(e)
                print("Error config: ", dma.register_map)


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
                isPlayerOneGrenadeActivated.clear()
            elif message.payload == b'15_CHECK_grenade_p2_miss':
                print("[MQTT] Player 2 is not in grenade range")     
                action_p1_queue.put('grenade_p2_misses') 
                isPlayerOneGrenadeActivated.clear()
                # action_queue.put('grenade_p2_misses')
            elif message.payload == b'14_CHECK_grenade_p1_hit':
                print("[MQTT] Player 1 is in grenade range")
                action_p2_queue.put('grenade_p1_hits')
                isPlayerTwoGrenadeActivated.clear()
            elif message.payload == b'15_CHECK_grenade_p1_miss':
                print("[MQTT] Player 1 is not in grenade range")      
                action_p2_queue.put('grenade_p1_misses')
                isPlayerTwoGrenadeActivated.clear() 
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
    eval_client = Evaluation_Client('137.132.92.184', 9999, 2)
    # eval_client = Evaluation_Client('localhost', 11001, 2)
    eval_client.daemon = True
    eval_client.start()

    game_engine = Game_Engine() 
    game_engine.daemon = True
    game_engine.start()

    mqtt = MQTT_Client('cg4002/gamestate', 'cg4002/visualizer', 'ultra96', 2)
    mqtt.daemon = True
    mqtt.start()

    HOST, PORT = "192.168.95.235", 11000
    server = Relay_Server(HOST, PORT)
    server.daemon = True
    server.start()

    mqtt.client.loop_forever()

if __name__ == "__main__":
    main()