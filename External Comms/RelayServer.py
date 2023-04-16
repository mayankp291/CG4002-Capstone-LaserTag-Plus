from multiprocessing import Process, Queue, Event
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from ast import literal_eval
import base64
import numpy as np
import traceback
import json
from constants import *


class RelayServerSend(Process):
    """
    A process that sends updated states to the relay laptop.
    """

    def __init__(self, sock, intcomms_queue, reloadSendRelayP1, reloadSendRelayP2):
        """
        Initializes the RelayServerSend process.

        Args:
        sock (socket.socket): The socket object used to communicate with the server.
        intcomms_queue (Queue): The queue used to receive updated states from other processes.
        reloadSendRelayP1 (Event): An event flag indicating that player 1 has reloaded.
        reloadSendRelayP2 (Event): An event flag indicating that player 2 has reloaded.
        """
        super().__init__()
        self.sock = sock
        self.intcomms_queue = intcomms_queue
        self.reloadSendRelayP1 = reloadSendRelayP1
        self.reloadSendRelayP2 = reloadSendRelayP2
        print("[RELAY_SEND] Ready to send data to Relay")

    def run(self):
        """
        Runs the RelayServerSend process, sending data to the relay server.
        """
        while True:
            send_data = self.intcomms_queue.get()
            send_data = json.loads(send_data)

            # keep action as reload if player has reloaded
            if self.reloadSendRelayP1.is_set() and self.reloadSendRelayP2.is_set():
                self.reloadSendRelayP1.clear()
                self.reloadSendRelayP2.clear()

            elif self.reloadSendRelayP1.is_set():
                self.reloadSendRelayP1.clear()
                send_data['p2']['action'] = 'none'

            elif self.reloadSendRelayP2.is_set():
                self.reloadSendRelayP2.clear()
                send_data['p1']['action'] = 'none'

            self.send(send_data)

    def send(self, data):
        """
        Sends the given data to the relay laptop.

        Args:
        data (dict): The data to send to the relay laptop.
        """
        try:
            data = str(data)
            self.sock.sendall(data.encode("utf-8"))
            print('[RELAY_SEND] Sent to Relay Laptop: {}'.format(data))
        except Exception as e:
            print('Connection to Relay Laptop lost')
            print(e)


# TCP Server to receive data from the Relay Laptops

class RelayServer(Process):
    """
    A process that receives data from the relay laptop.
    """

    def __init__(self, host, port, relay_flag, processing_flag, shoot_p1_hit, shoot_p2_hit, imu_queue_p1, imu_queue_p2,
                 action_p1_queue, action_p2_queue, intcomms_queue, reloadSendRelayP1, reloadSendRelayP2):
        """
        Initializes the RelayServer process.

        Args:
        host (str): The host address of the server.
        port (int): The port number of the server.
        relay_flag (Event): An event flag to make sure that only one thread is created to send data to relay laptop.
        processing_flag (Event): An event flag indicating that the game engine is running and AI needs to be halted.
        shoot_p1_hit (Event): An event flag indicating that player 1 has been hit.
        shoot_p2_hit (Event): An event flag indicating that player 2 has been hit.
        imu_queue_p1 (Queue): The queue used to transfer player 1 IMU data across processes.
        imu_queue_p2 (Queue): The queue used to transfer player 2 IMU data across processes.
        action_p1_queue (Queue): The queue used to transfer player 1 actions data across processes.
        action_p2_queue (Queue): The queue used to transfer player 2 actions data across processes.
        """
        super().__init__()
        self.host = host
        self.port = port
        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.relay_flag = relay_flag
        self.processing_flag = processing_flag
        self.imu_queue_p1 = imu_queue_p1
        self.imu_queue_p2 = imu_queue_p2
        self.shoot_p1_hit = shoot_p1_hit
        self.shoot_p2_hit = shoot_p2_hit
        self.action_p1_queue = action_p1_queue
        self.action_p2_queue = action_p2_queue
        self.intcomms_queue = intcomms_queue
        self.reloadSendRelayP1 = reloadSendRelayP1
        self.reloadSendRelayP2 = reloadSendRelayP2

    def run(self):
        """
        Runs the RelayServer process, receiving data from the relay server.
        """
        self.server.listen(1)
        print("[RELAY SERVER] Listening for connections on host {} port {} \n".format(
            self.host, self.port))
        while True:
            client, address = self.server.accept()
            print("[RELAY SERVER] Client connected from {} \n".format(address))
            client_handler = Process(
                target=self.handle_client,
                args=(client)
            )
            client_handler.start()

    ###
    # Data flow: get len, get msg, check len == len(msg), convert msg to dict
    ###
    def handle_client(self, request):
        """
        Handles a client connection.

        Args:
        request (socket.socket): The socket object used to communicate with the client.
        """
        try:
            # to start only one thread to send data to relay laptop
            if self.relay_flag.is_set():
                self.relay_flag.clear()
                sending_thread = RelayServerSend(
                    request, self.intcomms_queue, self.reloadSendRelayP1, self.reloadSendRelayP2)
                sending_thread.start()

            while True:
                # receive data from client
                # (protocol) len(data)_dataRELAY_SEND
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

                # check length of data
                if length != len(data):
                    print("Error", data)
                    print('Error: packet length does not match, packet dropped')

                else:
                    # convert data to dict {'playerID':, 'beetleID':, 'sensorData':}
                    data = literal_eval(data)

                    # process incoming data
                    beetleID = data["beetleID"]

                    data_device = beetleID_mapping[beetleID]

                    # process data according to beetleID
                    if not self.processing_flag.is_set() and (data_device == "IMU1" or data_device == "IMU2"):
                        # convert string to numpy array of ints
                        new_array = np.frombuffer(base64.binascii.a2b_base64(
                            data["sensorData"]), dtype=np.int32).reshape(SAMPLE_SIZE, 6)
                        # print(new_array, new_array.shape)
                        if data_device == "IMU1":
                            self.imu_queue_p1.put(('p1', new_array))
                        else:
                            self.imu_queue_p2.put(('p2', new_array))

                    # set flag if vest is hit
                    elif data_device == "VEST1":
                        print("VEST 1 RECV")
                        self.shoot_p1_hit.set()

                    elif data_device == "VEST2":
                        print("VEST 2 RECV")
                        self.shoot_p2_hit.set()

                    # add shoot action to queue
                    elif data_device == "GUN1":
                        # shot by player
                        print("GUN 1 RECV")
                        self.action_p1_queue.put("shoot")

                    elif data_device == "GUN2":
                        print("GUN 2 RECV")
                        self.action_p2_queue.put("shoot")

        except Exception as e:
            print("Client disconnected")
            request.close()
            print(e)
            traceback.print_exc()
