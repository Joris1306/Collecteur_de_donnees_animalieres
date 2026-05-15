#ifndef __CONFIG_H__
#define __CONFIG_H__

#define WAKE_UP           4
#define PWR_U_D           2

// Niveau de batterie
#define BAT_PIN           36

// DHT22 sensor
#define DHT_PIN           5

// Brightness sensor
#define LDR_PIN           -1 // Not Use

// UART2 - GPS
#define GPS_RX_PIN        16
#define GPS_TX_PIN        17

// CARTE SD 
#define SD_SCK            14
#define SD_MISO           12
#define SD_MOSI           13
#define SD_CS             15

// CAMERA PINS
#define SIOD_GPIO_NUM     21
#define SIOC_GPIO_NUM     22
#define D0_GPIO           26
#define D1_GPIO           33
#define D2_GPIO           39
#define D3_GPIO           32
#define D4_GPIO           27
#define D5_GPIO           23
#define D6_GPIO           19
#define D7_GPIO           18
#define VSYNC_GPIO        34
#define HREF_GPIO         25
#define PCLK_GPIO         35
#define XCLK_GPIO         -1 // Not Use  


#endif // __CONFIG_H__