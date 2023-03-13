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
import time
import tensorflow as tf
import numpy as np
from scipy.stats import skew
from scipy.fftpack import fft
from slidingwindow import SlidingWindow

model = tf.keras.models.load_model('my_model.h5')
# the peripheral class is used to connect and disconnect

# timeouts in seconds
CONNECTION_TIMEOUT = 3

Service_UUID = "0000dfb0-0000-1000-8000-00805f9b34fb"
Characteristic_UUID = "0000dfb1-0000-1000-8000-00805f9b34fb"

# serialSvc = dev.getServiceByUUID(
#     "0000dfb0-0000-1000-8000-00805f9b34fb")
# serialChar = serialSvc.getCharacteristics(
#     "0000dfb1-0000-1000-8000-00805f9b34fb")[0]


# 'GRENADE': 3
# 'LOGOUT' : 0
# 'SHIELD' : 1
# 'RELOAD' : 2
# 'IDLE' : 4

macAddresses = {
    1: "D0:39:72:BF:BF:BB",  # imu1
    2: "D0:39:72:BF:C6:07",  # VEST1
    3: "D0:39:72:BF:C3:BF",  # GUN1
    4: "D0:39:72:BF:C8:A8",  # IMU2
    5: "D0:39:72:BF:BF:DD",  # vest2
    6: "D0:39:72:BF:C8:CF"  # gun2
}

DATA_PACKET_SIZE = 20

SYN_FLAGS = [False] * 6
ACK_FLAGS = [False] * 6

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

arr1 = []
arr2 = []
arr3 = []
arr4 = []
arr5 = []
arr6 = []

arr11 = []
arr22 = []
arr33 = []
arr44 = []
arr55 = []
arr66 = []

keyPress = False
key_input = ""
counter = 1
ACTION = 'RELOAD'

NUM_OF_DATA_POINTS = 128
flag = threading.Event()
flag.clear()

WINDOW_SIZE = 40
move_detector = SlidingWindow(WINDOW_SIZE)


class CheckSumFailedError(Exception):
    pass


# each beetle has a delegate to handle BLE transactions
class MyDelegate(DefaultDelegate):
    def __init__(self, playerId, deviceId, dataBuffer, lock, receivingBuffer, hasHandshaken, serialSvc, serialChar,
                 isKeyPressed):
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
        self.isKeyPressed = isKeyPressed

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
        print("Checksum failed for device", self.deviceId, ", packet dropped")

    def extract_features(self, input):

        mean_acc_x = np.mean(input[0]).reshape(-1, 1)
        mean_acc_y = np.mean(input[1]).reshape(-1, 1)
        mean_acc_z = np.mean(input[2]).reshape(-1, 1)
        mean_gyro_x = np.mean(input[3]).reshape(-1, 1)
        mean_gyro_y = np.mean(input[4]).reshape(-1, 1)
        mean_gyro_z = np.mean(input[5]).reshape(-1, 1)

        sd_acc_x = np.std(input[0]).reshape(-1, 1)
        sd_acc_y = np.std(input[1]).reshape(-1, 1)
        sd_acc_z = np.std(input[2]).reshape(-1, 1)
        sd_gyro_x = np.std(input[3]).reshape(-1, 1)
        sd_gyro_y = np.std(input[4]).reshape(-1, 1)
        sd_gyro_z = np.std(input[5]).reshape(-1, 1)

        max_acc_x = np.amax(input[0]).reshape(-1, 1)
        max_acc_y = np.amax(input[1]).reshape(-1, 1)
        max_acc_z = np.amax(input[2]).reshape(-1, 1)
        max_gyro_x = np.amax(input[3]).reshape(-1, 1)
        max_gyro_y = np.amax(input[4]).reshape(-1, 1)
        max_gyro_z = np.amax(input[5]).reshape(-1, 1)

        min_acc_x = np.amin(input[0]).reshape(-1, 1)
        min_acc_y = np.amin(input[1]).reshape(-1, 1)
        min_acc_z = np.amin(input[2]).reshape(-1, 1)
        min_gyro_x = np.amin(input[3]).reshape(-1, 1)
        min_gyro_y = np.amin(input[4]).reshape(-1, 1)
        min_gyro_z = np.amin(input[5]).reshape(-1, 1)

        rms_acc_x = np.reshape(np.sqrt(np.mean(input[0] ** 2)), (-1, 1))
        rms_acc_y = np.reshape(np.sqrt(np.mean(input[1] ** 2)), (-1, 1))
        rms_acc_z = np.reshape(np.sqrt(np.mean(input[2] ** 2)), (-1, 1))
        rms_gyro_x = np.reshape(np.sqrt(np.mean(input[3] ** 2)), (-1, 1))
        rms_gyro_y = np.reshape(np.sqrt(np.mean(input[4] ** 2)), (-1, 1))
        rms_gyro_z = np.reshape(np.sqrt(np.mean(input[5] ** 2)), (-1, 1))

        skew_acc_x = np.reshape(skew(input[0]), (-1, 1))
        skew_acc_y = np.reshape(skew(input[1]), (-1, 1))
        skew_acc_z = np.reshape(skew(input[2]), (-1, 1))
        skew_gyro_x = np.reshape(skew(input[3]), (-1, 1))
        skew_gyro_y = np.reshape(skew(input[4]), (-1, 1))
        skew_gyro_z = np.reshape(skew(input[5]), (-1, 1))

        # # Convert to frequency domain
        # signal_acc_x = fft(input[0], axis=1)
        # signal_acc_y = fft(input[1], axis=1)
        # signal_acc_z = fft(input[2], axis=1)
        # signal_gyro_x = fft(input[3], axis=1)
        # signal_gyro_y = fft(input[4], axis=1)
        # signal_gyro_z = fft(input[5], axis=1)

        mag_acc_x = np.reshape(np.amax(np.abs(fft(input[0]))), (-1, 1))
        mag_acc_y = np.reshape(np.amax(np.abs(fft(input[1]))), (-1, 1))
        mag_acc_z = np.reshape(np.amax(np.abs(fft(input[2]))), (-1, 1))
        mag_gyro_x = np.reshape(np.amax(np.abs(fft(input[3]))), (-1, 1))
        mag_gyro_y = np.reshape(np.amax(np.abs(fft(input[4]))), (-1, 1))
        mag_gyro_z = np.reshape(np.amax(np.abs(fft(input[5]))), (-1, 1))

        phase_acc_x = np.reshape(np.amax(np.angle(fft(input[0]))), (-1, 1))
        phase_acc_y = np.reshape(np.amax(np.angle(fft(input[1]))), (-1, 1))
        phase_acc_z = np.reshape(np.amax(np.angle(fft(input[2]))), (-1, 1))
        phase_gyro_x = np.reshape(np.amax(np.angle(fft(input[3]))), (-1, 1))
        phase_gyro_y = np.reshape(np.amax(np.angle(fft(input[4]))), (-1, 1))
        phase_gyro_z = np.reshape(np.amax(np.angle(fft(input[5]))), (-1, 1))

        return np.concatenate((mean_acc_x, mean_acc_y, mean_acc_z, mean_gyro_x, mean_gyro_y, mean_gyro_z, sd_acc_x,
                               sd_acc_y, sd_acc_z, sd_gyro_x, sd_gyro_y, sd_gyro_z,
                               max_acc_x, max_acc_y, max_acc_z, max_gyro_x, max_gyro_y, max_gyro_z,
                               min_acc_x, min_acc_y, min_acc_z, min_gyro_x, min_gyro_y, min_gyro_z,
                               rms_acc_x, rms_acc_y, rms_acc_z, rms_gyro_x, rms_gyro_y, rms_gyro_z,
                               skew_acc_x, skew_acc_y, skew_acc_z, skew_gyro_x, skew_gyro_y, skew_gyro_z,
                               mag_acc_x, mag_acc_y, mag_acc_z, mag_gyro_x, mag_gyro_y, mag_gyro_z,
                               phase_acc_x, phase_acc_y, phase_acc_z, phase_gyro_x, phase_gyro_y, phase_gyro_z),
                              axis=1).astype(np.int32)
        

    def predictdata(self, data):
        global counter, model, move_detector, is_move_detection_skipped

        motiondata = data['motionData']
        imu_data = np.array(motiondata.values())

        move_detector.add_new_value(imu_data)

        if not move_detector.is_full():
            return "none"

        move_detector.update_threshold()

        if not move_detector.is_start_of_move():
            return "none"
        
        # if not is_move_detection_skipped:
        #     start_index = move_detector.is_start_of_move()
        #     if start_index >= 0:
        #         for i in range(start_index):
        #             move_detector.remove_old_value()
        #             is_move_detection_skipped = True
        
        # is_move_detection_skipped = False

        features = self.extract_features(move_detector.get_window_matrix())

        mapping = {0: 'LOGOUT', 1: 'SHIELD', 2: 'RELOAD', 3: 'GRENADE', 4: 'IDLE'}
        predictions = model.predict(features)
        predicted_class = np.argmax(predictions[0])
        print('Predicted class:', predicted_class, mapping[predicted_class])
        

        # if counter <= 50:
        #     motiondata = data['motionData']
        #     row = list(motiondata.values())
        #     arr1.append(row[0])
        #     arr2.append(row[1])
        #     arr3.append(row[2])
        #     arr4.append(row[3])
        #     arr5.append(row[4])
        #     arr6.append(row[5])
        #     # print("DATA RECV", row)
        #     counter += 1

        # elif counter > 50:
        #     # put line
        #     # newline
        #     # empty arr
        #     # only save when arrays are non-empty
        #     print("raw data collected!")
        #     raw_data = np.array([arr1, arr2, arr3, arr4, arr5, arr6]).astype(np.float32)
        #     # print(raw_data)
        #     features = self.extract_features(raw_data)
        #     print(f"Data collected and saved for {ACTION}, iteration {counter}")

        #     # # Make a prediction on the new data
        #     # predictions = model.predict(features)

        #     # # Print the predicted class
        #     # predicted_class = np.argmax(predictions[0])
        #     # print('Predicted class:', predicted_class, mapping[predicted_class])

        #     arr1.clear()
        #     arr2.clear()
        #     arr3.clear()
        #     arr4.clear()
        #     arr5.clear()
        #     arr6.clear()
        #     counter = 1

    def handleNotification(self, cHandle, data):
        try:

            self.receivingBuffer += data
            if len(self.receivingBuffer) >= 20:
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
                packetType = chr(unpackedPacket[0])
                # print("packetType, deviceId, length ", packetType , "," , self.deviceId,
                #       ",", len(self.receivingBuffer) )
                # # , ",", self.transmissionSpeed, "kbps"
                # print("Fragmented Packets Count for device:", self.deviceId, ":", self.fragPacketsCount)
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
                    # print("MotionPacketsCount: ", self.motionPacketsCount)
                    # print(sendData)
                    self.predictdata(sendData)
                    # self.lock.acquire()
                    # self.dataBuffer.put(sendData)
                    # self.lock.release()
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
        self.isKeyPressed = False

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
                                        self.receivingBuffer, self.hasHandshaken, self.serialSvc, self.serialChar,
                                        self.isKeyPressed)
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
                # if keyboard.is_pressed("a"):
                #     self.isKeyPressed = True
                #     global keyPress
                #     keyPress = True
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
        dataBuffer = mp.Queue()
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
        IMU1_Thread = threading.Thread(target=IMU1_Beetle.executeCommunications, args=())
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
        IMU1_Thread.join()
        # while True: time.sleep(100)

        # signal.pause()

    except (KeyboardInterrupt, SystemExit):
        print("Ended Comms")
        # sys.exit()