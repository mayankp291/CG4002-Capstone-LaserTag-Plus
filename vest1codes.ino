#include <IRremote.h> // >v3.0.0
#include <Adafruit_NeoPixel.h>      

#define PIN_RECV 3
#define LED_COUNT 7
const int ledPin = A2;


int healthPoint = 100;
const int buzzer = 4;
Adafruit_NeoPixel leds = Adafruit_NeoPixel(LED_COUNT, ledPin, NEO_GRB + NEO_KHZ800);
void setup()  
{  
  Serial.begin(9600); //initialize serial connection to print on the Serial Monitor of the Arduino IDE
  IrReceiver.begin(PIN_RECV); // Initializes the IR receiver object
  leds.begin();
  clearLEDs();
  leds.show();
  // pinMode(ledPin, OUTPUT);      // declare LED as output
  pinMode(buzzer, OUTPUT);
}  

void clearLEDs() {
  for(int i = 0; i < LED_COUNT; i++) {
    leds.setPixelColor(i, 0);
  }
}

void playTone(int healthPoint) {
    tone(buzzer, healthPoint * 20); // Send 1KHz sound signal...
    delay(500);        // ...for 1 sec
    noTone(buzzer);     // Stop sound...
    delay(500);        // ...for 1sec     
}

void led() {
    for(int i = 0; i < LED_COUNT; i++) {
      leds.setPixelColor(i, 150);
    }
    leds.show();
    delay(500);
    for(int i = 0; i < LED_COUNT; i++) {
      leds.setPixelColor(i, 0xFF0000);
    }
    leds.show();
    delay(500);
    for(int i = 0; i < LED_COUNT; i++) {
      leds.setPixelColor(i, 50);
    }
    leds.show();
    delay(500);
    clearLEDs();
    leds.show();
}
                               
void loop()  
{  
  if(healthPoint <= 0) {
      healthPoint = 100;
  }
  if (IrReceiver.decode()) {
    Serial.println("Received something...");
    if(IrReceiver.decodedIRData.address == 0x0102) {
        Serial.println("Shotted!");
        healthPoint = healthPoint - 10;
        led();
        playTone(healthPoint);
        // tone(buzzer, 1000); // Send 1KHz sound signal...
        // delay(500);        // ...for 1 sec
        // noTone(buzzer);     // Stop sound...
        // delay(500);        // ...for 1sec   
    }    
    IrReceiver.printIRResultShort(&Serial); // Prints a summary of the received data
    Serial.println();
    IrReceiver.begin(PIN_RECV); // Important, enables to receive the next IR signal
  }  
}