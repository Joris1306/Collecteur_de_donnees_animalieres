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
    def get_parameters(image_path: str) -> tuple[list[dict[str, str]], dict[str, str]]:
        """classification ia

        Args:
            image_path (str): chemin de l'image a traité (l'objet image peut être appelé : AI_CLASSIFICATION._open_image(image_path))

        Returns:
            tuple[list[dict[str, str]], dict[str, str]]: _description_
            - arg1 : list[dict[str, str]]: liste des 'objets' détectés avec leurs paramètres
                - arg1[i] : dict[str, str] : dictionnaire des paramètres de l'objet i (quelconque)
                - clé :
                    - 'ETAT' : str : état de la classification de l'animal
                    - 'NOM_ANIMAL' : str : nom de l'animal détecté
                    - 'CONFIANCE' : str : confiance de la détection de l'animal
            - arg2 : dict[str, str]: dictionnaire des paramètres globaux de l'image
                - clé :
                    - 'IMAGE_TRAITEE' : str : chemin de l'image traitée (avec les cadres et textes) 
        """
        try:
            # Load model and image once
            model = AI_CLASSIFICATION._get_model()
            image = AI_CLASSIFICATION._open_image(image_path)
            results = model(image)

            # Initialize result structures
            detected_objects = []
            etat = 0  # Default: No problem
            
            # Convert image for OpenCV processing
            img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Check if image is too blurry using Laplacian variance
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # If laplacian variance is low, image is too blurry (ETAT = 1)
            if laplacian_var < 50  :  # Threshold for blur detection
                etat = 1
            
            # Process each detection
            for r in results:
                for box in r.boxes:
                    conf = float(box.conf)
                    cls_id = int(box.cls)
                    label = model.names[cls_id]

                    # Filter by confidence threshold and only process persons
                    if conf >= AI_CLASSIFICATION.CONFIANCE and label == "person":
                        etat = 2  # There is a human (overrides blur detection)
                        
                        # Add detection to list (without ETAT, it's now global)
                        obj_params = {
                            'NOM_ANIMAL': label,
                            'CONFIANCE': f"{conf:.2f}"
                        }
                        detected_objects.append(obj_params)
                        
                        # Draw bounding box on image
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        
                        # Optional: Add text on image (currently commented out)
                        # text = f"{label} {conf*100:.1f}%"
                        # cv2.putText(
                        #     img, text,
                        #     (x1, y1-10),
                        #     cv2.FONT_HERSHEY_SIMPLEX,
                        #     0.7,
                        #     (0, 0, 255),
                        #     2
                        # )
            
            # Global parameters
            global_params = {
                'ETAT': str(etat),
                'IMAGE_TRAITEE': img
            }
            
            return detected_objects, global_params
            
        except Exception as e:
            print(f"Error in get_parameters: {e}")
            return [], {}


if __name__ == "__main__":
    # Test avec une image du dossier SAMPLE
    test_image_path = "images_ia/test_ourcamera2.png"  # À remplacer par un chemin d'image valide
    
    # Exécuter la classification
    detected_objects, global_params = AI_CLASSIFICATION.get_parameters(test_image_path)
    
    # Afficher les résultats
    print(f"Objets détectés: {len(detected_objects)}")
    print()
    
    for i, obj in enumerate(detected_objects):
        print(f"Objet {i+1}:")
        for key, value in obj.items():
            print(f"  {key}: {value}")
        print()
    
    print("Paramètres globaux:")
    for key, value in global_params.items():
        if key == 'IMAGE_TRAITEE':
            # Save the processed image
            output_path = "processed_image.jpg"
            cv2.imwrite(output_path, value)
            print(f"  {key}: Image numpy array (shape: {value.shape if hasattr(value, 'shape') else 'N/A'})")
            print(f"  ✓ Image sauvegardée: {output_path}")
        else:
            print(f"  {key}: {value}")
