import multiprocessing as mp
import os
from socket import *
import threading
from crccheck.crc import Crc8

from bluepy.btle import DefaultDelegate, Peripheral, Scanner, BTLEDisconnectError

handshake = False
synSent = False
beetleAck = False

class MyDelegate(DefaultDelegate):
    def __init__(self, playerId, deviceId, dataBuffer, lock, receivingBuffer):
        DefaultDelegate.__init__(self)
        self.playerId = playerId
        self.deviceId = deviceId
        self.lock = lock
        self.hasHandshaken = False
        self.dataBuffer = dataBuffer
        self.receivingBuffer = receivingBuffer

    def sendAckPacket(self):
        self.serialChar.write(bytes("A", "utf-8"))

    def handleAckPacket(self):
        self.sendAckPacket()
        self.hasHandshaken = True

    def handleNotification(self, cHandle, data):
        self.receivingBuffer += data
        print("Data received from beetle: ", self.receivingBuffer)
        if (len(self.receivingBuffer)) == 1 and self.receivingBuffer == b'A':
            global beetleAck
            beetleAck = True
            self.receivingBuffer = b'' # reset the data
        self.receivingBuffer = b''


    def checkCRC(self, length):
        calcChecksum = Crc8.calc(self.buffer[0: length])
        return calcChecksum == self.buffer[length]


# dev = Peripheral("D0:39:72:BF:C6:07")
# dev = Peripheral("D0:39:72:BF:BF:BB")
lock = mp.Lock()

dataBuffer = None
receivingBuffer = b''
dev = Peripheral("D0:39:72:BF:C8:CF")
devDelegate = MyDelegate(1, 5, dataBuffer, lock, receivingBuffer)
dev.setDelegate(devDelegate)
# try:
#     ch = dev.getCharacteristics()
#     # print(ch.read())
#     for c in ch:
#         print("c ", c)
#         print("  0x" + format(ch.getHandle(), '02X') + "   " + str(ch.uuid) + " " + ch.propertiesToString())
# finally:
#     dev.disconnect()

Characteristic_UUID = "0000dfb1-0000-1000-8000-00805f9b34fb"
serialSvc = dev.getServiceByUUID(
    "0000dfb0-0000-1000-8000-00805f9b34fb")
serialChar = serialSvc.getCharacteristics(
    "0000dfb1-0000-1000-8000-00805f9b34fb")[0]


while not handshake:
    dev.waitForNotifications(1.0)
    characteristics = dev.getCharacteristics()

    print("sending syn to beetle")
    if not synSent:
        serialChar.write(bytes('S', encoding="utf-8"))
        synSent = True
    if beetleAck:
        serialChar.write(bytes('A', encoding="utf-8"))
        handshake = True
        print("handshake completed")


