#include <IRremote.h> // >v3.0.0
                                            
#define PIN_SEND 3
int ledPin = 4;
const int buzzer = 2;
int inputPin = A1;

int buttonState = LOW; //this variable tracks the state of the button, low if not pressed, high if pressed
long lastDebounceTime = 0;  // the last time the output pin was toggled
long debounceDelay = 50;    // the debounce time; increase if the output flickers

int bullets = 6;

void setup()  
{  
  Serial.begin(9600);
  IrSender.begin(PIN_SEND); // Initializes IR sender
  pinMode(ledPin, OUTPUT);      // declare LED as output
  pinMode(buzzer, OUTPUT);
  pinMode(inputPin, INPUT);     // declare pushbutton as input
}  
void playTone(int bullets) {
    tone(buzzer, bullets * 200); // Send 1KHz sound signal...
    delay(500);        // ...for 1 sec
    noTone(buzzer);     // Stop sound...
    delay(500);        // ...for 1sec     
}
                               
void loop()  
{  
  if(bullets <= 0) {
      bullets = 6;
  }
  buttonState = digitalRead(inputPin);
  if( (millis() - lastDebounceTime) > debounceDelay) {
    if (buttonState == HIGH) {            // check if the input is HIGH
      lastDebounceTime = millis(); //set the current time

      IrSender.sendNEC(0x0102, 0x34, 0); // the address 0x0102 with the command 0x34 is sent 
      Serial.println("Triggered!!!");
      Serial.println(bullets);
      digitalWrite(ledPin, HIGH);  // turn LED OFF
      playTone(bullets);
      bullets = bullets - 1;
      delay(500); // wait for one second

    } else {
      lastDebounceTime = millis(); //set the current time

      digitalWrite(ledPin, LOW); // turn LED ON
    }
  }

}