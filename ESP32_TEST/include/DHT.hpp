#ifndef __DHT_HPP__
#define __DHT_HPP__

#include <Arduino.h>

#define DHT11 11
#define DHT22 22

class DHT {
public:
    DHT(uint8_t pin, uint8_t type)
        : _pin(pin), _type(type), _lastRead(0),
          _temperature(NAN), _humidity(NAN) {}

    void begin() {
        pinMode(_pin, INPUT_PULLUP);
    }

    bool read() {
        // Respect du temps minimum entre lectures
        unsigned long now = millis();
        if (now - _lastRead < 2000) {
            return !isnan(_temperature) && !isnan(_humidity);
        }
        _lastRead = now;

        uint8_t data[5] = {0};

        // Signal de départ
        pinMode(_pin, OUTPUT);
        digitalWrite(_pin, LOW);
        delay(_type == DHT11 ? 18 : 1);
        digitalWrite(_pin, HIGH);
        delayMicroseconds(40);
        pinMode(_pin, INPUT_PULLUP);

        // Réponse du capteur
        if (!expectPulse(LOW)) return false;
        if (!expectPulse(HIGH)) return false;

        // Lecture des 40 bits
        for (uint8_t i = 0; i < 40; i++) {
            if (!expectPulse(LOW)) return false;
            uint32_t highTime = expectPulse(HIGH);
            if (highTime == 0) return false;

            data[i / 8] <<= 1;
            if (highTime > 40) data[i / 8] |= 1;
        }

        // Checksum
        if (((data[0] + data[1] + data[2] + data[3]) & 0xFF) != data[4]) {
            return false;
        }

        // Conversion
        if (_type == DHT11) {
            _humidity = data[0];
            _temperature = data[2];
        } else { // DHT22
            _humidity = ((data[0] << 8) | data[1]) * 0.1;
            int16_t t = (data[2] << 8) | data[3];
            if (t & 0x8000) t = -(t & 0x7FFF);
            _temperature = t * 0.1;
        }

        return true;
    }

    float temperature() const { return _temperature; }
    float humidity() const { return _humidity; }

private:
    uint8_t _pin;
    uint8_t _type;
    unsigned long _lastRead;
    float _temperature;
    float _humidity;

    uint32_t expectPulse(bool level) {
        uint32_t count = 0;
        while (digitalRead(_pin) == level) {
            if (++count >= 1000) return 0;
            delayMicroseconds(1);
        }
        return count;
    }
};

#endif
