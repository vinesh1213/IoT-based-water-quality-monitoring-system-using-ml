#include <WiFi.h>
#include <HTTPClient.h>

#define PH_PIN 34
#define TURB_PIN 35

const char* ssid = "VineshIoT";
const char* password = "12345678";
const char* serverURL = "http://192.168.0.109:8000/api/data/";

float neutralVoltage = 2.4;
float slope = 0.18;

int turbidity_clean = 3200;
int turbidity_dirty = 1500;

int readAverage(int pin) {
  int sum = 0;
  for (int i = 0; i < 10; i++) {
    sum += analogRead(pin);
    delay(10);
  }
  return sum / 10;
}

void setup() {
  Serial.begin(115200);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void loop() {

  int phRaw = readAverage(PH_PIN);
  int turbRaw = readAverage(TURB_PIN);

  float voltage = phRaw * (3.3 / 4095.0);
  float pHValue = 7 + ((neutralVoltage - voltage) / slope);

  float turbidity = map(turbRaw, turbidity_dirty, turbidity_clean, 1000, 0);
  turbidity = constrain(turbidity, 0, 1000);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");

    String json = "{\"ph\": " + String(pHValue,2) +
                  ", \"turbidity\": " + String(turbidity,2) +
                  ", \"temperature\": 25}";

    int response = http.POST(json);

    // 🔹 Optional: only print response (no sensor values)
    Serial.println(response);

    http.end();
  }

  delay(5000);
}