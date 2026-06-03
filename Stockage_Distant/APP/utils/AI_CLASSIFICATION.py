import os
import sys
import logging
import warnings
import datetime

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_PATH = os.path.join(APP_ROOT, "SAMPLE")
STATIC_PATH = os.path.join(APP_ROOT, "static")
PROCESSED_IMAGE_DIR = os.path.join(STATIC_PATH, "images_ia")
YOLO_DEFAULT_MODEL = os.path.join(APP_ROOT, "utils", "yolov8n.pt")

if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

try:
    from utils.ai_settings import get_ai_settings
except ModuleNotFoundError:
    from ai_settings import get_ai_settings

logger = logging.getLogger(__name__)

# SpeciesNet can import YOLOv5 which still uses pkg_resources internally.
# Filter only this known deprecation warning to keep logs clean.
warnings.filterwarnings(
    "ignore",
    message=r"pkg_resources is deprecated as an API.*",
    category=UserWarning,
    module=r"yolov5\.utils\.general",
)

try:
    from speciesnet import DEFAULT_MODEL
    from speciesnet import SpeciesNet
    from speciesnet import draw_bboxes
    from speciesnet import load_rgb_image
    SPECIESNET_AVAILABLE = True
    SPECIESNET_IMPORT_ERROR = None
except ModuleNotFoundError:
    # Allow the rest of the application to run even when speciesnet is not installed.
    DEFAULT_MODEL = None
    SpeciesNet = None
    draw_bboxes = None
    load_rgb_image = None
    SPECIESNET_AVAILABLE = False
    SPECIESNET_IMPORT_ERROR = "speciesnet module is not installed in the active Python environment"


class AI_CLASSIFICATION:
    _speciesnet_unavailable_warned = False

    @staticmethod
    def _confidence_to_percent(conf_value) -> str:
        try:
            value = float(conf_value)
        except Exception:
            value = 0.0

        # Most model scores are in [0,1]. If already in [0,100], keep as-is.
        if value <= 1.0:
            value *= 100.0

        value = max(0.0, min(100.0, value))
        return str(int(round(value)))

    @staticmethod
    def _save_processed_image(image, source_path: str) -> str:
        src_dir = os.path.dirname(source_path)
        src_base = os.path.basename(source_path)
        src_name, src_ext = os.path.splitext(src_base)

        if not src_name:
            src_name = "image"

        if not src_ext:
            src_ext = ".jpg"

        ext_lower = src_ext.lower()
        format_map = {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
            ".webp": "WEBP",
            ".bmp": "BMP",
            ".tif": "TIFF",
            ".tiff": "TIFF",
        }
        save_format = format_map.get(ext_lower, "JPEG")

        out_name = f"traitee_{src_name}{src_ext}"
        out_abs_path = os.path.join(src_dir, out_name)

        image_to_save = image
        if save_format == "JPEG" and getattr(image, "mode", None) in ("RGBA", "LA", "P"):
            image_to_save = image.convert("RGB")

        image_to_save.save(out_abs_path, format=save_format)

        # Return path relative to /static for Flask templates/DB consistency.
        static_prefix = STATIC_PATH + os.sep
        if out_abs_path.startswith(static_prefix):
            return out_abs_path[len(static_prefix):].replace(os.sep, "/")
        return out_abs_path

    @staticmethod
    def _resolve_image_path(image_path: str) -> str:
        """Resolve a web-style relative image path to an existing file on disk."""
        if not image_path:
            return image_path

        if os.path.isabs(image_path) and os.path.exists(image_path):
            return image_path

        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(app_root, image_path),
            os.path.join(app_root, 'static', image_path),
            os.path.join(app_root, 'static', 'images', os.path.basename(image_path)),
        ]

        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate

        return image_path

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
            resolved_image_path = AI_CLASSIFICATION._resolve_image_path(image_path)
            settings = get_ai_settings()
            active_model = settings.get("active_model", "speciesnet-default")

            if active_model == "disabled":
                return [], {"ETAT": "0", "IMAGE_TRAITEE": image_path}

            try:
                import cv2  # type: ignore
                import numpy as np  # type: ignore
            except ModuleNotFoundError as dep_err:
                logger.error("AI classification unavailable: missing dependency: %s", dep_err)
                return [], {"ETAT": "0"}

            etat = 0
            detected_objects = []
            human_labels = []
            img_with_boxes = None

            if active_model.startswith("speciesnet"):
                if (
                    not SPECIESNET_AVAILABLE
                    or SpeciesNet is None
                    or DEFAULT_MODEL is None
                    or load_rgb_image is None
                    or draw_bboxes is None
                ):
                    if not AI_CLASSIFICATION._speciesnet_unavailable_warned:
                        logger.warning(
                            "AI classification disabled: %s",
                            SPECIESNET_IMPORT_ERROR or "SpeciesNet dependency unavailable",
                        )
                        AI_CLASSIFICATION._speciesnet_unavailable_warned = True
                    return [], {"ETAT": "0", "IMAGE_TRAITEE": image_path}

                model_path = DEFAULT_MODEL
                if active_model == "speciesnet-custom":
                    custom_model_path = settings.get("custom_model_path", "").strip()
                    if custom_model_path and (
                        custom_model_path.startswith("kaggle:")
                        or os.path.exists(custom_model_path)
                    ):
                        model_path = custom_model_path
                    else:
                        logger.warning(
                            "AI model configured as speciesnet-custom but path is missing or invalid: %s",
                            custom_model_path,
                        )

                model = SpeciesNet(model_path)
                image = load_rgb_image(resolved_image_path)
                if image is None:
                    raise ValueError(f"Impossible de charger l'image: {resolved_image_path}")

                predictions = model.predict(
                    instances_dict={
                        "instances": [
                            {
                                "filepath": resolved_image_path,
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

                if detections:
                    for det in detections:
                        label = str(det.get("label", "")).strip()
                        if not label:
                            continue

                        conf_raw = det.get("conf", det.get("confidence", 0.0))
                        try:
                            conf_value = float(conf_raw)
                        except Exception:
                            conf_value = 0.0

                        detected_objects.append(
                            {
                                "NOM_ANIMAL": label,
                                "CONFIANCE": AI_CLASSIFICATION._confidence_to_percent(conf_value),
                            }
                        )
                elif prediction_item and "prediction" in prediction_item:
                    raw_animal_name = prediction_item.get("prediction", "")
                    animal_label = raw_animal_name.split(";")[-1].strip() if raw_animal_name else ""
                    if animal_label:
                        detected_objects.append(
                            {
                                "NOM_ANIMAL": animal_label,
                                "CONFIANCE": AI_CLASSIFICATION._confidence_to_percent(
                                    prediction_item.get("prediction_score", 0.0)
                                ),
                            }
                        )

                img_with_boxes = image
                if detections:
                    img_with_boxes = draw_bboxes(image, detections)

                human_labels = [str(det.get("label", "")).lower() for det in detections]

            elif active_model.startswith("yolo"):
                try:
                    from ultralytics import YOLO  # type: ignore
                    from PIL import Image  # type: ignore
                except ModuleNotFoundError as dep_err:
                    logger.error("YOLO classification unavailable: missing dependency: %s", dep_err)
                    return [], {"ETAT": "0", "IMAGE_TRAITEE": image_path}

                model_path = YOLO_DEFAULT_MODEL if os.path.exists(YOLO_DEFAULT_MODEL) else "yolov8n.pt"
                if active_model == "yolo-custom":
                    custom_model_path = settings.get("custom_model_path", "").strip()
                    if custom_model_path and os.path.exists(custom_model_path):
                        model_path = custom_model_path
                    else:
                        logger.warning(
                            "AI model configured as yolo-custom but path is missing or invalid: %s",
                            custom_model_path,
                        )

                model = YOLO(model_path)
                results = model.predict(source=resolved_image_path, verbose=False)
                if not results:
                    return [], {"ETAT": "0", "IMAGE_TRAITEE": image_path}

                result = results[0]
                names = result.names or {}
                boxes = result.boxes

                if boxes is not None:
                    for box in boxes:
                        cls_id = int(box.cls.item())
                        conf_value = float(box.conf.item())
                        label = str(names.get(cls_id, cls_id))
                        detected_objects.append(
                            {
                                "NOM_ANIMAL": label,
                                "CONFIANCE": AI_CLASSIFICATION._confidence_to_percent(conf_value),
                            }
                        )
                        human_labels.append(label.lower())

                plotted = result.plot()
                img_with_boxes = Image.fromarray(plotted[:, :, ::-1])

            else:
                logger.warning("Unknown AI model configuration: %s", active_model)
                return [], {"ETAT": "0", "IMAGE_TRAITEE": image_path}

            if img_with_boxes is None:
                return [], {"ETAT": "0", "IMAGE_TRAITEE": image_path}

            processed_image_rel_path = AI_CLASSIFICATION._save_processed_image(
                img_with_boxes,
                resolved_image_path,
            )

            img_rgb = np.array(img_with_boxes.convert("RGB"))
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < 100:
                etat = 1

            if any(lbl in ("human", "person") for lbl in human_labels):
                etat = 2


            global_params = {
                'ETAT': str(etat),
                'IMAGE_TRAITEE': processed_image_rel_path
            }

            return detected_objects, global_params

        except Exception as e:
            logger.error("Error in get_parameters: %s", e)
            return [], {}


if __name__ == "__main__":

        # Test avec une image du dossier SAMPLE
        # test_image_path = os.path.join(SAMPLE_PATH, "pic5.webp") # À remplacer par un chemin d'image valide
        test_image_path = os.path.join(APP_ROOT, "utils","images_ia","zebra.jpg")

        print(f"Chemin d'image teste: {test_image_path}")
        print("-" * 60)

        # Exécuter la classification
        detected_objects, global_params = AI_CLASSIFICATION.get_parameters(test_image_path)

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
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {value}")

