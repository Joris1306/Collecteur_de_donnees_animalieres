#ifndef __RTC_HPP__
#define __RTC_HPP__

#include <Arduino.h>
#include <time.h>
#include <sys/time.h>

RTC_DATA_ATTR char rtcLatitude[16] = "";
RTC_DATA_ATTR char rtcLongitude[16] = "";

class RTC
{
private :
    String _hours;
    String _minutes;
    String _seconds;
    String _day;
    String _month;
    String _year;

public:
    RTC() 
    {
        //configTime(0, 0, "pool.ntp.org");
    }  

    String getHours()  { return _hours; }
    String getMinutes(){ return _minutes; }
    String getSeconds(){ return _seconds; }
    String getDay()    { return _day; }
    String getMonth()  { return _month; }
    String getYear()   { return _year; }
    String getLat() { return String(rtcLatitude); }
    String getLon() { return String(rtcLongitude); }


    String getDateTime()
    {
        struct tm timeinfo;
        if (!getLocalTime(&timeinfo)) return String("Erreur temps");

        char buffer[25];
        strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", &timeinfo);

        _hours = String(timeinfo.tm_hour);
        _minutes = String(timeinfo.tm_min);
        _seconds = String(timeinfo.tm_sec);
        _day = String(timeinfo.tm_mday);
        _month = String(timeinfo.tm_mon + 1);
        _year = String(timeinfo.tm_year + 1900);

        return String(buffer);
    }

    void updateFromGPS(String Lat, String lon, String hours, String minutes, String seconds, String day, String month, String year)
    {
        if (hours == "" || day == "" || month == "" || year == "") return;

        struct tm timeinfo;
        memset(&timeinfo, 0, sizeof(struct tm));
        
        Lat.toCharArray(rtcLatitude, sizeof(rtcLatitude));
        lon.toCharArray(rtcLongitude, sizeof(rtcLongitude));

        timeinfo.tm_hour = hours.toInt();
        timeinfo.tm_min  = minutes.toInt();
        timeinfo.tm_sec  = seconds.toInt();

        timeinfo.tm_mday = day.toInt();
        timeinfo.tm_mon  = month.toInt() - 1;  // tm_mon = 0–11
        timeinfo.tm_year = year.toInt() - 1900; // année complète

        time_t t = mktime(&timeinfo);

        struct timeval now = { .tv_sec = t, .tv_usec = 0 };
        settimeofday(&now, nullptr);

    }


};

#endif
