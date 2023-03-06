from socket import *
import sshtunnel
from paramiko import SSHClient
import os
from dotenv import load_dotenv
import time
import threading
import random
import sys

# load environment variables
load_dotenv()


# IMU = {'x': 0, 'y': 0, 'z': 0}
IMU = {'playerID': 2, 'beetleID': 4, 'sensorData': {'aX': 409, 'aY': 158, 'aZ': 435, 'gX': 265, 'gY': 261, 'gZ': 261}}


SOC_USERNAME = os.getenv("SOC_USERNAME")
SOC_PASSWORD = os.getenv("SOC_PASSWORD")
SOC_IP = os.getenv("SOC_IP")
PORT_BIND = int(os.getenv("PORT"))

ULTRA96_USERNAME = os.getenv("ULTRA96_USERNAME")
ULTRA96_PASSWORD = os.getenv("ULTRA96_PASSWORD")
ULTRA96_IP = os.getenv("ULTRA96_IP")


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
    
    @staticmethod
    def tunnel_ultra96():
    # open tunnel to soc.comp.nus.edu.sg server
        tunnel_soc = sshtunnel.open_tunnel(
            ssh_address_or_host = (SOC_IP, 22),
            remote_bind_address = (ULTRA96_IP, 22),
            ssh_username = SOC_USERNAME,
            ssh_password = SOC_PASSWORD,
            block_on_close = False
            )
        tunnel_soc.start()
        
        print('Tunnel into SOC Server successful, at port: ' + str(tunnel_soc.local_bind_port))

        # open tunnel from soc.comp.nus.edu.sg server to ultra96
        tunnel_ultra96 = sshtunnel.open_tunnel(
            ssh_address_or_host = ('localhost', tunnel_soc.local_bind_port),
            # bind port from localhost to ultra96
            remote_bind_address=('localhost', PORT_BIND),
            ssh_username = ULTRA96_USERNAME,
            ssh_password = ULTRA96_PASSWORD,
            local_bind_address = ('localhost', PORT_BIND), #localhost to bind it to
            block_on_close = False
            )
        tunnel_ultra96.start()
        print('Tunnel into Ultra96 successful, local bind port: ' + str(tunnel_ultra96.local_bind_port))


    def send(self, message):
        self.relaySocket.send(message.encode('utf-8'))
        # print('Sent message to Relay Server', message)
        print('Sent packet to Relay Server', end='\r')       
        


def main():
    # Relay_Client.tunnel_ultra96()
    relay_thread = Relay_Client('localhost', 11000)
    relay_thread.start()
    # relay_thread2 = Relay_Client('localhost', 11000)
    # relay_thread2.start()
    
if __name__ == "__main__":
    main()