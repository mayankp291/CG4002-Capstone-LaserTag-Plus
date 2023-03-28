from socket import *
import os
import time
import threading
import random
import sys



# IMU = {'x': 0, 'y': 0, 'z': 0}
IMU = {'playerID': 2, 'beetleID': 4, 'sensorData': {'aX': 409, 'aY': 158, 'aZ': 435, 'gX': 265, 'gY': 261, 'gZ': 261}}
test = {'playerID': 2, 'beetleID': 7, 'sensorData': None}



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
            match = {0:"logout", 1:"shoot", 2:"grenade", 3:"shield", 4:"reload", 5:"shoot_p2_hits", 6:"shoot_p1_hits"}	
            while True:
                print(match)
                a = input("Press any button to send data")
                test['sensorData'] = (match[int(a[0])], match[int(a[1])])
                msg = str(test)
                # msg = str(IMU)
                # msg = str(len(msg)) + '_' + msg
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

    relay_thread = Relay_Client('localhost', 11000)
    relay_thread.start()
    # relay_thread2 = Relay_Client('localhost', 11000)
    # relay_thread2.start()
    
if __name__ == "__main__":
    main()