from ipaddress import ip_address
from logging import shutdown
import os
import sys
import time
import traceback
import random
from GameState import GameState
import Helper
from PlayerState import PlayerStateBase
import json
import socket
import threading
import pika
import base64
import tkinter as tk
from tkinter import ttk
from tkinter.constants import HORIZONTAL, VERTICAL
import pandas as pd
from Crypto import Random
from Crypto.Cipher import AES

p1_action=None
p2_action=None
state=GameState()
event_send_to_server=threading.Event()
event_send_to_phone1=threading.Event()
event_send_to_phone2=threading.Event()
p1_pos=1
p2_pos=1
#when both true, move one step
p1_flag=False
p2_flag=False
_shutdown=threading.Event()
single_player_mode=True

pc_ip_address="172.27.212.54"

LOG_DIR = os.path.join(os.path.dirname(__file__), 'evaluation_logs')
MESSAGE_SIZE = 2 
ACTIONS = ["shoot", "shield", "grenade", "reload"]
NUM_ACTION_REPEATS = 4
ENCRYPT_BLOCK_SIZE = 16 
class Publisher(threading.Thread):
    def __init__(self,queueName,player):
        super(Publisher, self).__init__()
        self.player=player#indicates player 1 or 2
        self.queueName=queueName
        credentials = pika.PlainCredentials('admin1', 'admin123')#username,password
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(pc_ip_address,5672,'/',credentials))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queueName)
    
    def run(self):
        
        global state
        
        while True:
            if self.player==1:
                event_send_to_phone1.wait()
            else:
                event_send_to_phone2.wait()
            self.channel.basic_publish(exchange='', routing_key=self.queueName, body=state._get_data_plain_text_phone())
            print("sending message in rabbitmq:")
            print(state._get_data_plain_text_phone())    
            if self.player==1:
                event_send_to_phone1.clear()
            else: event_send_to_phone2.clear()
            if _shutdown.is_set():
                self.connection.close()
                sys.exit()
                


class Server(threading.Thread):
    def __init__(self, ip_addr, port_num, player_index):
        super(Server, self).__init__()
        self.player_index=player_index
        
        
        self.connection = None              
        self.has_no_response = False        
        self.logout = False                 

        # Create a TCP/IP socket and bind to port
        self.shutdown = threading.Event()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (ip_addr, port_num)

        self.socket.bind(server_address)



    def run(self):
        global single_player_mode
        
        global p1_action
        global p2_action
        global p1_flag
        global p2_flag
        global state
        global p1_pos
        global p2_pos
        # Listen for incoming connections
        self.socket.listen(1)

        self.client_address, self.secret_key = self.setup_connection()      # Wait for secret key 

        
        while not self.shutdown.is_set():           # Stop waiting for data if we received a shutdown signal

                data = self.connection.recv(1024)       # Blocking wait for data
                update_pos_flag=False
                if data:
                    try:
                        msg = data.decode("utf8")                           # Decode raw bytes to UTF-8
                        decrypted_message = self.decrypt_message(msg)       # Decrypt message using secret key
                        # If no valid action was sent
                        if len(decrypted_message) == 0:
                            pass
                        
                        else:
                            self.has_no_response = False
                            action=decrypted_message
                            print(f"received: player{self.player_index}:{action}")
                            if self.player_index==1 and p1_flag==False:
                                p1_flag=True
                                p1_action=action
                                if p1_action=="logout":
                                    self.shutdown.set()
                                    _shutdown.set() #event for other threads
                                    #break
                                if single_player_mode:
                                    p2_action="none"
                                    p2_flag=True
                            elif self.player_index==2 and p2_flag==False:
                                p2_flag=True
                                p2_action=action
                            if p1_flag and p2_flag:
                                p1_flag=False
                                p2_flag=False
                                try:
                                    p1_pos = int(p1_action)
                                    p1_action="none"#not reached unless p1_action is a int, which leads to updating position
                                    update_pos_flag=True
                                except ValueError:
                                    if p1_pos==0: #previously disconnected
                                        p1_pos=1
                                try:
                                    p2_pos = int(p2_action)
                                    p2_action="none"
                                    update_pos_flag=True
                                except ValueError:
                                    if p2_pos==0:
                                        p2_pos=1
                                
                                # check if actions are valid actions
                                action_p1_is_valid = state.player_1.action_is_valid(p1_action)
                                action_p2_is_valid = state.player_2.action_is_valid(p2_action)

                                # change the state of player 1
                                state.player_1.update(p1_pos, p2_pos, p1_action, p2_action, action_p2_is_valid)

                                # change the state of player 2
                                state.player_2.update(p2_pos, p1_pos, p2_action, p1_action, action_p1_is_valid)

                                
                                if not update_pos_flag:
                                    event_send_to_server.set()
                                    event_send_to_phone1.set()
                                    if not single_player_mode:
                                        event_send_to_phone2.set()
                    except Exception as e:
                        traceback.print_exc()
                else:
                    print('no more data from', self.client_address)
                    self.stop()



    def setup_connection(self):

        # Wait for a connection
        print('Waiting for a connection')
        self.connection, client_address = self.socket.accept()

        print("Enter the secret key: ")
        secret_key = sys.stdin.readline().strip()

        print('connection from', client_address)
        
        return client_address, secret_key


    
    def decrypt_message(self, cipher_text):       
        decoded_message = base64.b64decode(cipher_text)                             # Decode message from base64 to bytes
        iv = decoded_message[:16]                                                   # Get IV value
        secret_key = bytes(str(self.secret_key), encoding="utf8")                   # Convert secret key to bytes

        cipher = AES.new(secret_key, AES.MODE_CBC, iv)                              # Create new AES cipher object
        decrypted_message = cipher.decrypt(decoded_message[16:]).strip()            # Perform decryption
        decrypted_message = decrypted_message.decode('utf8')                        # Decode bytes into utf-8

        decrypted_message = decrypted_message[decrypted_message.find('#'):]         # Trim to start of response string
        decrypted_message = bytes(decrypted_message[1:], 'utf8').decode('utf8')     # Trim starting # character

        return decrypted_message


    def stop(self):
        self.connection.close()
        self.shutdown.set()
        print("bye bye")
        sys.exit()


class Client(threading.Thread):
    def __init__(self, ip_addr, port_num, key):
        super(Client, self).__init__()

        self.idx = 0
        self.timeout = 60
        self.has_no_response = False

        self.logout = False

        
        self.key = key
        
        
        self.shutdown = threading.Event()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (ip_addr, port_num)
        self.socket.connect(server_address)
        print("Connected")
        
    # To encrypt the message, which is a string
    def encrypt_message(self, message):
        raw_message = "#" + message
        padded_raw_message = raw_message + " " * (
            ENCRYPT_BLOCK_SIZE - (len(raw_message) % ENCRYPT_BLOCK_SIZE)
        )
        iv = Random.new().read(AES.block_size)
        secret_key = bytes(str(self.key), encoding="utf8")
        cipher = AES.new(secret_key, AES.MODE_CBC, iv)
        encrypted_message = base64.b64encode(
            iv + cipher.encrypt(bytes(padded_raw_message, "utf8"))
        )
        return encrypted_message

    # To send the message to the sever
    def send_message(self, message):
        encrypted_message = self.encrypt_message(message)
        self.socket.sendall(encrypted_message)

    def receive_action(self):
        action = self.socket.recv(1024)
        msg = action.decode("utf8")
        return msg

    def stop(self):
        
        self.shutdown.set()

        sys.exit()
    def run(self):
        global p1_action
        global p2_action
        global state


        while not _shutdown.is_set():
            event_send_to_server.wait()
            state.send_encrypted(self.socket,self.key)
            state.recv_and_update(self.socket)
            event_send_to_server.clear()
        
        if _shutdown.is_set():
            self.stop()


def main():
    if len(sys.argv) != 4:
        print('Invalid number of arguments')
        print('python3 eval_client.py [IP address] [Port] [mode]')
        print('mode takes value 1 for single player and 2 for double player')
        sys.exit()
    global single_player_mode
    ip_addr     = sys.argv[1]
    port_num    = int(sys.argv[2])
    if int(sys.argv[3]) == 1:
        single_player_mode = True
    else:
        single_player_mode = False
        
        
    player1=PlayerStateBase()
    player2=PlayerStateBase()
    global state

    s_port_num=8899
    s_port_num_2=8898

    key = "PLSPLSPLSPLSWORK"
    state.init_players(player1,player2) #init game state as if the 2 players are initialized newly
    
    my_client = Client(ip_addr, port_num, key)
    server_1 = Server("localhost", s_port_num, 1)
    publisher1=Publisher("phone1",1)

    server_1.start()
    my_client.start()
    publisher1.start()
    if not single_player_mode:
        server_2 = Server("localhost", s_port_num_2, 2)
        server_2.start()
        publisher2=Publisher("phone2",2)
        publisher2.start()


if __name__ == "__main__":
    main()