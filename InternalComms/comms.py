import multiprocessing as mp
import os
import signal
from socket import *
import sys
import struct
import threading
from crccheck.crc import Crc8
import time
import datetime
from bluepy.btle import DefaultDelegate, Peripheral, Scanner, BTLEDisconnectError
import csv

# the peripheral class is used to connect and disconnect

# timeouts in seconds
CONNECTION_TIMEOUT = 3

Service_UUID =  "0000dfb0-0000-1000-8000-00805f9b34fb"
Characteristic_UUID = "0000dfb1-0000-1000-8000-00805f9b34fb"
dataBuffer = mp.Queue()

# serialSvc = dev.getServiceByUUID(
#     "0000dfb0-0000-1000-8000-00805f9b34fb")
# serialChar = serialSvc.getCharacteristics(
#     "0000dfb1-0000-1000-8000-00805f9b34fb")[0]

macAddresses = {
    1: "D0:39:72:BF:BF:BB", #imu1
    2: "D0:39:72:BF:C6:07", #VEST1
    3: "D0:39:72:BF:C3:BF", #GUN1
    4: "D0:39:72:BF:C8:A8", #IMU2
    5: "D0:39:72:BF:BF:DD", #vest2
    6: "D0:39:72:BF:C8:CF" #gun2
}

DATA_PACKET_SIZE = 20

SYN_FLAGS = [False] * 6
ACK_FLAGS = [False] * 6

# Device IDs
IMU_PLAYER_1 = 1
VEST_PLAYER_1= 2
GUN_PLAYER_1 = 3
IMU_PLAYER_2 = 4
VEST_PLAYER_2 = 5
GUN_PLAYER_2 = 6

SYN_PACKET = 'S'
ACK_PACKET = 'A'
MOTION_PACKET = 'M'
AMMO_PACKET = 'B'
HEALTH_PACKET = 'H'

class CheckSumFailedError(Exception):
    pass

# each beetle has a delegate to handle BLE transactions
class MyDelegate(DefaultDelegate):
    def __init__(self, playerId, deviceId, dataBuffer, lock, receivingBuffer, hasHandshaken, serialSvc, serialChar):
        DefaultDelegate.__init__(self)
        self.playerId = playerId
        self.deviceId = deviceId
        self.lock = lock
        self.hasHandshaken = hasHandshaken
        self.dataBuffer = dataBuffer
        self.receivingBuffer = receivingBuffer
        self.serialSvc = serialSvc
        self.serialChar = serialChar
        self.motionPacketsCount = 0
        self.gunPacketsCount = 0
        self.fragPacketsCount = 0
        self.startTime = None
        self.endTime = None
        self.transmissionSpeed = 0

    def sendAckPacket(self):
        self.serialChar.write(bytes("A", "utf-8"))

    def handleAckPacket(self):
        ACK_FLAGS[self.deviceId] = True
        print("received ack from beetle")
        self.serialChar.write(bytes('A', encoding="utf-8"))
        print("HandshakeCompleted")
        self.sendAckPacket()
        self.hasHandshaken = True
        # self.startTime = time.time()
        # self.startTime = datetime.now()

    def checkSum(self, data):
        packet = struct.unpack('<20b', data)
        checksum = 0

        for i in range(19):
            checksum = (checksum ^ packet[i])

        if checksum == packet[19]:
            return True
        else:
            return False
    def handleCheckSumError(self, data):
        # If there is a problem, then drop
        self.receivingBuffer = b''
        print("Checksum failed for device", self.deviceId ,", packet dropped")

    def savedata(self, data):
        
        
        motiondata = data['motionData']
        row = list(motiondata.values())
        # define CSV filename
        filename = 'data.csv'

        # open file in write mode
        with open(filename, mode='a', newline='') as file:
            
            # create a writer object
            writer = csv.writer(file)
            
            # write header row
            # writer.writerow(['First Name', 'Last Name', 'Age'])
            
            # write data rows
            # for row in data
                # writer.writerow(row)
            writer.writerow(row)
                
        # print(f"Data saved to {filename} successfully.")
        print("DATA SAVED:", row)


    def handleNotification(self, cHandle, data):
        try:
            self.receivingBuffer += data
            if len(self.receivingBuffer) >=20:
                # print("Data received from beetle: ", self.receivingBuffer)
                # self.endTime = time.time()
                # self.endTime = datetime.now()
                # self.transmissionSpeed = (self.motionPacketsCount + self.gunPacketsCount + self.fragPacketsCount) * 8 / (1000 * (self.endTime - self.startTime).total_seconds())
                # if self.endTime - self.startTime > 10:
                #     self.transmissionSpeed = (self.motionPacketsCount + self.gunPacketsCount + self.fragPacketsCount) * 8 / 10

                dataPacket = self.receivingBuffer[0:20]
                if not self.checkSum(dataPacket):
                    raise CheckSumFailedError("Checksum failed")
                unpackedPacket = ()
                expectedPacketFormat = ("bb6h5xb")
                unpackedPacket = struct.unpack_from(expectedPacketFormat, dataPacket, 0)
                # dataPacket = dataPacket[::-1]
                # print(unpackedPacket)
                # print(unpackedPacket[0], len(unpackedPacket))
                packetType = chr(unpackedPacket[0])
                print("packetType, deviceId, length ", packetType , "," , self.deviceId,
                      ",", len(self.receivingBuffer) )
                # , ",", self.transmissionSpeed, "kbps"
                print("Fragmented Packets Count for device:", self.deviceId, ":", self.fragPacketsCount)
                if packetType == 'A':
                    self.handleAckPacket()
                if packetType == 'M':
                    sendData = {
                        "playerID": self.playerId,
                        "beetleID": self.deviceId,
                        "motionData": {
                            "aX": unpackedPacket[2],
                            "aY": unpackedPacket[3],
                            "aZ": unpackedPacket[4],
                            "gX": unpackedPacket[5],
                            "gY": unpackedPacket[6],
                            "gZ": unpackedPacket[7]
                        }
                    }
                    self.motionPacketsCount += 1
                    print("MotionPacketsCount: ", self.motionPacketsCount)
                    print(sendData)
                    # self.savedata(sendData)
                    self.lock.acquire()
                    self.dataBuffer.put(sendData)
                    self.lock.release()
                if packetType == 'B' or packetType == 'H':
                    expectedPacketFormat = ("bb?16xb")
                    self.gunPacketsCount += 1
                    print("GunPacketsCount: ", self.gunPacketsCount)
                    unpackedPacket = struct.unpack_from(expectedPacketFormat, dataPacket, 0)
                    sendData = {
                        "playerID": self.playerId,
                        "beetleID": self.deviceId,
                        "hit": unpackedPacket[2],
                    }
                    print(sendData)
                    self.lock.acquire()
                    self.dataBuffer.put(sendData)
                    self.lock.release()
                    self.sendAckPacket()
                self.receivingBuffer = b''
            else:
                self.fragPacketsCount += 1
                self.receivingBuffer = self.receivingBuffer + data
                if len(self.receivingBuffer) == 20:
                    self.handleNotification(None, self.receivingBuffer)
                self.receivingBuffer = b''

        except CheckSumFailedError:
            self.handleCheckSumError(data)

        except ValueError:
            pass


    def checkCRC(self, length):
        calcChecksum = Crc8.calc(self.buffer[0: length])
        return calcChecksum == self.buffer[length]


class BeetleConnectionThread:
    def __init__(self, playerId, beetleId, macAddress, dataBuffer, lock, receivingBuffer):
        self.beetleId = beetleId
        self.macAddress = macAddress
        self.dataBuffer = dataBuffer
        self.playerId = playerId
        self.dev = None
        self.deleg = None
        self.lock = lock
        self.serialSvc = None
        self.serialChar = None
        self.receivingBuffer = receivingBuffer
        self.hasHandshaken = False

        if self.beetleId == GUN_PLAYER_1 or self.beetleId == GUN_PLAYER_2:
            self.isReload = False

    def writetoBeetle(self):
        pass

    def openBeetleConnection(self):
        # while True:
        try:
            self.dev = Peripheral(self.macAddress)
            print("Connected to Beetle: ", self.macAddress)
            self.serialSvc = self.dev.getServiceByUUID(Service_UUID)
            self.serialChar = self.serialSvc.getCharacteristics(Characteristic_UUID)[0]
            deviceDelegate = MyDelegate(self.playerId, self.beetleId, self.dataBuffer, self.lock,
                                        self.receivingBuffer, self.hasHandshaken, self.serialSvc, self.serialChar)
            self.dev.withDelegate(deviceDelegate)
            return True
            # break
        except BTLEDisconnectError:
            print("Connection failed")
            return False
            # return


    def startThreeWayHandshake(self, hasHandshake):

        while not hasHandshake:
            self.dev.waitForNotifications(1.0)

            if not SYN_FLAGS[self.beetleId]:
                print("sending syn to beetle")
                self.serialChar.write(bytes('S', encoding="utf-8"))
                SYN_FLAGS[self.beetleId] = True
            if ACK_FLAGS[self.beetleId]:
                print("received ack from beetle")
                self.serialChar.write(bytes('A', encoding="utf-8"))
                hasHandshake = True
                print("HandshakeCompleted")
        return hasHandshake

    def checkForReload(self):
        if self.isReload == 1:
            self.serialChar.write(bytes("R", encoding = "utf-8"))

    def sendSynMessage(self):
        # self.dev.waitForNotifications(1.0)
        if not SYN_FLAGS[self.beetleId]:
            print("sending syn to beetle")
            self.serialChar.write(bytes('S', encoding="utf-8"))
            SYN_FLAGS[self.beetleId] = True

    def executeCommunications(self):
        # connect to beetle
        hasHandshake = False
        isConnected = False
        while True:
            try:
                if not hasHandshake:
                    if not isConnected:
                        isConnected = self.openBeetleConnection()
                    # hasHandshake = self.startThreeWayHandshake(hasHandshake)
                    self.sendSynMessage()

                if hasHandshake:
                    self.dev.waitForNotifications(1)
                    if self.beetleId == GUN_PLAYER_1 or self.beetleId == GUN_PLAYER_2:
                        self.checkForReload(self.serialChar)

                if SYN_FLAGS[self.beetleId] and ACK_FLAGS[self.beetleId]:
                    hasHandshake = True
                if not self.dev.waitForNotifications(CONNECTION_TIMEOUT):
                    print('disconnecting')
                    self.hasHandshaken = False
                    isConnected = False
                    hasHandshake = False
                    SYN_FLAGS[self.beetleId] = False
                    ACK_FLAGS[self.beetleId] = False
                    self.dev.disconnect()
                    # continue
            except KeyboardInterrupt:
                self.dev.disconnect()
                print('Disconnecting from beetle ', self.beetleId)
                self.hasHandshaken = False
                isConnected = False
                hasHandshake = False
                SYN_FLAGS[self.beetleId] = False
                ACK_FLAGS[self.beetleId] = False
            except (BTLEDisconnectError, AttributeError):
                print("Device Disconnected")
                self.hasHandshaken = False
                isConnected = False
                hasHandshake = False
                SYN_FLAGS[self.beetleId] = False
                ACK_FLAGS[self.beetleId] = False

            except Exception as e:
                print("Unexpected error:", sys.exc_info()[0])
                print(e.__doc__)
                print(e.message)






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
                msg = dataBuffer.get()
                # input("Press any button to send data")
                # msg = str(IMU)
                # msg = str(len(msg)) + '_' + msg
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
        


def executeThreads():
    # create threads

    # lock is used to acquire the objects like mutex, so that the dataBuffer is not written in by the other threads
    lock = mp.lock()

    # using a multiprocessing queue FIFO
    dataBuffer = mp.Queue()

    # Player 1
    IMU1_Beetle = BeetleConnectionThread(1, IMU_PLAYER_1, macAddresses.get(1), dataBuffer, lock)
    IMU1_Thread = threading.Thread(target=IMU1_Beetle.executeCommunications())

    Gun1_Beetle = BeetleConnectionThread(1, GUN_PLAYER_1, macAddresses.get(3), dataBuffer, lock)
    Gun1_Thread = threading.Thread(target=Gun1_Beetle.executeCommunications())

    Vest1_Beetle = BeetleConnectionThread(1, VEST_PLAYER_1, macAddresses.get(2), dataBuffer, lock)
    Vest1_Thread = threading.Thread(target=Vest1_Beetle.executeCommunications())

    # Player 2
    IMU2_Beetle = BeetleConnectionThread(2, IMU_PLAYER_2, macAddresses.get(4), dataBuffer, lock)
    IMU2_Thread = threading.Thread(target=IMU2_Beetle.executeCommunications())

    Gun2_Beetle = BeetleConnectionThread(2, GUN_PLAYER_2, macAddresses.get(6), dataBuffer, lock)
    Gun2_Thread = threading.Thread(target=Gun2_Beetle.executeCommunications())

    Vest2_Beetle = BeetleConnectionThread(2, VEST_PLAYER_2, macAddresses.get(5), dataBuffer, lock)
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


if __name__ == '__main__':
    try:
        lock = mp.Lock()
        

        # using a multiprocessing queue FIFO
        # dataBuffer = mp.Queue()
        receivingBuffer1 = b''
        receivingBuffer2 = b''
        receivingBuffer3 = b''
        # IMU2_Beetle = BeetleConnectionThread(2, IMU_PLAYER_2, macAddresses.get(4), dataBuffer, lock, receivingBuffer)
        # IMU2_Beetle.executeCommunications()

        # # Devices 234
        # Gun1_Beetle = BeetleConnectionThread(1, GUN_PLAYER_1, macAddresses.get(3), dataBuffer, lock, receivingBuffer1)
        # Gun1_Thread = threading.Thread(target=Gun1_Beetle.executeCommunications, args = ())

        # Vest1_Beetle = BeetleConnectionThread(1, VEST_PLAYER_1, macAddresses.get(2), dataBuffer, lock, receivingBuffer2)
        # Vest1_Thread = threading.Thread(target=Vest1_Beetle.executeCommunications, args = ())

        # # Player 2
        # IMU2_Beetle = BeetleConnectionThread(2, IMU_PLAYER_2, macAddresses.get(4), dataBuffer, lock, receivingBuffer3)
        # IMU2_Thread = threading.Thread(target=IMU2_Beetle.executeCommunications, args = ())

        # Player 1 (IMU)
        IMU1_Beetle = BeetleConnectionThread(1, IMU_PLAYER_1, macAddresses.get(1), dataBuffer, lock, receivingBuffer3)
        # IMU1_Beetle = BeetleConnectionThread(2, IMU_PLAYER_2, macAddresses.get(4), dataBuffer, lock, receivingBuffer3)
        IMU1_Thread = threading.Thread(target=IMU1_Beetle.executeCommunications, args = ())
        # relay_thread = Relay_Client('172.20.10.2', 11000)
        
        

        # Gun1_Thread.daemon = True
        # Vest1_Thread.daemon = True
        # IMU2_Thread.daemon = True

        # Gun1_Thread.start()
        # Vest1_Thread.start()
        # IMU2_Thread.start()

        # Gun1_Thread.join()
        # Vest1_Thread.join()
        # IMU2_Thread.join()

        IMU1_Thread.start()
        # relay_thread.start()
        IMU1_Thread.join()
        # relay_thread.join()

        # while True: time.sleep(100)

        # signal.pause()

    except (KeyboardInterrupt, SystemExit):
        print("Ended Comms")
        # sys.exit()
