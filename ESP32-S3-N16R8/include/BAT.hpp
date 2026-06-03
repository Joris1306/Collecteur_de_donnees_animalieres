#ifndef __BAT_HPP__
#define __BAT_HPP__

#include <Arduino.h>
#include <stdio.h>
#include "esp_adc_cal.h"

#define VOLTAGE 3.3          // Référence ADC
#define RESOLUTION 12        // 12-bit
#define ADC_MAX 4095.0
#define VOLTAGE_DIVIDER 2.0  // 1.0 = pas de diviseur, 2.0 = diviseur 1:1, etc.
#define VOLTAGE_MAX_BATT 4.2
#define VOLTAGE_MIN_BATT 3.0

class BAT
{
    private:
        unsigned int _pin;
        esp_adc_cal_characteristics_t* adc_chars;
        
    public:
        BAT(unsigned int pin);
        ~BAT();
        float ReadVoltage();
        float ReadPercent();
};

BAT::BAT(unsigned int pin)
{
    this->_pin = pin;
    
    pinMode(this->_pin, INPUT);
    analogReadResolution(RESOLUTION);
    
    // Caractéristiques ADC pour compensation
    adc_chars = (esp_adc_cal_characteristics_t*)calloc(1, sizeof(esp_adc_cal_characteristics_t));
    esp_adc_cal_characterize(ADC_UNIT_1, ADC_ATTEN_DB_11, ADC_WIDTH_BIT_12, 1100, adc_chars);
}

BAT::~BAT()
{
    if (adc_chars) free(adc_chars);
}

float BAT::ReadVoltage()
{
    // Faire 5 lectures et calculer la moyenne
    uint32_t sum = 0;
    int samples = 5;
    
    for (int i = 0; i < samples; i++)
    {
        sum += analogRead(this->_pin);
        delay(5);
    }
    
    uint32_t adc_reading = sum / samples;
    
    // Convertir avec compensation ADC
    uint32_t voltage_mv = esp_adc_cal_raw_to_voltage(adc_reading, adc_chars);
    float voltage = (voltage_mv / 1000.0) * VOLTAGE_DIVIDER;
    
    return voltage;
}

float BAT::ReadPercent()
{
    float voltage = ReadVoltage();

    if(voltage > VOLTAGE_MAX_BATT) 
    {
        return 100;
    }
    else if(voltage < VOLTAGE_MIN_BATT) 
    {
        return 0;
    }
    else
    {
        return ((voltage - VOLTAGE_MIN_BATT) / (VOLTAGE_MAX_BATT - VOLTAGE_MIN_BATT)) * 100.0;
    }
}

#endif