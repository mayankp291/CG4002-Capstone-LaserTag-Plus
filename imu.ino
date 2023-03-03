#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

Adafruit_MPU6050 mpu;

double a_x_err = -1.57;
double a_y_err = 0;
double a_z_err = 0.1;
double g_x_err = 0.01;
double g_y_err = 0.04;
double g_z_err = 0.05;

//when run this func to get the error of imu, please place the sensor static
void calculate_error() {
  int i = 0;
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  while(i < 200) {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    a_x_err += a.acceleration.x - 0;
    a_y_err += a.acceleration.y - 0;
    a_z_err = a_z_err + (a.acceleration.z - 9.8);
    g_x_err += g.gyro.x - 0;
    g_y_err += g.gyro.y - 0;
    g_z_err += g.gyro.z - 0;
    i++;
  }
  a_x_err /= 200;
  a_y_err /= 200;
  a_z_err /= 200;
  g_x_err /= 200;
  g_y_err /= 200;
  g_z_err /= 200;
  
  Serial.print("a_x_err: ");
  Serial.println(a_x_err);

  Serial.print("a_y_err: ");
  Serial.println(a_y_err);

  Serial.print("a_z_err: ");
  Serial.println(a_z_err);

  Serial.print("g_x_err: ");
  Serial.println(g_x_err);

  Serial.print("g_y_err: ");
  Serial.println(g_y_err);

  Serial.print("g_z_err: ");
  Serial.println(g_z_err);
}

void setup(void) {
  Serial.begin(115200);
  while(!Serial) {
    delay(10);
    Serial.println("Adafruit MPU6050 start test:");
  }

  //initialize
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  Serial.println("MPU6050 Found!");

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  Serial.print("Accelerometer range set to: ");

  switch (mpu.getAccelerometerRange()) {
  case MPU6050_RANGE_2_G:
    Serial.println("+-2G");
    break;
  case MPU6050_RANGE_4_G:
    Serial.println("+-4G");
    break;
  case MPU6050_RANGE_8_G:
    Serial.println("+-8G");
    break;
  case MPU6050_RANGE_16_G:
    Serial.println("+-16G");
    break;
  }

  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  Serial.print("Gyro range set to: ");
  switch (mpu.getGyroRange()) {
  case MPU6050_RANGE_250_DEG:
    Serial.println("+- 250 deg/s");
    break;
  case MPU6050_RANGE_500_DEG:
    Serial.println("+- 500 deg/s");
    break;
  case MPU6050_RANGE_1000_DEG:
    Serial.println("+- 1000 deg/s");
    break;
  case MPU6050_RANGE_2000_DEG:
    Serial.println("+- 2000 deg/s");
    break;
  }

  mpu.setFilterBandwidth(MPU6050_BAND_5_HZ);
  Serial.print("Filter bandwidth set to: ");
  switch (mpu.getFilterBandwidth()) {
  case MPU6050_BAND_260_HZ:
    Serial.println("260 Hz");
    break;
  case MPU6050_BAND_184_HZ:
    Serial.println("184 Hz");
    break;
  case MPU6050_BAND_94_HZ:
    Serial.println("94 Hz");
    break;
  case MPU6050_BAND_44_HZ:
    Serial.println("44 Hz");
    break;
  case MPU6050_BAND_21_HZ:
    Serial.println("21 Hz");
    break;
  case MPU6050_BAND_10_HZ:
    Serial.println("10 Hz");
    break;
  case MPU6050_BAND_5_HZ:
    Serial.println("5 Hz");
    break;
  }

//comment this when u don't neet 
  // calculate_error();

  Serial.println("");
  delay(100);
}

void loop() {
  // get newsensor readings
sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  /* Print out the values  m/s^2   */
  Serial.print("Acceleration X: ");
  Serial.print(a.acceleration.x - a_x_err);
  Serial.print(", Y: ");
  Serial.print(a.acceleration.y - a_y_err);
  Serial.print(", Z: ");
  Serial.print(a.acceleration.z - a_z_err);
  Serial.println(" m/s^2");
  /* rad*/
  Serial.print("Rotation X: ");
  Serial.print(g.gyro.x - g_x_err);
  Serial.print(", Y: ");
  Serial.print(g.gyro.y - g_y_err);
  Serial.print(", Z: ");
  Serial.print(g.gyro.z - g_z_err);
  Serial.println(" rad/s");

  Serial.print("Temperature: ");
  Serial.print(temp.temperature);
  Serial.println(" degC");

  Serial.println("");
  delay(500);
}
