import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image

CONFIANCE = 0.5

class AI_CLASSIFICATION:

    

    @staticmethod
    def get_animal_name(image_path):
        model = YOLO("yolov8n.pt")
        image = Image.open(image_path)
        results = model(image)

        animal_name = "Pas identifié ou Faux positif"

        for r in results:
            for box in r.boxes:
                conf = float(box.conf)
                cls_id = int(box.cls)
                label = model.names[cls_id]

                if conf >= CONFIANCE:  # Seuil de confiance
                    if model.names[int(box.cls)] not in ["person"]:
                        continue
                    animal_name = label

                    #animal_name = ""
                    #animal_name = animal_name + " " + label

        return animal_name


    @staticmethod
    def get_image_traitee(image_path):
        model = YOLO("yolov8n.pt")
        image = Image.open(image_path)
        results = model(image)

        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        for r in results:
            for box in r.boxes:

                # filtrage des détections (que HUMAIN pour l'instant)
                if box.conf < CONFIANCE:
                    continue
                if model.names[int(box.cls)] not in ["person"]:
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

        return img
    


    @staticmethod
    def get_etat(image_path):
        model = YOLO("yolov8n.pt")
        image = Image.open(image_path)
        results = model(image)

        etat = 0

        for r in results:
            for box in r.boxes:
                conf = float(box.conf)
                cls_id = int(box.cls)
                label = model.names[cls_id]

                if conf >= CONFIANCE:  # Seuil de confiance
                    if label == "person":
                        return 2

        return etat
    





# model = YOLO("yolov8n.pt")

# image = Image.open("images_ia/Wolf2.jpg")
# results = model(image)

# img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

# for r in results:
#     for box in r.boxes:
#         x1, y1, x2, y2 = map(int, box.xyxy[0])
#         conf = float(box.conf)
#         cls_id = int(box.cls)
#         label = model.names[cls_id]

#         # cadre sur la photo
#         cv2.rectangle(img, (x1,y1), (x2,y2), (0, 0, 255), 2)#Pour régler couleur

#         # texte sur la photo
#         text = f"{label} {conf*100:.1f}%"
#         cv2.putText(
#             img, text,
#             (x1, y1-10),
#             cv2.FONT_HERSHEY_SIMPLEX,
#             0.7,
#             (0, 0, 255),#Pour régler couleur
#             2
#         )

# cv2.imwrite("result.jpg", img)
