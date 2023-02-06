import multiprocessing as mp
import os
from socket import *
import threading
from crccheck.crc import crc8

from bluepy.btle import DefaultDelegate, Peripheral, Scanner, BTLEDisconnectError

# the peripheral class is used to connect and disconnect


macAddresses = {
    1: "D0:39:72:BF:BF:BB", #imu
    2: "D0:39:72:BF:C6:07",
    3: "",
    4: "",
    5: "",
    6: ""
}

# each beetle has a delegate to handle BLE transactions
class MyDelegate(DefaultDelegate):
    def __init__(self, id):
        DefaultDelegate.__init__(self)
        self.id = id
        self.hasHandshaken = False

    def sendAckPacket(self):
        self.serialChar.write(bytes("A", "utf-8"))

    def handleAckPacket(self):
        self.sendAckPacket()
        self.hasHandshaken = True

    def handleNotification(self,cHandle, data):
        self.buffer +=data

    def checkCRC(self, length):
        calcChecksum = Crc8.calc(self.buffer[0: length])


p = Peripheral(macAddresses.get(1))

