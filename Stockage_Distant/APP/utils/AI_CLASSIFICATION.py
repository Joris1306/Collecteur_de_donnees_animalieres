
import cv2
import numpy as np
from speciesnet import DEFAULT_MODEL
from speciesnet import SpeciesNet
from speciesnet import draw_bboxes
from speciesnet import load_rgb_image


class AI_CLASSIFICATION:

    @staticmethod
    def get_parameters(image_path: str) -> tuple[list[dict[str, str]], dict[str, str]]:
        """classification ia

        Args:
            image_path (str): chemin de l'image a traité

        Returns:
            tuple[list[dict[str, str]], dict[str, str]]: _description_
            - arg1 : list[dict[str, str]]: liste des 'objets' détectés avec leurs paramètres
                - arg1[i] : dict[str, str] : dictionnaire des paramètres de l'objet i (quelconque)
                - clé :
                    - 'NOM_ANIMAL' : str : nom de l'animal détecté
                    - 'CONFIANCE' : str : confiance de la détection de l'animal
            - arg2 : dict[str, str]: dictionnaire des paramètres globaux de l'image
                - clé :
                    - 'ETAT' : str : état global (0: ok, 1: flou, 2: humain)
                    - 'IMAGE_TRAITEE' : str : image traitée (numpy array)
        """
        try:
            model = SpeciesNet(DEFAULT_MODEL)


            image = load_rgb_image(image_path)
            if image is None:
                raise ValueError(f"Impossible de charger l'image: {image_path}")

            predictions = model.predict(
                instances_dict={
                    "instances": [
                        {
                            "filepath": image_path,
                        }
                    ]
                }
            )

            prediction_item = None
            if predictions and "predictions" in predictions and predictions["predictions"]:
                prediction_item = predictions["predictions"][0]

            detections = []
            if prediction_item:
                detections = prediction_item.get("detections", [])

            detected_objects = []
            if prediction_item and "prediction" in prediction_item:
                raw_animal_name = prediction_item.get("prediction", "")
                animal_label = raw_animal_name.split(";")[-1].strip() if raw_animal_name else ""
                detected_objects.append(
                    {
                        "NOM_ANIMAL": animal_label,
                        "CONFIANCE": f"{float(prediction_item.get('prediction_score', 0.0)):.2f}",
                    }
                )

            etat = 0

            img_with_boxes = image
            if detections:
                img_with_boxes = draw_bboxes(image, detections)

            img_rgb = np.array(img_with_boxes.convert("RGB"))
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < 100:
                etat = 1

            if any(det.get("label") == "human" for det in detections):
                etat = 2


            global_params = {
                'ETAT': str(etat),
                'IMAGE_TRAITEE': rel_traitee_path  # Return relative path, not absolute
            }

            return detected_objects, global_params

        except Exception as e:
            print(f"Error in get_parameters: {e}")
            return [], {}


if __name__ == "__main__":

        # Test avec une image du dossier SAMPLE
        test_image_path = "images_ia/humain_3.png"  # À remplacer par un chemin d'image valide

        print(f"Chemin d'image teste: {test_image_path}")
        print("-" * 60)

        # Exécuter la classification
        detected_objects, global_params = AI_CLASSIFICATION_ALT.get_parameters(test_image_path)

        # Afficher les résultats
        print(f"Objets detectes: {len(detected_objects)}")
        print()

        for i, obj in enumerate(detected_objects):
            print(f"Objet {i+1}:")
            for key, value in obj.items():
                print(f"  {key}: {value}")
            print()

        print("Parametres globaux:")
        for key, value in global_params.items():
            if key == 'IMAGE_TRAITEE':
                # Save the processed image
                output_path = "processed_image_speciesnet.jpg"
                cv2.imwrite(output_path, value)
                print(f"  {key}: Image numpy array (shape: {value.shape if hasattr(value, 'shape') else 'N/A'})")
                print(f"  [OK] Image sauvegardee: {output_path}")
            else:
                print(f"  {key}: {value}")

