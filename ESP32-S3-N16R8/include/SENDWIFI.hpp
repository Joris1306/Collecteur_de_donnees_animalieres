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

#define IP "90.59.66.6"
//#define IP "10.22.113.233"



class SendData
{
    private:
        const char *ssid = "test";
        const char *password = "testesp@";
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

        // SD
        int SendAllData(String File_name, int width, int height, float temperature, float humudity, String latitude, String longitude, String annee, String mois, String jours, String heures, String minutes, String secondes, float niv_batterie);

        // Directement PSRAM
        int SendAllDataPSRAM(uint8_t* imgData, size_t imgSize, int width, int height, float temperature, float humudity, String latitude, String longitude, String annee, String mois, String jours, String heures, String minutes, String secondes, float niv_batterie);

};

#endif 