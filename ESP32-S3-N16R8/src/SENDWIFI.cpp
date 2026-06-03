#include "SENDWIFI.hpp"

// ===================================================
// ============ Fonction séparée =====================
// ===================================================

/**
 * @brief Constructeur
 */
SendData::SendData() {}

/**
 * @brief Destructeur
 */
SendData::~SendData() {}

/**
 * @brief Récupération de l'URL du serveur image
 */
String SendData::getserverURLimage()
{
    return serverURLimage;
}

/**
 * @brief Récupération de l'URL du serveur data
 */
String SendData::getserverURLdata()
{
    return serverURLdata;
}

// ====================================================
// ================ Envoi des données =================
// ====================================================

/**
 * @brief Envoi de toutes les données (image + méta-données)
 */
int SendData::SendAllData(String File_name, int width, int height, float temperature, float humudity, String latitude, String longitude, String annee, String mois, String jours, String heures, String minutes, String secondes, float niv_batterie)
{
    // =============== Initialisation WiFi ================

    WiFi.begin(ssid, password);
    Serial.println("Connexion au WiFi...");

    int retry = 0;
    while (WiFi.status() != WL_CONNECTED && retry < 50)
    {
        delay(200);
        Serial.print(".");
        retry++;
    }

    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("\nWiFi échec");
        return -1;
    }

    Serial.println("\nWiFi connecté");

    File file;

    HTTPClient http;

    int index = 5;
    int httpCode = 0;
    int error = 0;
    retry = 0;
    Serial.println("lo");

    if (SD.begin(CS, hspi))
    {
        Serial.println("la");

        file = SD.open(File_name, FILE_READ);

        Serial.println("Envoi de l'image " + File_name);

        if (!file)
        {
            return -1;
        }

        while (file.available())
        {
            retry = 0;
            httpCode = 0;
            int len = file.read((uint8_t *)TabToSend, RAW_CHUNK_SIZE);
            while (httpCode != 200 && retry < RetryNum)
            {
                http.begin(serverURLimage);
                http.addHeader("Content-Type", "application/octet-stream");
                httpCode = http.POST((uint8_t *)TabToSend, len);
                http.end();
                retry++;
            }

            if (httpCode != 200)
            {
                error++;
            }
        }
        file.close();
    }
    else
    {
        Serial.println("Erreur de montage de la SD");
        return -1;
    }

    // Après la boucle d'envoi d'image
    delay(100);

    StaticJsonDocument<256> doc;

    // 320x240

    doc["IMG.TYPE"] = "JPEG";
    doc["IMG.WIDTH"] = width;
    doc["IMG.HEIGHT"] = height;
    doc["WHEATER.TEMP"] = temperature;
    doc["WHEATER.HUM"] = humudity;
    doc["GPS.LAT"] = latitude;
    doc["GPS.LONG"] = longitude;
    doc["DATE.YEAR"] = annee;
    doc["DATE.MONTH"] = mois;
    doc["DATE.DAY"] = jours;
    doc["DATE.HOUR"] = heures;
    doc["DATE.MINUTE"] = minutes;
    doc["DATE.SECOND"] = secondes;
    doc["CAM.BATTERY"] = niv_batterie;
    doc["CAM.ID"] = 1;

    // Sérialiser en String
    String jsonString;
    serializeJson(doc, jsonString);

    http.end();
    httpCode = 0;

    while (httpCode != 200 && retry < RetryNum)
    {
        http.begin(serverURLdata);
        http.addHeader("Content-Type", "application/json");
        httpCode = http.POST(jsonString);
        http.end();
        retry++;
    }

    

    if (httpCode != 200)
    {
        error++;
    }
    else if(httpCode == 200)
    {
        Serial.println("Données méta envoyées avec succès");
    }
    else
    {
        Serial.println("Erreur inconnue lors de l'envoi des méta-données");
    }

    if (error > 0)
    {
        Serial.println("Erreur d'envoi %d chunks mal envoyés (Chunk image ou Meta-data : JSON)" + error);
        return -1;
    }
    else
    {
        Serial.println("Envoi des données réussi");
        return 0;
    }
}

/**
 * @brief Envoi de toutes les données (image + méta-données) directement depuis la PSRAM
 */
int SendData::SendAllDataPSRAM(uint8_t* imgData, size_t imgSize, int width, int height, float temperature, float humudity, String latitude, String longitude, String annee, String mois, String jours, String heures, String minutes, String secondes, float niv_batterie)
{
    // =============== Initialisation WiFi ================

    WiFi.begin(ssid, password);
    Serial.println("Connexion au WiFi...");

    int retry = 0;
    while (WiFi.status() != WL_CONNECTED && retry < 50)
    {
        delay(200);
        Serial.print(".");
        retry++;
    }

    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("\nWiFi échec");
        return -1;
    }

    Serial.println("\nWiFi connecté");

    HTTPClient http;

    int httpCode = 0;
    int error = 0;
    retry = 0;
    Serial.println("lo");

    Serial.println("Envoi de l'image depuis la PSRAM");

    size_t sentBytes = 0;

    while (sentBytes < imgSize)
    {
        retry = 0;
        httpCode = 0;

        size_t chunkSize = std::min((size_t)RAW_CHUNK_SIZE, imgSize - sentBytes);

        while (httpCode != 200 && retry < RetryNum)
        {
            http.begin(serverURLimage);
            http.addHeader("Content-Type", "application/octet-stream");
            httpCode = http.POST(imgData + sentBytes, chunkSize);
            http.end();
            retry++;
        }

        if (httpCode != 200)
        {
            error++;
        }

        sentBytes += chunkSize;
    }

    // Après la boucle d'envoi d'image
    delay(100);

    StaticJsonDocument<256> doc;

    doc["IMG.TYPE"] = "JPEG";
    doc["IMG.WIDTH"] = width;
    doc["IMG.HEIGHT"] = height;
    doc["WHEATER.TEMP"] = temperature;
    doc["WHEATER.HUM"] = humudity;
    doc["GPS.LAT"] = latitude;
    doc["GPS.LONG"] = longitude;
    doc["DATE.YEAR"] = annee;
    doc["DATE.MONTH"] = mois;
    doc["DATE.DAY"] = jours;
    doc["DATE.HOUR"] = heures;
    doc["DATE.MINUTE"] = minutes;
    doc["DATE.SECOND"] = secondes;
    doc["CAM.BATTERY"] = niv_batterie;
    doc["CAM.ID"] = 1;

    // Sérialiser en String
    String jsonString;
    serializeJson(doc, jsonString);
    http.end();
    httpCode = 0;
    while (httpCode != 200 && retry < RetryNum)
    {
        http.begin(serverURLdata);
        http.addHeader("Content-Type", "application/json");
        httpCode = http.POST(jsonString);
        http.end();
        retry++;
    }
    if (httpCode != 200)
    {
        error++;
    }
    else if(httpCode == 200)
    {
        Serial.println("Données méta envoyées avec succès");
    }
    else
    {
        Serial.println("Erreur inconnue lors de l'envoi des méta-données");
    }
    if (error > 0)
    {
        Serial.println("Erreur d'envoi %d chunks mal envoyés (Chunk image ou Meta-data : JSON)" + error);
        return -1;
    }
    else
    {
        Serial.println("Envoi des données réussi");
        return 0;
    }

    WiFi.disconnect(true);
}