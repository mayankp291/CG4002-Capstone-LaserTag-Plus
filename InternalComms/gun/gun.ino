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

#DEFINE TIMEOUT_VAL 50

unsigned long previousMillis = 0;
unsigned long currentMillis;

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
    byte typeOfPacket; // gun
    byte deviceID;
    bool isGunShot;
    byte padding[16];
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



void sendSensorReading() {
    DatagramPacket gunPacket;
    gunPacket.typeOfPacket = (byte) 'B';
    gunPacket.deviceID = 5;
    gunPacket.isGunShot = true;

    gunPacket.padding[16] = {0};
    gunPacket.crcCheck = 1;

    Serial.write((byte *)&gunPacket, sizeof(gunPacket));
}

boolean hasSent = false;
boolean hasAcknowledged = false;

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
           delay(10000);
           sendSensorReading();
           hasSent = true;
           count++;
           hasAcknowledged = false;
       }

       if(hasHandshake == true && hasSent == true && hasAcknowledged == false) {
            if(millis() - currentMillis >= TIMEOUT_VAL)
            {
                hasSent = false;
            }
            char serialRead = Serial.read();
            if(serialRead == 'A') {
                hasAcknowledged = true;
            }
       }
   }

}