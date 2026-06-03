#include "SDM.h"

SPIClass hspi(HSPI); // définition unique ici

void initSD() 
{
    pinMode(SD_CS, OUTPUT);
    digitalWrite(SD_CS, HIGH);

    hspi.begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS);

    if (!SD.begin(SD_CS, hspi, 4000000)) 
    { 
        DEBUG_PRINT("Erreur SD sur HSPI");
        
        if (!SD.begin(SD_CS, hspi, 1000000)) 
        {
            DEBUG_PRINT("Erreur SD même à 1MHz. Vérifiez le câblage.");
        } 
        else 
        {
            DEBUG_PRINT("SD OK sur HSPI à 1MHz.");
        }
    } 
    else 
    {
        DEBUG_PRINT("SD OK sur HSPI à 4MHz.");
    }
}
