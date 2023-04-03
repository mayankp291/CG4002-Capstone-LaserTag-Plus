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

#define factor 1000
#define SYN_PACKET 'S'
#define ACK_PACKET 'A'
#define DATA_PACKET 'D'

// global variables for accelerometer and gyroscope data
int16_t accX, accY, accZ;
int16_t gyrX, gyrY, gyrZ;
double a_x_err = -1.57;
double a_y_err = 0;
double a_z_err = 0.1;
double g_x_err = 0.01;
double g_y_err = 0.04;
double g_z_err = 0.05;

//when run this func to get the error of imu, please place the sensor static
// void calculate_error() {
//   int i = 0;
//   sensors_event_t a, g, temp;
//   mpu.getEvent(&a, &g, &temp);
//   while(i < 200) {
//     sensors_event_t a, g, temp;
//     mpu.getEvent(&a, &g, &temp);
//     a_x_err += a.acceleration.x - 0;
//     a_y_err += a.acceleration.y - 0;
//     a_z_err = a_z_err + (a.acceleration.z - 9.8);
//     g_x_err += g.gyro.x - 0;
//     g_y_err += g.gyro.y - 0;
//     g_z_err += g.gyro.z - 0;
//     i++;
//   }
//   a_x_err /= 200;
//   a_y_err /= 200;
//   a_z_err /= 200;
//   g_x_err /= 200;
//   g_y_err /= 200;
//   g_z_err /= 200;

//   Serial.print("a_x_err: ");
//   Serial.println(a_x_err);

//   Serial.print("a_y_err: ");
//   Serial.println(a_y_err);

//   Serial.print("a_z_err: ");
//   Serial.println(a_z_err);

//   Serial.print("g_x_err: ");
//   Serial.println(g_x_err);

//   Serial.print("g_y_err: ");
//   Serial.println(g_y_err);

//   Serial.print("g_z_err: ");
//   Serial.println(g_z_err);
// }
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
  byte typeOfPacket; // motion
  byte deviceID;
  int16_t accX;
  int16_t accY;
  int16_t accZ;
  int16_t gyrX;
  int16_t gyrY;
  int16_t gyrZ;
  byte padding[5];
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
  ackPacket.padding[18] = {0};
  ackPacket.checkSum = findCheckSum((uint8_t *)&ackPacket);
  Serial.write((byte *)&ackPacket, sizeof(ackPacket));
  //    Serial.write(ACK_PACKET);
  //    crc.add(ACK_PACKET);
  //    Serial.write(crc.getCRC());

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
  //   randomNumber = random(500);
  //    while(!Serial) {
  //     delay(10);
  // //     Serial.println("Adafruit MPU6050 start test:");
  //   }

  //initialize
     if (!mpu.begin()) {
   //     Serial.println("Failed to find MPU6050 chip");
       while (1) {
         delay(10);
       }
     }
  //   Serial.println("MPU6050 Found!");

  mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
  //   Serial.print("Accelerometer range set to: ");

  //   switch (mpu.getAccelerometerRange()) {
  //   case MPU6050_RANGE_2_G:
  //     Serial.println("+-2G");
  //     break;
  //   case MPU6050_RANGE_4_G:
  //     Serial.println("+-4G");
  //     break;
  //   case MPU6050_RANGE_8_G:
  //     Serial.println("+-8G");
  //     break;
  //   case MPU6050_RANGE_16_G:
  //     Serial.println("+-16G");
  //     break;
  //   }

     mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  //   Serial.print("Gyro range set to: ");
  //   switch (mpu.getGyroRange()) {
  //   case MPU6050_RANGE_250_DEG:
  //     Serial.println("+- 250 deg/s");
  //     break;
  //   case MPU6050_RANGE_500_DEG:
  //     Serial.println("+- 500 deg/s");
  //     break;
  //   case MPU6050_RANGE_1000_DEG:
  //     Serial.println("+- 1000 deg/s");
  //     break;
  //   case MPU6050_RANGE_2000_DEG:
  //     Serial.println("+- 2000 deg/s");
  //     break;
  //   }
  //
     mpu.setFilterBandwidth(MPU6050_BAND_5_HZ);
  //   Serial.print("Filter bandwidth set to: ");
  //   switch (mpu.getFilterBandwidth()) {
  //   case MPU6050_BAND_260_HZ:
  //     Serial.println("260 Hz");
  //     break;
  //   case MPU6050_BAND_184_HZ:
  //     Serial.println("184 Hz");
  //     break;
  //   case MPU6050_BAND_94_HZ:
  //     Serial.println("94 Hz");
  //     break;
  //   case MPU6050_BAND_44_HZ:
  //     Serial.println("44 Hz");
  //     break;
  //   case MPU6050_BAND_21_HZ:
  //     Serial.println("21 Hz");
  //     break;
  //   case MPU6050_BAND_10_HZ:\
  //     Serial.println("10 Hz");
  //     break;
  //   case MPU6050_BAND_5_HZ:
  //     Serial.println("5 Hz");
  //     break;
  //   }
  //
  //   Serial.println("");
  //   delay(100);
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
  // get newsensor readings
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  /* Print out the values  m/s^2   */
  accX = (a.acceleration.x - a_x_err) * factor;
  accY = (a.acceleration.y - a_y_err) * factor;
  accZ = (a.acceleration.z - a_z_err) * factor;
  gyrX = (g.gyro.x - g_x_err) * factor;
  gyrY = (g.gyro.y - g_y_err) * factor;
  gyrZ = (g.gyro.z - g_z_err) * factor;
//    Serial.print("Acceleration X: ");
//    Serial.print(accX);
//    Serial.print(", Y: ");
//    Serial.print(accY);
//    Serial.print(", Z: ");
//    Serial.print(accZ);
//    Serial.println(" m/s^2");
//    /* rad*/
//    Serial.print("Rotation X: ");
//    Serial.print(gyrX);
//    Serial.print(", Y: ");
//    Serial.print(gyrY);
//    Serial.print(", Z: ");
//    Serial.print(gyrZ);
//    Serial.println(" rad/s");
//  Serial.print(accX);
//  Serial.print(",");
//  Serial.print(accY);
//  Serial.print(",");
//  Serial.print(accZ);
//  Serial.print(", ");
//  Serial.print(gyrX);
//  Serial.print(",");
//  Serial.print(gyrY);
//  Serial.print(",");
//  Serial.print(gyrZ);
//  Serial.println("");

  //  Serial.print("Temperature: ");
  //  Serial.print(temp.temperature);
  //  Serial.println(" degC");
  //
//    Serial.println("");
  delay(50);
//delay(300);/
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
  motionPacket.checkSum = findCheckSum((uint8_t *)&motionPacket);

  Serial.write((byte *)&motionPacket, sizeof(motionPacket));
}

boolean hasSent = false;

int count = 0;

void loop(void) {
  if (Serial.available()>0) {

    if (hasHandshake == false) {
      char serialRead = Serial.read();
      // Serial.println(serialRead);
      if (serialRead == 'S') {
        //              Serial.write('A');
        sendACKPacket();
      }
      else if (serialRead == 'A') {
        hasHandshake = true;

      }
    }

    if (hasHandshake == true) {
      //          count<=5 &&
      //           delay(2000);
      getSensorReading();
      sendSensorReading();
      hasSent = true;
      count++;
    }
//    if (serialRead == 'K') {
//        hasHandshake = false;
//    }
  }
 if(Serial.available() <=0) {
   hasHandshake = false;
 }
//  if(Serial.available() == 0) {
//    hasHandshake = false;
//  }

//getSensorReading();
//sendSensorReading();

}