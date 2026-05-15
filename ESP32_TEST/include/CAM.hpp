#ifndef CAM_HPP
#define CAM_HPP

#include <Arduino.h>
#include "esp_camera.h"
#include "SD.h"
#include "SPI.h"
#include "CONFIG.h"

class CAM {
private:
    int _pictureCount;

public:
    CAM() : _pictureCount(0) {}

    /**
     * Initialise le capteur avec les réglages optimisés trouvés
     */
    bool begin() {
        camera_config_t config;
        config.ledc_channel = LEDC_CHANNEL_0;
        config.ledc_timer = LEDC_TIMER_0;
        config.pin_d0 = D0_GPIO;
        config.pin_d1 = D1_GPIO;
        config.pin_d2 = D2_GPIO;
        config.pin_d3 = D3_GPIO;
        config.pin_d4 = D4_GPIO;
        config.pin_d5 = D5_GPIO;
        config.pin_d6 = D6_GPIO;
        config.pin_d7 = D7_GPIO;
        config.pin_xclk = XCLK_GPIO;
        config.pin_pclk = PCLK_GPIO;
        config.pin_vsync = VSYNC_GPIO;
        config.pin_href = HREF_GPIO;
        config.pin_sccb_sda = SIOD_GPIO_NUM;
        config.pin_sccb_scl = SIOC_GPIO_NUM;
        config.pin_pwdn = -1;
        config.pin_reset = -1;
        config.xclk_freq_hz = 12000000; 
        config.pixel_format = PIXFORMAT_JPEG;

        // On garde ta configuration limite optimisée
        if (psramFound()) {
            config.frame_size = FRAMESIZE_VGA;
            config.jpeg_quality = 12;
            config.fb_count = 2;
            config.fb_location = CAMERA_FB_IN_PSRAM;
        } else {
            config.frame_size = FRAMESIZE_QVGA; // 800x600
            config.jpeg_quality = 8;           // Ton réglage limite
            config.fb_count = 1;
            config.fb_location = CAMERA_FB_IN_DRAM;
        }

        esp_err_t err = esp_camera_init(&config);
        if (err != ESP_OK) {
            Serial.printf("Erreur Init Caméra: 0x%x\n", err);
            return false;
        }

        // Réglages capteur par défaut pour améliorer l'image
        sensor_t * s = esp_camera_sensor_get();
        s->set_brightness(s, 0); 
        s->set_contrast(s, 0);
        return true;
    }

    /**
     * Prend une photo et la sauvegarde sur la SD
     */
    bool takeAndSavePhoto(String filename) {
        Serial.println("Capture en cours...");

        // 1. Vidage du buffer pour garantir une image fraîche
        camera_fb_t * fb = esp_camera_fb_get();
        if (fb) {
            esp_camera_fb_return(fb);
            delay(100);
        }

        // 2. Capture réelle
        fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("ERREUR : Impossible de récupérer le framebuffer (DMA)");
            return false;
        }

        // 3. Écriture sur SD
        //String path = "/pic" + String(_pictureCount++) + ".jpg";
        File file = SD.open(filename, FILE_WRITE);
        
        if (!file) {
            Serial.println("ERREUR : Impossible d'ouvrir le fichier sur SD");
            esp_camera_fb_return(fb);
            return false;
        }

        size_t written = file.write(fb->buf, fb->len);
        file.close();
        
        Serial.printf("Photo sauvegardée: %s (%u bytes)\n", filename, written);

        esp_camera_fb_return(fb);
        return (written == fb->len);
    }
};

#endif