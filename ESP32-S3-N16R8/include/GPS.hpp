#ifndef __GPS_HPP__
#define __GPS_HPP__

#include <Arduino.h>

class GPS {
private:
    int _RX, _TX;
    String gpsData;
    String latitude, longitude;
    String hours, minutes, seconds;
    String day, month, year;

public:
    GPS(int RX, int TX);
    void update();
    bool gpsready();
    void ParseRMC(String trame);
    String convertToDecimal(String value, String dir);

    // Getters
    String getLatitude()  { return latitude; }
    String getLongitude() { return longitude; }
    String getHours()     { return hours; }
    String getMinutes()   { return minutes; }
    String getSeconds()   { return seconds; }
    String getDay()       { return day; }
    String getMonth()     { return month; }
    String getYear()      { return year; }
};

GPS::GPS(int RX, int TX) : _RX(RX), _TX(TX) {
    latitude = "0.000000"; longitude = "0.000000";
    hours = "00"; minutes = "00"; seconds = "00";
    day = "01"; month = "01"; year = "2000";

    // Utilisation de Serial1 pour ESP32 (ajustez si autre carte)
    Serial1.begin(9600, SERIAL_8N1, _RX, _TX);
}

bool GPS::gpsready() {
    while (Serial1.available()) {
        String trame = Serial1.readStringUntil('\n');
        // On cherche une trame RMC valide avec le statut 'A' (Active)
        if ((trame.startsWith("$GPRMC") || trame.startsWith("$GNRMC")) && trame.indexOf(",A,") > 0) {
            gpsData = trame; 
            return true;
        }
    }
    return false;
}

void GPS::update() {
    // Si on a une donnée en attente (venant de gpsready), on la traite
    if (gpsData.length() > 0) {
        ParseRMC(gpsData);
        gpsData = ""; // On vide après traitement pour éviter de parser deux fois
    } 
}

void GPS::ParseRMC(String trame) {
    int idx = 0;
    String fields[12];
    
    // Initialisation des champs pour éviter les résidus
    for(int i=0; i<12; i++) fields[i] = "";

    // Séparation manuelle des champs par la virgule
    for (int i = 0; i < trame.length(); i++) {
        if (trame[i] == ',') {
            idx++;
            if (idx >= 12) break;
        } else {
            fields[idx] += trame[i];
        }
    }

    // Double vérification du statut (Champ 2)
    if (fields[2] != "A") return;

    // Heure UTC (Champ 1 : hhmmss.ss)
    if (fields[1].length() >= 6) {
        hours   = fields[1].substring(0, 2);
        minutes = fields[1].substring(2, 4);
        seconds = fields[1].substring(4, 6);
    }

    // Latitude (Champs 3 et 4)
    if (fields[3].length() > 0)
        latitude = convertToDecimal(fields[3], fields[4]);

    // Longitude (Champs 5 et 6)
    if (fields[5].length() > 0)
        longitude = convertToDecimal(fields[5], fields[6]);

    // Date (Champ 9 : ddmmyy)
    if (fields[9].length() == 6) {
        day   = fields[9].substring(0, 2);
        month = fields[9].substring(2, 4);
        year  = "20" + fields[9].substring(4, 6);
    }
}

String GPS::convertToDecimal(String value, String dir) {
    if (value.length() < 4) return "0.000000";

    double val = value.toDouble();
    int deg = (int)(val / 100);
    double minutes = val - (deg * 100);
    double decimal = deg + (minutes / 60.0);

    if (dir == "S" || dir == "W") decimal *= -1;

    return String(decimal, 6);
}

#endif