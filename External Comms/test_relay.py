from socket import *
from paramiko import SSHClient
import os
import time
import threading
import random
import sys


class Relay_Client(threading.Thread):
    def __init__(self, ip, port) -> None:
        super().__init__()
        self.relay_ip = gethostbyname(ip)
        self.relay_port = port
        self.relaySocket = socket(AF_INET, SOCK_STREAM)
        self.relaySocket.connect((self.relay_ip, self.relay_port))
        print('Connected to Relay Server', self.relay_ip, self.relay_port)
        

    def run(self):
        try: 
            while True:
                input("Press any button to send data")
                msg = str(IMU)
                msg = str(len(msg)) + '_' + msg
                self.send(msg)
                # self.recv()
        except:
            print('Connection to Relay Server lost')
            self.relaySocket.close()
            sys.exit()



    def send(self, message):
        self.relaySocket.send(message.encode('utf-8'))
        # print('Sent message to Relay Server', message)
        print('Sent packet to Relay Server', end='\r')       
        


def main():
    # Relay_Client.tunnel_ultra96()
    relay_thread = Relay_Client('172.20.10.2', 11000)
    relay_thread.start()
    # relay_thread2 = Relay_Client('localhost', 11000)
    # relay_thread2.start()
    
if __name__ == "__main__":
    main()