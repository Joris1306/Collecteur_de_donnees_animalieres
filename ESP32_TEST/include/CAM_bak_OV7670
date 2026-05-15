#ifndef __CAM_HPP__
#define __CAM_HPP__

#include <Arduino.h>
#include <Wire.h>
#include <SD.h>

// Adresse I2C de l'OV7670
#define OV7670_ADDR 0x21

// --- GPIO OV7670 (Pins de l'utilisateur) ---
#define XCLK_GPIO_NUM   23
#define SIOD_GPIO_NUM   21 // SDA
#define SIOC_GPIO_NUM   22 // SCL

#define Y2_GPIO_NUM     4   // D0
#define Y3_GPIO_NUM     5   // D1
#define Y4_GPIO_NUM     18  // D2
#define Y5_GPIO_NUM     19  // D3
#define Y6_GPIO_NUM     36  // D4
#define Y7_GPIO_NUM     39  // D5
#define Y8_GPIO_NUM     34  // D6
#define Y9_GPIO_NUM     35  // D7

#define VSYNC_GPIO_NUM  32
#define HREF_GPIO_NUM   33
#define PCLK_GPIO_NUM   25

#define TIMEOUT_MS 1000

// Taille du buffer pour écriture SD
#define BUFFER_SIZE 512

class CAM
{
    private:
        int _width  = 640;
        int _height = 480;
        uint8_t _sdBuffer[BUFFER_SIZE];
        size_t _bufferIndex = 0;

    public:
        CAM() {}

        bool begin();
        void CaptureFrame(const char* filename);

    private:
        void writeReg(uint8_t reg, uint8_t val);
        void init_OV7670();
        uint8_t readByteFast(); 
        bool waitForPin(int pin, int state, unsigned long timeout);
        inline bool readPinFast(int pin);
        void flushBuffer(File &f);
};

bool CAM::begin()
{
    // Configuration du XCLK à 8 MHz
    ledcSetup(0, 8000000, 1);  // 8 MHz pour OV7670
    ledcAttachPin(XCLK_GPIO_NUM, 0);
    ledcWrite(0, 128);  // 50% duty cycle pour onde carrée
    
    // Configuration des pins de données comme INPUT
    const int dataPins[] = {Y2_GPIO_NUM, Y3_GPIO_NUM, Y4_GPIO_NUM, Y5_GPIO_NUM, 
                           Y6_GPIO_NUM, Y7_GPIO_NUM, Y8_GPIO_NUM, Y9_GPIO_NUM};
    
    for(int i = 0; i < 8; i++) {
        pinMode(dataPins[i], INPUT);
    }

    // Configuration des pins de contrôle
    pinMode(PCLK_GPIO_NUM, INPUT);
    pinMode(VSYNC_GPIO_NUM, INPUT);
    pinMode(HREF_GPIO_NUM, INPUT);

    // Initialisation I2C
    Wire.begin(SIOD_GPIO_NUM, SIOC_GPIO_NUM);
    Wire.setClock(100000);  // 100kHz pour l'initialisation
    delay(100);

    init_OV7670();
    return true;
}

void CAM::writeReg(uint8_t reg, uint8_t val)
{
    Wire.beginTransmission(OV7670_ADDR);
    Wire.write(reg);
    Wire.write(val);
    if(Wire.endTransmission() != 0) 
    {
        Serial.printf("I2C error writing reg 0x%02X\n", reg);
    }
    delayMicroseconds(100);
}

void CAM::init_OV7670()
{
    Serial.println("Initializing OV7670...");
    
    // 1. Reset
    writeReg(0x12, 0x80); 
    delay(100);
    
    // 2. Configuration de base
    writeReg(0x12, 0x04);    // COM7: RGB Output, VGA
    
    // 3. Configure clock (divider)
    writeReg(0x11, 0x01);    // CLKRC: internal clock /2 (8MHz / 2 = 4MHz)
    
    // 4. Format RGB565
    writeReg(0x40, 0xD0);    // COM15: RGB565, Full range
    
    // 5. Désactiver AEC/AGC
    writeReg(0x13, 0x00);    // COM8: No AGC, AEC
    
    // 6. Configuration VGA (640x480)
    writeReg(0x17, 0x13);    // HSTART
    writeReg(0x18, 0x01);    // HSTOP
    writeReg(0x32, 0xB6);    // HREF
    writeReg(0x19, 0x02);    // VSTART
    writeReg(0x1A, 0x7A);    // VSTOP
    writeReg(0x03, 0x0A);    // VREF
    
    // 7. Configuration de la matrice de couleur (simplifiée)
    writeReg(0x4F, 0x80);    // MTX1
    writeReg(0x50, 0x80);    // MTX2
    writeReg(0x51, 0x00);    // MTX3
    writeReg(0x52, 0x22);    // MTX4
    writeReg(0x53, 0x5E);    // MTX5
    writeReg(0x54, 0x80);    // MTX6
    
    // 8. Configuration divers
    writeReg(0x6B, 0x0A);    // PLL
    writeReg(0x15, 0x02);    // COM10: VSYNC negative, HREF negative
    
    // 9. Désactiver les effets spéciaux
    writeReg(0x0C, 0x00);    // COM3: No scaling
    writeReg(0x3E, 0x00);    // COM14: No scaling
    
    Serial.println("OV7670 initialization complete");
}

bool CAM::waitForPin(int pin, int state, unsigned long timeout)
{
    unsigned long start = millis();
    while(readPinFast(pin) != state)
    {
        if(millis() - start > timeout) {
            Serial.printf("Timeout waiting for pin %d to be %d\n", pin, state);
            return false;
        }
    }
    return true;
}

inline bool CAM::readPinFast(int pin)
{
    // Lecture directe des registres GPIO
    if(pin < 32) 
    {
        return (GPIO.in >> pin) & 0x1;
    } 
    else 
    {
        return (GPIO.in1.val >> (pin - 32)) & 0x1;
    }
}

uint8_t CAM::readByteFast()
{
    // Les pins D4-D7 (36, 39, 34, 35) sont sur GPIO_IN1 (32-39)
    // Les pins D0-D3 (4, 5, 18, 19) sont sur GPIO_IN (0-31)
    
    uint8_t value = 0;
    uint32_t reg_low = GPIO.in;      // Pins 0-31
    uint32_t reg_high = GPIO.in1.val; // Pins 32-39
    
    // D0 (Y2) - pin 4
    if (reg_low & (1 << Y2_GPIO_NUM)) value |= (1 << 0);
    
    // D1 (Y3) - pin 5
    if (reg_low & (1 << Y3_GPIO_NUM)) value |= (1 << 1);
    
    // D2 (Y4) - pin 18
    if (reg_low & (1 << Y4_GPIO_NUM)) value |= (1 << 2);
    
    // D3 (Y5) - pin 19
    if (reg_low & (1 << Y5_GPIO_NUM)) value |= (1 << 3);
    
    // D4 (Y6) - pin 36 -> GPIO_IN1 bit 4
    if (reg_high & (1 << (Y6_GPIO_NUM - 32))) value |= (1 << 4);
    
    // D5 (Y7) - pin 39 -> GPIO_IN1 bit 7
    if (reg_high & (1 << (Y7_GPIO_NUM - 32))) value |= (1 << 5);
    
    // D6 (Y8) - pin 34 -> GPIO_IN1 bit 2
    if (reg_high & (1 << (Y8_GPIO_NUM - 32))) value |= (1 << 6);
    
    // D7 (Y9) - pin 35 -> GPIO_IN1 bit 3
    if (reg_high & (1 << (Y9_GPIO_NUM - 32))) value |= (1 << 7);
    
    return value;
}

void CAM::flushBuffer(File &f)
{
    if(_bufferIndex > 0)
    {
        f.write(_sdBuffer, _bufferIndex);
        _bufferIndex = 0;
    }
}

void CAM::CaptureFrame(const char* filename)
{
    Serial.printf("Starting capture to: %s\n", filename);
    
    File f = SD.open(filename, FILE_WRITE);
    if(!f)
    {
        Serial.println("Failed to open file on SD card!");
        return;
    }
    
    _bufferIndex = 0;
    
    // Attendre début de trame (VSYNC HIGH -> LOW)
    Serial.println("Waiting for VSYNC HIGH...");
    if(!waitForPin(VSYNC_GPIO_NUM, HIGH, TIMEOUT_MS)) {
        Serial.println("VSYNC HIGH timeout!");
        f.close();
        return;
    }
    
    Serial.println("Waiting for VSYNC LOW (start of frame)...");
    if(!waitForPin(VSYNC_GPIO_NUM, LOW, TIMEOUT_MS)) {
        Serial.println("VSYNC LOW timeout!");
        f.close();
        return;
    }
    
    Serial.println("Starting frame capture...");
    unsigned long startTime = millis();
    unsigned long lastPrint = startTime;
    int linesCaptured = 0;
    
    // Capturer toutes les lignes
    for(int h = 0; h < _height; h++)
    {
        // Attendre début de ligne (HREF HIGH)
        if(!waitForPin(HREF_GPIO_NUM, HIGH, TIMEOUT_MS))
        {
            Serial.printf("HREF HIGH timeout at line %d!\n", h);
            break;
        }
        
        // Pour chaque pixel (2 octets par pixel en RGB565)
        for(int w = 0; w < _width; w++)
        {
            // Premier octet (MSB du pixel) - sur front montant de PCLK
            while(readPinFast(PCLK_GPIO_NUM) == HIGH); // Attendre LOW
            while(readPinFast(PCLK_GPIO_NUM) == LOW);  // Attendre HIGH (front montant)
            uint8_t byte1 = readByteFast();
            
            // Deuxième octet (LSB du pixel) - sur front montant suivant
            while(readPinFast(PCLK_GPIO_NUM) == HIGH); // Attendre LOW
            while(readPinFast(PCLK_GPIO_NUM) == LOW);  // Attendre HIGH (front montant)
            uint8_t byte2 = readByteFast();
            
            // Stocker dans le buffer
            _sdBuffer[_bufferIndex++] = byte1;
            _sdBuffer[_bufferIndex++] = byte2;
            
            // Vider le buffer si plein
            if(_bufferIndex >= BUFFER_SIZE)
            {
                flushBuffer(f);
            }
        }
        
        // Attendre fin de ligne (HREF LOW)
        waitForPin(HREF_GPIO_NUM, LOW, TIMEOUT_MS);
        
        linesCaptured++;
        
        // Afficher progression toutes les 50 lignes
        if(millis() - lastPrint > 1000) {
            Serial.printf("Progress: %d/%d lines (%d%%)\n", 
                         linesCaptured, _height, 
                         (linesCaptured * 100) / _height);
            lastPrint = millis();
        }
    }
    
    // Vider les données restantes
    flushBuffer(f);
    f.close();
    
    unsigned long endTime = millis();
    unsigned long duration = endTime - startTime;
    
    Serial.println("\n=== Capture Summary ===");
    Serial.printf("Lines captured: %d/%d\n", linesCaptured, _height);
    Serial.printf("Total time: %lu ms\n", duration);
    Serial.printf("Data written: %lu bytes\n", (unsigned long)linesCaptured * _width * 2);
    if(linesCaptured > 0) {
        Serial.printf("Average line time: %.2f ms\n", (float)duration / linesCaptured);
    }
}

#endif