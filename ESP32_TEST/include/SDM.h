#ifndef SDM_H
#define SDM_H

#include <SPI.h>
#include <SD.h>
#include "CONFIG.h"



// Déclaration externe (pas de définition ici)
extern SPIClass hspi;

// Déclaration de la fonction
void initSD();

#endif // SDM_H
