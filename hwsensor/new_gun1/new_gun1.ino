#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include "CRC.h"
#include "CRC8.h"
#include <IRremote.h> // >v3.0.0

#define PIN_SEND 3
int ledPin = 4;
const int buzzer = 2;
int inputPin = A1;

int buttonState = LOW; //this variable tracks the state of the button, low if not pressed, high if pressed
long lastDebounceTime = 0;  // the last time the output pin was toggled
long debounceDelay = 50;    // the debounce time; increase if the output flickers

int bullets = 6;
bool dummy_shot = false;

bool isReloading = false;

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
    bool isGunShot;
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
  IrSender.begin(PIN_SEND); // Initializes IR sender
  pinMode(ledPin, OUTPUT);      // declare LED as output
  pinMode(buzzer, OUTPUT);
  pinMode(inputPin, INPUT);     // declare pushbutton as input
  // generating random numbers
//   randomNumber = random(500);
}

void playTone(int bullets) {
    tone(buzzer, bullets * 200); // Send 1KHz sound signal...
    delay(500);        // ...for 1 sec
    noTone(buzzer);     // Stop sound...
    delay(500);        // ...for 1sec     
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
    gunPacket.checkSum = findCheckSum((uint8_t *)&gunPacket);

    Serial.write((byte *)&gunPacket, sizeof(gunPacket));
}

void playReloadTone() {
    tone(buzzer, 7 * 200); // Send 1KHz sound signal...
    delay(1500);        // ...for 1 sec
    noTone(buzzer);     // Stop sound...
    //delay(500);        // ...for 1sec
}

boolean hasSent = false;
boolean hasAcknowledged = false;
int shotsCount = 0;

int count = 0;

void loop(void) {
  // if(bullets <= 0) {
  //     bullets = 6;
  //     playReloadTone();
  // }

  if(isReloading) {
    bullets = 6;
    playReloadTone();
    isReloading = false;
  }
  buttonState = digitalRead(inputPin);
  if( (millis() - lastDebounceTime) > debounceDelay) {
    if (buttonState == HIGH) {            // check if the input is HIGH
      lastDebounceTime = millis(); //set the current time

      
//       Serial.println("Triggered!!!");
      if (bullets > 0 ) {
          IrSender.sendNEC(0x0102, 0x34, 0); // the address 0x0102 with the command 0x34 is sent 
          dummy_shot = true;
          shotsCount +=1;
          playTone(bullets);
          bullets = bullets - 1;
      }
//       Serial.println(bullets);
      digitalWrite(ledPin, HIGH);  // turn LED OFF

      delay(500); // wait for one second

    } else {
      lastDebounceTime = millis(); //set the current time
      dummy_shot = false;
      digitalWrite(ledPin, LOW); // turn LED ON, actually no use because there is no led for gun
    }
  }

   if(Serial.available()) {
        char serialRead = Serial.read();
        // Serial.println(serialRead);
        if (serialRead == 'S') {
//              Serial.write('A');
            hasHandshake = false;
            sendACKPacket();
        }
        else if(serialRead == 'A') {
          hasHandshake = true;

        }
        if(serialRead == 'R') {
           isReloading = true;
        }


//        if(hasHandshake == false) {
//
//        }
//
//        if(hasHandshake == true) {
//             char serialRead = Serial.read();
//
//
//        }
       if(dummy_shot == true) {
        hasSent = false;
       }

//       if(hasHandshake == true && dummy_shot == true)
       if(hasHandshake == true && hasSent == false && shotsCount > 0)
       {
//          count<=5 &&
//            delay(10000);
           for (int i = 0; i < shotsCount; i++) {
              sendSensorReading();
           }
           shotsCount = 0;
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
