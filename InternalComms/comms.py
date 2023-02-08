import multiprocessing as mp
import os
from socket import *
import threading
from crccheck.crc import Crc8

from bluepy.btle import DefaultDelegate, Peripheral, Scanner, BTLEDisconnectError

# the peripheral class is used to connect and disconnect

macAddresses = {
    1: "D0:39:72:BF:BF:BB", #imu1
    2: "D0:39:72:BF:C6:07", #gun1
    3: "D0:39:72:BF:BF:DD", #vest1
    4: "",
    5: "",
    6: ""
}

DATA_PACKET_SIZE = 20

# Device IDs
IMU_PLAYER_1 = 1
GUN_PLAYER_1 = 2
VEST_PLAYER_1 = 3
IMU_PLAYER_2 = 4
GUN_PLAYER_2 = 5
VEST_PLAYER_2 = 6

SYN_PACKET = 'S'
ACK_PACKET = 'A'
MOTION_PACKET = 'M'
AMMO_PACKET = 'B'
HEALTH_PACKET = 'H'


# each beetle has a delegate to handle BLE transactions
class MyDelegate(DefaultDelegate):
    def __init__(self, playerId, deviceId, dataBuffer, lock):
        DefaultDelegate.__init__(self)
        self.playerId = playerId
        self.deviceId = deviceId
        self.lock = lock
        self.hasHandshaken = False
        self.dataBuffer = dataBuffer

    def sendAckPacket(self):
        self.serialChar.write(bytes("A", "utf-8"))

    def handleAckPacket(self):
        self.sendAckPacket()
        self.hasHandshaken = True

    def handleNotification(self,cHandle, data):
        self.buffer +=data

    def checkCRC(self, length):
        calcChecksum = Crc8.calc(self.buffer[0: length])
        return calcChecksum == self.buffer[length]

class BeetleConnectionThread:
    def __init__(self, playerId, beetleId, macAddress, dataBuffer, lock):
        self.beetleId = beetleId
        self.macAddress = macAddress
        self.dataBuffer = dataBuffer
        self.playerId = playerId
        self.dev = None
        self.deleg = None
        self.lock = lock


    def writetoBeetle(self):
        pass

    def openBeetleConnection(self):
        while 1:
            try:
                self.dev = Peripheral(self.macAddress)
                print("Connected to Beetle: ", self.macAddress)
                deviceDelegate = MyDelegate(self.playerId, self.beetleId, self.dataBuffer, self.lock)
                self.dev.setDelegate(deviceDelegate)
                break
            except BTLEDisconnectError:
                print("Connection failed")
                return

    def startThreeWayHandshake(self):
        hasHandshake = False
        while not hasHandshake:
            self.dev.waitForNotifications(1.0)

    def executeCommunications(self):
        # connect to beetle
        self.openBeetleConnection()
        self.startThreeWayHandshake()

        pass

if __name__ == '__main__':
    # create threads

    # lock is used to acquire the objects like mutex, so that the dataBuffer is not written in by the other threads
    lock = mp.lock()

    # using a multiprocessing queue FIFO
    dataBuffer = mp.Queue()

    # Player 1
    IMU1_Beetle = BeetleConnectionThread(1, IMU_PLAYER_1, macAddresses.get(1), dataBuffer, lock)
    IMU1_Thread = threading.Thread(target=IMU1_Beetle.executeCommunications())

    Gun1_Beetle = BeetleConnectionThread(1, GUN_PLAYER_1, macAddresses.get(2), dataBuffer, lock)
    Gun1_Thread = threading.Thread(target=Gun1_Beetle.executeCommunications())

    Vest1_Beetle = BeetleConnectionThread(1, VEST_PLAYER_1, macAddresses.get(3), dataBuffer, lock)
    Vest1_Thread = threading.Thread(target=Vest1_Beetle.executeCommunications())

    # Player 2
    IMU2_Beetle = BeetleConnectionThread(2, IMU_PLAYER_2, macAddresses.get(4), dataBuffer, lock)
    IMU2_Thread = threading.Thread(target=IMU2_Beetle.executeCommunications())

    Gun2_Beetle = BeetleConnectionThread(2, GUN_PLAYER_2, macAddresses.get(5), dataBuffer, lock)
    Gun2_Thread = threading.Thread(target=Gun2_Beetle.executeCommunications())

    Vest2_Beetle = BeetleConnectionThread(2, VEST_PLAYER_2, macAddresses.get(6), dataBuffer, lock)
    Vest2_Thread = threading.Thread(target=Vest2_Beetle.executeCommunications())

    IMU1_Thread.start()
    Gun1_Thread.start()
    Vest1_Thread.start()

    # IMU2_Thread.start()
    # Gun2_Thread.start()
    # Vest2_Thread.start()

    IMU1_Thread.join()
    Gun1_Thread.join()
    Vest1_Thread.join()

    # IMU2_Thread.join()
    # Gun2_Thread.join()
    # Vest2_Thread.join()



