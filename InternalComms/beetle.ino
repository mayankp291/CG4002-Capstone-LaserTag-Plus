#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include "CRC.h"
#include "CRC8.h"

Adafruit_MPU6050 mpu;

byte dataPacket[20];
bool hasHandshake = false;
byte sequenceNo;
byte packetCount;

int randomNumber;

CRC8 crc;

#define SYN_PACKET 'S'
#define ACK_PACKET 'A'
#define DATA_PACKET 'D'

// global variables for accelerometer and gyroscope data
int16_t accX, accY, accZ;
int16_t gyrX, gyrY, gyrZ;

// Calculate CRC to identify errors in transmission
uint8_t calculateCRC8(uint8_t *data, int len) {
    return crc8(data, len);
}

struct AcknowledgementPacket {
    byte typeOfPacket;
    byte padding[18];
    byte crcCheck;
} ackPacket;

struct DatagramPacket {
    byte typeOfPacket; // motion
    byte deviceID;
    int16_t accX;
    int16_t accY;
    int16_t accZ;
    int16_t gyrX;
    int16_t gyrY;
    int16_t gyrZ;
    byte padding[5];
    byte crcCheck;
} ;


void sendACKPacket() {
    AcknowledgementPacket ackPacket;
    ackPacket.typeOfPacket = (byte) 'A';
    Serial.write((byte *)&ackPacket, sizeof(ackPacket));
//    Serial.write(ACK_PACKET);
//    crc.add(ACK_PACKET);
//    Serial.write(crc.getCRC());
    ackPacket.padding[18] = {0};
    ackPacket.crcCheck = 1;
//    crc.restart();
}

void sendDataPacket() {
    DatagramPacket gloveDataPacket;
    // fill in the values of the data packetType
    // gloveDataPacket.crcCheck = calculateCRC8()
    Serial.write(DATA_PACKET);
}

void setup(void) {
  Serial.begin(115200);
  hasHandshake = false;
  sequenceNo = 0;
  packetCount = 0;

  // generating random numbers
  randomNumber = random(500);
}

void doHandshake() {
  byte packetType = Serial.read();
  if (packetType == SYN_PACKET)
  {
        sendACKPacket();
        // break;
  }
  else if (packetType == ACK_PACKET)
  {
        hasHandshake = true;
  }
}

void getSensorReading() {
    accX = random(500);
    accY = random(500);
    accZ = random(500);
    gyrX = random(500);
    gyrY = random(500);
    gyrZ = random(500);
}

void sendSensorReading() {
    DatagramPacket motionPacket;
    motionPacket.typeOfPacket = (byte) 'M';
    motionPacket.deviceID = 5;
    motionPacket.accX = accX;
    motionPacket.accY = accY;
    motionPacket.accZ = accZ;
    motionPacket.gyrX = gyrX;
    motionPacket.gyrY = gyrY;
    motionPacket.gyrZ = gyrZ;
//    motionPacket.deviceID = 5;
//    motionPacket.accX = 11;
//    motionPacket.accY = 11;
//    motionPacket.accZ = 11;
//    motionPacket.gyrX = 11;
//    motionPacket.gyrY = 11;
//    motionPacket.gyrZ = 11;

    motionPacket.padding[5] = {0};
    motionPacket.crcCheck = 1;

    Serial.write((byte *)&motionPacket, sizeof(motionPacket));
}

boolean hasSent = false;

int count = 0;

void loop(void) {
   if(Serial.available()) {
       if(hasHandshake == false) {
            char serialRead = Serial.read();
            // Serial.println(serialRead);
            if (serialRead == 'S') {
//              Serial.write('A');
                sendACKPacket();
            }
            else if(serialRead == 'A') {
              hasHandshake = true;

            }
       }

       if(hasHandshake == true) {
//          count<=5 &&
           delay(2000);
           getSensorReading();
           sendSensorReading();
           hasSent = true;
           count++;
       }
   }

}