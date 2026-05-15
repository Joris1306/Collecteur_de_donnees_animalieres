#ifndef __LDR_HPP__
#define __LDR_HPP__

#include <Arduino.h>

#define RESISTOR_BRIDGE 1500

class LDR
{
    private:
        unsigned int _ldrpin;
        float _voltageValue;
        unsigned int _resistorValue;
        unsigned int _luxValue;

    public:
        LDR(int ldrpin);
        float GetVoltageValue();
        unsigned int  GetResistorValue();
        unsigned int  GetLuxValue();
};

LDR::LDR(int ldrpin)
{
    pinMode(ldrpin, INPUT);
    analogReadResolution(12);

    _ldrpin = ldrpin;
    _voltageValue = 0;
    _resistorValue = 0;
    _luxValue = 0;
}

float LDR::GetVoltageValue()
{
    /*
    int sum = 0;

    for(int i = 0; i < 10; i++) 
    {
        sum += analogRead(_ldrpin);
    }

    _voltageValue = (sum * 3.3) / (10.0 * 4095.0);
    */
    _voltageValue = (analogRead(_ldrpin) * 3.3) / (1.0 * 4095.0);
    return _voltageValue;
}

unsigned int LDR::GetResistorValue()
{
    LDR::GetVoltageValue();
    
    if(_voltageValue < 0.01) 
    {
        _resistorValue = 1000000; // Valeur max 
    } 
    else 
    {
        _resistorValue = (( RESISTOR_BRIDGE * 3.3 ) / _voltageValue ) - RESISTOR_BRIDGE;
    }
    
    return _resistorValue;
}


unsigned int LDR::GetLuxValue()
{
    LDR::GetResistorValue();
    
    float resistanceKOhms = _resistorValue / 1000.0; // Conversion en kohms
    
    if (resistanceKOhms <= 0.1) 
    {
        resistanceKOhms = 0.1; // Limite inférieure
    }
    if (resistanceKOhms >= 1000) 
    {
        resistanceKOhms = 1000; // Limite supérieure
    }
    
    // Formule 
    _luxValue = pow(1000.0 / resistanceKOhms, 1.4);
    
    if (_luxValue < 1) _luxValue = 1;
    if (_luxValue > 10000) _luxValue = 10000;
    
    return (unsigned int)_luxValue;
}

#endif