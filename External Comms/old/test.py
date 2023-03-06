import os
import sys
import time
import traceback
import random

import socket

import base64

from tkinter.constants import HORIZONTAL, VERTICAL

from Crypto import Random
from Crypto.Cipher import AES

ENCRYPT_BLOCK_SIZE = 16 
p1_action=None
p2_action=None

class Client:
    def __init__(self, ip_addr, port_num, key):

        self.key = key
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (ip_addr, port_num)
        self.socket.connect(server_address)
        
        
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

        
def main():
    ip_addr = "localhost"
    s_port_num=int(sys.argv[1])
    key = "PLSPLSPLSPLSWORK"

    my_client = Client(ip_addr, s_port_num, key)
    

    while True:
        action=input("action:")
        my_client.send_message(action)
        if action=="logout":
            break


if __name__ == "__main__":
    main()