import json
import os
from typing import Dict

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_CONFIG_PATH = os.path.join(APP_ROOT, "JSON", "ai_config.json")

ALLOWED_MODELS = {
    "disabled",
    "speciesnet-default",
    "speciesnet-custom",
    "yolo-default",
    "yolo-custom",
}

DEFAULT_SETTINGS = {
    "active_model": "speciesnet-default",
    "custom_model_path": "",
}


def get_ai_settings() -> Dict[str, str]:
    settings = dict(DEFAULT_SETTINGS)

    if os.path.exists(AI_CONFIG_PATH):
        try:
            with open(AI_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                settings.update({
                    "active_model": str(data.get("active_model", settings["active_model"])),
                    "custom_model_path": str(data.get("custom_model_path", settings["custom_model_path"])),
                })
        except Exception:
            pass

    if settings["active_model"] not in ALLOWED_MODELS:
        settings["active_model"] = DEFAULT_SETTINGS["active_model"]

    return settings


def set_ai_settings(active_model: str, custom_model_path: str = "") -> Dict[str, str]:
    if active_model not in ALLOWED_MODELS:
        raise ValueError(f"Unsupported model selection: {active_model}")

    payload = {
        "active_model": active_model,
        "custom_model_path": custom_model_path.strip(),
    }

    os.makedirs(os.path.dirname(AI_CONFIG_PATH), exist_ok=True)
    with open(AI_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return payload
