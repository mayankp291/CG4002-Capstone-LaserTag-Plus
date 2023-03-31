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

### format for packet
dic = {"playerId": 1, "action": "reload"}

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

# the peripheral class is used to connect and disconnect

# timeouts in seconds
CONNECTION_TIMEOUT = 1

Service_UUID = "0000dfb0-0000-1000-8000-00805f9b34fb"
Characteristic_UUID = "0000dfb1-0000-1000-8000-00805f9b34fb"
dataBuffer = mp.Queue()

gameQueue = mp.Queue()

# serialSvc = dev.getServiceByUUID(
#     "0000dfb0-0000-1000-8000-00805f9b34fb")
# serialChar = serialSvc.getCharacteristics(
#     "0000dfb1-0000-1000-8000-00805f9b34fb")[0]

macAddresses = {
    1: "D0:39:72:BF:BF:BB",  # imu1
    2: "D0:39:72:BF:C6:07",  # VEST1
    3: "D0:39:72:BF:C3:BF",  # GUN1
    4: "D0:39:72:BF:C8:A8",  # IMU2
    5: "D0:39:72:BF:BF:DD",  # vest2
    6: "D0:39:72:BF:C8:CF"  # gun2
}

DATA_PACKET_SIZE = 20

SYN_FLAGS = [False] * 7
ACK_FLAGS = [False] * 7
HANDSHAKE_FLAGS = [False] * 7

# Device IDs
IMU_PLAYER_1 = 1
VEST_PLAYER_1 = 2
GUN_PLAYER_1 = 3
IMU_PLAYER_2 = 4
VEST_PLAYER_2 = 5
GUN_PLAYER_2 = 6

SYN_PACKET = 'S'
ACK_PACKET = 'A'
MOTION_PACKET = 'M'
AMMO_PACKET = 'B'
HEALTH_PACKET = 'H'
RELOAD_PACKET = 'R'
GRENADE_PACKET = 'G'

isReloadFlagGun1 = threading.Event()
isReloadFlagGun1.clear()

isReloadFlagGun2 = threading.Event()
isReloadFlagGun2.clear()

doesGrenadeHitFlagVest1 = threading.Event()
doesGrenadeHitFlagVest1.clear()

doesGrenadeHitFlagVest2 = threading.Event()
doesGrenadeHitFlagVest2.clear()


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
        HANDSHAKE_FLAGS[self.deviceId] = True
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
        print("Checksum failed for device", self.deviceId, ", packet dropped")


    def handleNotification(self, cHandle, data):
        try:
            self.receivingBuffer += data
            if len(self.receivingBuffer) >=20:
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
                print("data smaller than 20 bytes received")
                print(self.receivingBuffer)


        except CheckSumFailedError:
            self.handleCheckSumError(data)

        except ValueError:
            pass



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

        if self.beetleId == VEST_PLAYER_1 or self.beetleId == VEST_PLAYER_2:
            self.isGrenadeHit = False

    def writetoBeetle(self):
        pass

    def openBeetleConnection(self):
        # while True:
        try:
            self.dev = Peripheral(self.macAddress)
            print("Connected to Beetle: ", self.beetleId)
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
        print('checking for reload')
        if self.beetleId == GUN_PLAYER_1:
            if isReloadFlagGun1.is_set():
                print('writing reload to beetle')
                self.serialChar.write(bytes("R", encoding="utf-8"))
                self.isReload = True
                isReloadFlagGun1.clear()

        if self.beetleId == GUN_PLAYER_2:
            if isReloadFlagGun2.is_set():
                self.serialChar.write(bytes("R", encoding="utf-8"))
                self.isReload = True
                isReloadFlagGun2.clear()

    def checkForGrenadeHit(self):
        print('checking for grenade')
        if self.beetleId == VEST_PLAYER_1:
            if doesGrenadeHitFlagVest1.is_set():
                self.serialChar.write(bytes("G", encoding="utf-8"))
                self.isGrenadeHit = True
                doesGrenadeHitFlagVest1.clear()

        if self.beetleId == VEST_PLAYER_2:
            if doesGrenadeHitFlagVest2.is_set():
                print('writing grenade on beetle')
                self.serialChar.write(bytes("G", encoding="utf-8"))
                self.isGrenadeHit = True
                doesGrenadeHitFlagVest2.clear()

    def checkBulletCount(self):
        data = None

        if not gameQueue.empty():
            data = gameQueue.get()

        if data:
            if self.beetleId == GUN_PLAYER_1:
                print('writing bullets to beetle', self.beetleId)
                bullets_p1 = data['p1']['bullets']
                self.serialChar.write(bytes(chr(bullets_p1), encoding="utf-8"))

            if self.beetleId == GUN_PLAYER_2:
                print('writing bullets to beetle', self.beetleId)
                bullets_p2 = data['p2']['bullets']
                print("bullets were updated", bullets_p2)
                self.serialChar.write(bytes(chr(bullets_p2), encoding="utf-8"))

        # bullets_p1 = data['p1']['bullets']
        # hp_p1 = data['p1']['hp']
        # bullets_p2 = data['p2']['bullets']
        # hp_p2 = data['p2']['hp']

    def checkHealthCount(self):
        data = None

        if not gameQueue.empty():
            data = gameQueue.get()

        if data:
            if self.beetleId == GUN_PLAYER_1:
                print('writing hp to beetle', self.beetleId)
                hp_p1 = data['p1']['hp']
                self.serialChar.write(bytes(hp_p1, encoding="utf-8"))

            if self.beetleId == GUN_PLAYER_2:
                print('writing hp to beetle', self.beetleId)
                hp_p2 = data['p2']['hp']
                self.serialChar.write(bytes(hp_p2, encoding="utf-8"))

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

                if SYN_FLAGS[self.beetleId] and ACK_FLAGS[self.beetleId]:
                    hasHandshake = True
                if HANDSHAKE_FLAGS[self.beetleId]:
                    hasHandshake = True

                if not self.dev.waitForNotifications(5):
                    self.hasHandshaken = False
                    isConnected = False
                    hasHandshake = False
                    SYN_FLAGS[self.beetleId] = False
                    ACK_FLAGS[self.beetleId] = False
                    self.dev.disconnect()
                if hasHandshake:
                    print('comes here and has handshaked')
                    if self.beetleId == GUN_PLAYER_1 or self.beetleId == GUN_PLAYER_2:
                        self.checkForReload()
                        self.checkBulletCount()

                    if self.beetleId == VEST_PLAYER_1 or self.beetleId == VEST_PLAYER_2:
                        self.checkForGrenadeHit()
                        self.checkHealthCount()

                    self.dev.waitForNotifications(1)

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
                print(str(e))


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


def testReloadThread():
    while True:
        time.sleep(20)
        isReloadFlagGun2.set()
        isReloadFlagGun1.set()
        print('setting reload flags')


def testGrenadeHitThread():
    while True:
        time.sleep(5)
        doesGrenadeHitFlagVest1.set()
        doesGrenadeHitFlagVest2.set()
        print('setting grenade flags')


def testBulletUpdateThread():
    while True:
        time.sleep(20)
        data = {'p2': {
            'bullets': 6}
        }

        gameQueue.put(data)
        # data['p1']['hp']


if __name__ == '__main__':
    try:
        lock = mp.Lock()

        # using a multiprocessing queue FIFO
        # dataBuffer = mp.Queue()
        receivingBuffer1 = b''
        receivingBuffer2 = b''
        receivingBuffer3 = b''
        receivingBuffer4 = b''
        receivingBuffer5 = b''
        receivingBuffer6 = b''
        # IMU2_Beetle = BeetleConnectionThread(2, IMU_PLAYER_2, macAddresses.get(4), dataBuffer, lock, receivingBuffer)
        # IMU2_Beetle.executeCommunications()



        Gun1_Beetle = BeetleConnectionThread(1, GUN_PLAYER_2, macAddresses.get(6), dataBuffer, lock, receivingBuffer3)
        Gun1_Thread = threading.Thread(target=Gun1_Beetle.executeCommunications, args=())

        UpdateBulletThread = threading.Thread(target=testBulletUpdateThread, args=())


        Gun1_Thread.start()


        UpdateBulletThread.start()

        Gun1_Thread.join()



        UpdateBulletThread.join()


    except (KeyboardInterrupt, SystemExit):
        print("Ended Comms")
        # sys.exit()
