#ifndef __CONFIG_H__
#define __CONFIG_H__

// Activer / désactiver Débogage série
#define DEBUG_SD           true

// Macro pour débogage
#define DEBUG_PRINT(msg) if(DEBUG_SD) { Serial.println(msg); }

// Pin pour alimentation et réveil
#define WAKE_UP           1
#define PWR_U_D           2
#define LED_IR            45

// Niveau de batterie
#define BAT_PIN           14

// DHT22 sensor
#define DHT_PIN           38

// Brightness sensor
#define LDR_PIN           -1 // Not Use

// UART3 - Commincation
#define WPBIS_RXD_2       41
#define WPBIS_TXD_2       42

// UART2 - GPS
#define GPS_PWR_UD        21
#define GPS_RX_PIN        18
#define GPS_TX_PIN        17

// CARTE SD 
#define SD_SCK            13
#define SD_MISO           12
#define SD_MOSI           11
#define SD_CS             10

// CAMERA PINS
#define SIOD_GPIO_NUM     8 // SDA
#define SIOC_GPIO_NUM     9 // SCL
#define D0_GPIO           47
#define D1_GPIO           3
#define D2_GPIO           16
#define D3_GPIO           15
#define D4_GPIO           7
#define D5_GPIO           6
#define D6_GPIO           5
#define D7_GPIO           4
#define VSYNC_GPIO        40
#define HREF_GPIO         39
#define PCLK_GPIO         46
#define RST_GPIO          -1 // Connect to GND
#define XCLK_GPIO         -1 // Not Use  


#endif // __CONFIG_H__