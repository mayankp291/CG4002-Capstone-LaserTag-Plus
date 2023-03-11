#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include "CRC.h"
#include "CRC8.h"
#include <IRremote.h> // >v3.0.0
#include <Adafruit_NeoPixel.h>      

#define PIN_RECV 2
#define LED_COUNT 7
const int ledPin = 4;


int healthPoint = 100;
const int buzzer = 5;
Adafruit_NeoPixel leds = Adafruit_NeoPixel(LED_COUNT, ledPin, NEO_GRB + NEO_KHZ800);
bool dummy_is_shot = false;

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

#define TIMEOUT_VAL 50

unsigned long previousMillis = 0;
unsigned long currentMillis;

// Calculate CRC to identify errors in transmission
uint8_t calculateCRC8(uint8_t *data, int len) {
    return crc8(data, len);
}

struct AcknowledgementPacket {
    byte typeOfPacket;
    byte padding[18];
    byte checkSum;
} ackPacket;

struct DatagramPacket {
    byte typeOfPacket; // gun
    byte deviceID;
    bool isShotReceived;
    byte padding[16];
    byte checkSum;
} ;

uint8_t findCheckSum(uint8_t *inputPacket) {
    uint8_t checkSum = 0;
    for (int i = 0; i < 19; i++) {
        checkSum ^= inputPacket[i];
    }
    return checkSum;
}

void sendACKPacket() {
    AcknowledgementPacket ackPacket;
    ackPacket.typeOfPacket = (byte) 'A';

//    Serial.write(ACK_PACKET);
//    crc.add(ACK_PACKET);
//    Serial.write(crc.getCRC());
    ackPacket.padding[18] = {0};
    ackPacket.checkSum = findCheckSum((uint8_t *)&ackPacket);
    Serial.write((byte *)&ackPacket, sizeof(ackPacket));
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
  IrReceiver.begin(PIN_RECV); // Initializes the IR receiver object
  pinMode(ledPin, OUTPUT);      // declare LED as output
  pinMode(buzzer, OUTPUT);
  // generating random numbers
//   randomNumber = random(500);
}

void clearLEDs() {
  for(int i = 0; i < LED_COUNT; i++) {
    leds.setPixelColor(i, 0);
  }
}

void led() {
    int color = 0x800080;
    if(healthPoint == 100) {
      for(int i = 0; i < LED_COUNT; i++) leds.setPixelColor(i, 0x00FF00);
    } else if(healthPoint == 90) {
      for(int i = 0; i < LED_COUNT; i++) leds.setPixelColor(i, 0x0000FF);
      color = 0x0000FF;
    } else if(healthPoint == 80) {
      for(int i = 0; i < LED_COUNT; i++) leds.setPixelColor(i, 0xFFC0CB);
      color = 0xFFC0CB;
    } else if(healthPoint == 70) {
      for(int i = 0; i < LED_COUNT; i++) leds.setPixelColor(i, 0xFFFF00);
      color = 0xFFFF00;
    } else if(healthPoint == 60) {
      for(int i = 0; i < LED_COUNT; i++) leds.setPixelColor(i, 0x800080);
      color = 0x800080;
    } else if(healthPoint == 40) {
      for(int i = 0; i < LED_COUNT; i++) leds.setPixelColor(i, 0xADD8E6);
      color = 0xADD8E6;
    } else if(healthPoint == 30) {
      for(int i = 0; i < LED_COUNT; i++) leds.setPixelColor(i, 0xFF4500);
      color = 0xFF4500;
    } else if(healthPoint == 20) {
      for(int i = 0; i < LED_COUNT; i++) leds.setPixelColor(i, 0xFFD700);
      color = 0xFFD700;
    } else if(healthPoint == 10) {
      for(int i = 0; i < LED_COUNT; i++) leds.setPixelColor(i, 0xDC143C);
      color = 0xDC143C;
    } else {
      for(int i = 0; i < LED_COUNT; i++) leds.setPixelColor(i, 0xFF0000);
      color = 0xFF0000;
    } 
    leds.show();
    // delay(500);
    // for(int i = 0; i < LED_COUNT; i++) {
    //   leds.setPixelColor(i, 0xFF0000);
    // }
    // leds.show();
    // delay(500);
    // for(int i = 0; i < LED_COUNT; i++) {
    //   leds.setPixelColor(i, 50);
    // }
    // leds.show();
    delay(2000);
    clearLEDs();
    leds.show();
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
    DatagramPacket vestPacket;
    vestPacket.typeOfPacket = (byte) 'H';
    vestPacket.deviceID = 5;
    vestPacket.isShotReceived = dummy_is_shot;

    vestPacket.padding[16] = {0};
    vestPacket.checkSum = findCheckSum((uint8_t *)&vestPacket);

    Serial.write((byte *)&vestPacket, sizeof(vestPacket));
}

boolean hasSent = false;
boolean hasAcknowledged = false;

int count = 0;

void loop(void) {
  if(healthPoint <= 0) {
      healthPoint = 100;
  }
  if (IrReceiver.decode()) {
//     Serial.println("Received something...");
    if(IrReceiver.decodedIRData.address == 0x0102) {
//         Serial.println("Shotted!");
        healthPoint = healthPoint - 10;
        led();
        // tone(buzzer, 1000); // Send 1KHz sound signal...
        // delay(500);        // ...for 1 sec
        // noTone(buzzer);     // Stop sound...
        // delay(500);        // ...for 1sec   
        dummy_is_shot = true;
    } else {
      dummy_is_shot = false;
    }
    IrReceiver.printIRResultShort(&Serial); // Prints a summary of the received data
//     Serial.println();
    IrReceiver.begin(PIN_RECV); // Important, enables to receive the next IR signal
  }

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

       if(hasHandshake == true && dummy is show == true) {
//          count<=5 &&
//            delay(10000);
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
