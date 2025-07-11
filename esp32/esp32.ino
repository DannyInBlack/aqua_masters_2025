#include "ESC.h";

#define TX1 1  // ESP32 RX (connected to Arduino TX via voltage divider)
#define RX1 3  // Not used for receiving

#define M1 32
#define M2 33
#define M3 25
#define M4 26
#define M5 27
#define M6 14
#define M7 12
#define M8 13

#define SPEED_MAX (1000)                                  // Set the Minimum Speed in microseconds
#define STOPPED (1500)                                  // Set the Minimum Speed in microseconds
#define SPEED_MAXR (2000)

ESC escs[8]{
  ESC(M1, SPEED_MAX, SPEED_MAXR, 1000),
  ESC(M2, SPEED_MAX, SPEED_MAXR, STOPPED),
  ESC(M3, SPEED_MAX, SPEED_MAXR, STOPPED),
  ESC(M4, SPEED_MAX, SPEED_MAXR, STOPPED),
  ESC(M5, SPEED_MAX, SPEED_MAXR, STOPPED),
  ESC(M6, SPEED_MAX, SPEED_MAXR, STOPPED),
  ESC(M7, SPEED_MAX, SPEED_MAXR, STOPPED),
  ESC(M8, SPEED_MAX, SPEED_MAXR, 1000)
};

int motorValues[8];

void setup() {
  Serial.begin(115200);   // Serial monitor
  Serial2.begin(115200, SERIAL_8N1, TX1, RX1);  // Start UART2 (baud: 9600)
  
  Serial.println("Setting up ESP motors...");
  // escs[0].calib();
  // escs[2].calib();
  // escs[3].calib();
  // escs[4].calib();
  // escs[5].calib();
  // escs[6].calib();
  // escs[7].calib();
  escs[0].arm();
  escs[2].arm(); 
  escs[3].arm(); 
  escs[4].arm(); 
  escs[5].arm();
  escs[6].arm();
  escs[7].arm();

  delay(4000);
}

void getFromPi(){
  if (Serial2.available()) {
    String input = Serial2.readStringUntil('\n');
    int numParsed = sscanf(input.c_str(), "%d %d %d %d %d %d %d %d",
                           &motorValues[0], &motorValues[1], &motorValues[2], &motorValues[3],
                           &motorValues[4], &motorValues[5], &motorValues[6], &motorValues[7]);
    escs[0].speed(motorValues[0]);
    escs[2].speed(motorValues[2]);
    escs[3].speed(motorValues[3]);
    escs[4].speed(motorValues[4]);
    escs[5].speed(motorValues[5]);
    escs[6].speed(motorValues[6]);
    escs[7].speed(motorValues[7]);
  }
  delay(50);
}

// Test motor thrust in both directions (bidirectional thrust test)
void test(int motor = 0) {
  escs[motor].speed(1000);
  delay(5000);
  escs[motor].speed(1500);
  delay(5000);
  escs[motor].speed(2000);
  delay(5000);
  escs[motor].speed(1500);
  delay(5000);
  escs[motor].stop();
}

void loop() {
  getFromPi();
  // test(0);
}