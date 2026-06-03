#ifndef __SENDWIFI_HPP__
#define __SENDWIFI_HPP__

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
#include "SDM.h"
#include "CONFIG.h"


#define RAW_CHUNK_SIZE 32768
#define RetryNum 2

#define IP "10.26.202.173"

class SendData
{
    private:
        const char *ssid = "Joris's A56";
        const char *password = "Jojo1306";
        String serverURLimage = "http://" + String(IP) + ":5050/api/image";
        String serverURLdata = "http://" + String(IP) + ":5050/api/data";
        const int SCK = SD_SCK;
        const int MISO = SD_MISO;
        const int MOSI = SD_MOSI;
        const int CS = SD_CS;
        char TabToSend[RAW_CHUNK_SIZE];

    public:
        SendData();
        ~SendData();
        String getserverURLimage();
        String getserverURLdata();
        int SendAllData(String File_name, float temperature, float humudity, String latitude, String longitude, String annee, String mois, String jours, String heures, String minutes, String secondes, float niv_batterie);
};

#endif 