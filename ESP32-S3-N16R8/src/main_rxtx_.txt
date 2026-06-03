#include <Arduino.h>

#define RXD1 41
#define TXD1 42

void setup() {
  Serial.begin(115200);   // USB / debug
  Serial1.begin(9600, SERIAL_8N1, RXD1, TXD1);
  Serial.println("UART1 prêt");
}

void loop() {
  if (Serial1.available()) {
    char c = Serial1.read();
    Serial.print(c);   // renvoie vers le PC
  }
}
