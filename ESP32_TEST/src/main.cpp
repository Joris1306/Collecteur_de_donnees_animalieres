#include <Arduino.h>
#include "SDM.h"
#include "CAM.hpp"
#include <DHT.h>
#include "RTC.hpp"
#include "GPS.hpp"
#include "BAT.hpp"
#include "SENDWIFI.hpp"

#define RefreshGPS 86400000 // 24h en ms

BAT bat(BAT_PIN);
RTC rtc;
GPS gps(GPS_RX_PIN, GPS_TX_PIN);
CAM cam;
DHT dht(DHT_PIN, DHT22);
SendData send;

#define RefreshGPS_US 86400000000ULL // 24h en microsecondes

RTC_DATA_ATTR uint64_t lastGPSResetTime = 0;
RTC_DATA_ATTR bool activate = false;


bool isGPSTimeout()
{
    uint64_t now = esp_timer_get_time(); // µs depuis boot 

    if (lastGPSResetTime == 0)
        return true; // Premier boot

    if ((now - lastGPSResetTime) < 0)
    {
        // Cas où le timer a overflow (après ~584942 ans)
        lastGPSResetTime = now;
        return true;
    }
    else
    {
        return false;
    }
}


void WakeUpLoop() 
{
    digitalWrite(PWR_U_D, HIGH); // Alimentation ON 

    delay(1000); // Attente stabilisation alim

    initSD();
    cam.begin();

    delay(1000); // Attente stabilisation

    String fileName = "/pic.jpg";
    cam.takeAndSavePhoto(fileName.c_str()); 

    dht.begin(); // Attend 2 secondes avant de lire les données
    delay(1000);

    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    float batteryPercent = bat.ReadPercent();

    if (!activate || isGPSTimeout())
    {
        activate = true;
        Serial.println("Recherche GPS");

        while (!gps.gpsready())
        {
            Serial.println("En attente GPS...");
            delay(1000);
        }

        gps.update();

        rtc.updateFromGPS(
            gps.getLatitude(),
            gps.getLongitude(),
            gps.getHours(),
            gps.getMinutes(),
            gps.getSeconds(),
            gps.getDay(),
            gps.getMonth(),
            gps.getYear()
        );


        rtc.getDateTime();

        lastGPSResetTime = esp_timer_get_time(); // Mise à jour du timestamp
    }
    else
    {
        Serial.println("RTC interne uniquement");
        rtc.getDateTime();
    }

    Serial.println("Lat: " + String(rtc.getLat()));
    Serial.println("Long: " + String(rtc.getLon()));

    // Variable Interne RTC
    String savedLat = rtc.getLat();
    String savedLon = rtc.getLon();
    String year = rtc.getYear();
    String month = rtc.getMonth();
    String day = rtc.getDay();
    String hours = rtc.getHours();
    String minutes = rtc.getMinutes();
    String seconds = rtc.getSeconds();

    setCpuFrequencyMhz(240);

    send.SendAllData(fileName, temperature, humidity, savedLat, savedLon, year, month, day, hours, minutes, seconds, batteryPercent);

    setCpuFrequencyMhz(80);
    
    digitalWrite(PWR_U_D, LOW); // Alimentation OFF 
}

void mainTask(void *parameter) 
{
    Serial.begin(115200);

    setCpuFrequencyMhz(80);

    pinMode(PWR_U_D, OUTPUT);
    pinMode(WAKE_UP, INPUT_PULLDOWN);

    esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();

    if (cause == ESP_SLEEP_WAKEUP_EXT1)
    {
        WakeUpLoop();

        while (digitalRead(WAKE_UP) == HIGH)
        {
            delay(1000);
        }
    }

    esp_sleep_enable_ext1_wakeup(
        1ULL << WAKE_UP,
        ESP_EXT1_WAKEUP_ANY_HIGH
    );
    
    esp_deep_sleep_start();
}


void setup() 
{
    xTaskCreatePinnedToCore(
      mainTask,
      "mainTask",
      4096,
      NULL,
      1,
      NULL,
      0    // CORE 0
    );
}

void loop() 
{
    // Rien ici
}