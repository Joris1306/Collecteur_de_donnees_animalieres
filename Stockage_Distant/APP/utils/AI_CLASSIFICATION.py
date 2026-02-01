import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image
import sys
import os

# Add parent directory to path so this script can be run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utlitaires import BASE_PATH


class AI_CLASSIFICATION:
    CONFIANCE = 0.3
    MODEL_PATH = os.path.join(BASE_PATH,'utils',"yolov8n.pt")
    IMAGE_DIR = os.path.join(BASE_PATH,'static')
    _MODEL = None
    _TARGET_LABELS = {"person"}

    @staticmethod
    def _get_model():
        if AI_CLASSIFICATION._MODEL is None:
            AI_CLASSIFICATION._MODEL = YOLO(AI_CLASSIFICATION.MODEL_PATH)
        return AI_CLASSIFICATION._MODEL

    @staticmethod
    def _open_image(image_path):
        return Image.open(os.path.join(AI_CLASSIFICATION.IMAGE_DIR, image_path))

    @staticmethod
    def get_animal_name(image_path):
        model = AI_CLASSIFICATION._get_model()
        image = AI_CLASSIFICATION._open_image(image_path)
        results = model(image)

        animal_name = "Pas identifié ou Faux positif"

        for r in results:
            for box in r.boxes:
                conf = float(box.conf)
                cls_id = int(box.cls)
                label = model.names[cls_id]

                if conf >= AI_CLASSIFICATION.CONFIANCE:  # Seuil de confiance
                    if model.names[int(box.cls)] not in AI_CLASSIFICATION._TARGET_LABELS:
                        continue
                    animal_name = label

                    #animal_name = ""
                    #animal_name = animal_name + " " + label

        return animal_name


    @staticmethod
    def get_image_traitee(image_path):
        model = AI_CLASSIFICATION._get_model()
        image = AI_CLASSIFICATION._open_image(image_path)
        results = model(image)

        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        for r in results:
            for box in r.boxes:

                # filtrage des détections (que HUMAIN pour l'instant)
                if box.conf < AI_CLASSIFICATION.CONFIANCE:
                    continue
                if model.names[int(box.cls)] not in AI_CLASSIFICATION._TARGET_LABELS:
                    continue

                #variables par les fonctions de yolo
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf)
                cls_id = int(box.cls)
                label = model.names[cls_id]

                # cadre sur la photo
                cv2.rectangle(img, (x1,y1), (x2,y2), (0, 0, 255), 2)#Pour régler couleur

                # texte sur la photo
                text = f"{label} {conf*100:.1f}%"
                cv2.putText(
                    img, text,
                    (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),#Pour régler couleur
                    2
                )

        image_dir = os.path.dirname(image_path)
        image_name = os.path.basename(image_path)
        rel_traitee_path = os.path.join(image_dir, f"traitee_{image_name}")
        img_traitee_path = os.path.join(AI_CLASSIFICATION.IMAGE_DIR, rel_traitee_path)
        os.makedirs(os.path.dirname(img_traitee_path), exist_ok=True)
        cv2.imwrite(img_traitee_path, img)

        return rel_traitee_path

    @staticmethod
    def get_etat(image_path):
        model = AI_CLASSIFICATION._get_model()
        image = AI_CLASSIFICATION._open_image(image_path)
        results = model(image)

        etat = 0

        for r in results:
            for box in r.boxes:
                conf = float(box.conf)
                label = model.names[int(box.cls)]

                if conf >= AI_CLASSIFICATION.CONFIANCE and label in AI_CLASSIFICATION._TARGET_LABELS:
                    return 2

        return etat
    
    @staticmethod
    def get_confiance_animal(image_path):
        model = YOLO(AI_CLASSIFICATION.MODEL_PATH)
        image = Image.open(image_path)
        results = model(image)

        conf_animal = 0.0

        for r in results:
            for box in r.boxes:
                conf = float(box.conf)
                cls_id = int(box.cls)
                label = model.names[cls_id]

                if conf >= AI_CLASSIFICATION.CONFIANCE:  # Seuil de confiance
                    if model.names[int(box.cls)] not in ["person"]:
                        continue
                    conf_animal = conf 

        return conf_animal

    @staticmethod
    def get_parameters(image_path):
        pass

def main():
    image_path = os.path.join(BASE_PATH, 'static',"images/2026-01-30_11-11-31.png")

    image_traitee = AI_CLASSIFICATION.get_image_traitee(image_path)

    Image.open(image_traitee).show()

if __name__ == "__main__":
    main()
    