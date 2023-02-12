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
    byte typeOfPacket = "A";
    byte padding[18];
    byte checkSum = 'A';
} ackPacket;

struct DatagramPacket {
    byte typeOfPacket = 'M'; // motion
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

void sendACKPacket(char packetType) {
    Serial.write(ACK_PACKET);
    crc.add(ACK_PACKET);
    Serial.write(crc.getCRC());

    crc.restart();
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
}

void doHandshake() {
  byte packetType = Serial.read();
  if (packetType == SYN_PACKET)
  {
        sendACKPacket(ACK_PACKET);
        // break;
  }
  else if (packetType == ACK_PACKET)
  {
        hasHandshake = true;
  }
}

void loop(void) {
   if(Serial.available()) {
    char serialRead = Serial.read();
    Serial.println(serialRead);
   }
}