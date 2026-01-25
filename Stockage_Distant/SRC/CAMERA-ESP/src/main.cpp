#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

// === WiFi credentials ===
const char* ssid = "ESP-CAM";
const char* password = "ESP-CAM";

// === Select your ESP32-CAM model ===
#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

WebServer server(81);

void startCameraServer();

void startCameraServer() {
  server.on("/", HTTP_GET, []() {
    String html = R"(
      <html>
      <body>
        <h1>ESP32-CAM Stream</h1>
        <img src="/stream" style="width:100%; max-width:800px;">
      </body>
      </html>
    )";
    server.send(200, "text/html", html);
  });

  server.on("/stream", HTTP_GET, []() {
    WiFiClient client = server.client();
    client.write((uint8_t*)"HTTP/1.1 200 OK\r\nContent-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n", 79);
    
    while (client.connected()) {
      camera_fb_t* fb = esp_camera_fb_get();
      if (!fb) {
        delay(10);
        continue;
      }
      
      client.write((uint8_t*)"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ", 54);
      client.print(fb->len);
      client.write((uint8_t*)"\r\n\r\n", 4);
      client.write(fb->buf, fb->len);
      client.write((uint8_t*)"\r\n", 2);
      esp_camera_fb_return(fb);
      delay(33);
    }
  });

  server.begin();
  Serial.println("Camera server started on port 81");
}

// Callback when a device connects
void onSTAConnected(WiFiEvent_t event, WiFiEventInfo_t info) {
  Serial.println("Device connected to AP!");
  Serial.print("MAC Address: ");
  for (int i = 0; i < 6; i++) {
    Serial.printf("%02X", info.wifi_sta_connected.bssid[i]);
    if (i < 5) Serial.print(":");
  }
  Serial.println();
}

// Callback when a device disconnects
void onSTADisconnected(WiFiEvent_t event, WiFiEventInfo_t info) {
  Serial.println("Device disconnected from AP!");
}

void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println("\nBooting...");

  // Create WiFi Access Point
  const char* ap_ssid = "ESP32-CAM";
  const char* ap_password = "12345678";
  
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ap_ssid, ap_password);
  
  // Register WiFi event callbacks
  WiFi.onEvent(onSTAConnected, ARDUINO_EVENT_WIFI_AP_STACONNECTED);
  WiFi.onEvent(onSTADisconnected, ARDUINO_EVENT_WIFI_AP_STADISCONNECTED);
  
  IPAddress IP = WiFi.softAPIP();
  Serial.println("Access Point started!");
  Serial.print("SSID: ");
  Serial.println(ap_ssid);
  Serial.print("Password: ");
  Serial.println(ap_password);
  Serial.print("IP: ");
  Serial.println(IP);

  // Camera config
  camera_config_t config;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 10;
  config.fb_count = 2;
  config.xclk_freq_hz = 20000000;  // Add this line - 20MHz clock
  config.ledc_timer = LEDC_TIMER_0;
  config.ledc_channel = LEDC_CHANNEL_0;
  
  config.pin_pwdn  = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;

  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d0 = Y2_GPIO_NUM;

  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;

  // Init camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x", err);
    return;
  }

  // Start streaming server
  startCameraServer();
  Serial.println("Camera ready! Stream available at:");
  Serial.print("http://");
  Serial.print(WiFi.softAPIP());
  Serial.println(":81");
}

void loop() {
  server.handleClient();
  delay(10);
}
