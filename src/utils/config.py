# utils/config.py
import json
import os

SETTINGS_MODEL1_FILE = "configs/settings_model1.json"
SETTINGS_MODEL2_FILE = "configs/settings_model2.json"
SETTINGS_MODEL3_FILE = "configs/settings_model3.json"

# Dosya yoksa kullanılacak ilk fabrika ayarları
DEFAULT_SETTINGS_MODEL1 = {
    "GRID_STEP": 0.05,
    "TAKE_PROFIT": 0.05,
    "LEVELS_BELOW": 6,
    "LEVELS_ABOVE": 6,
    "DEFAULT_LOT": 0.01,
    "MAX_OPEN_POSITIONS": 999,
    "MAX_PRICE_LIMIT": 120.00,
    "MIN_PRICE_LIMIT": 20.00,
    "LOOP_INTERVAL_SECONDS": 1.9
}

DEFAULT_SETTINGS_MODEL2 = {
    "GLOBAL_GRID_STEP": 0.05,
    "GLOBAL_TAKE_PROFIT": 0.05,
    "GLOBAL_DEFAULT_LOT": 0.01,
    "MAX_OPEN_POSITIONS": 999,
    "MAX_PRICE_LIMIT": 120.00,
    "MIN_PRICE_LIMIT": 20.00,
    "LOOP_INTERVAL_SECONDS": 1.0,
    "CLEAR_ON_ZONE_EXIT": True,
    "ZONES": []
}

def get_settings_file(model_name: str) -> str:
    return SETTINGS_MODEL1_FILE if model_name == "Model 1" else SETTINGS_MODEL2_FILE

def get_default_settings(model_name: str) -> dict:
    return DEFAULT_SETTINGS_MODEL1 if model_name == "Model 1" else DEFAULT_SETTINGS_MODEL2

def load_settings(model_name: str = "Model 1"):
    """JSON dosyasından ayarları okur, dosya yoksa varsayılanları oluşturur."""
    file_path = get_settings_file(model_name)
    default_settings = get_default_settings(model_name)
    
    if not os.path.exists(file_path):
        save_settings(default_settings, model_name)
        return default_settings
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default_settings

def save_settings(settings_dict, model_name: str = "Model 1"):
    """Yeni ayarları JSON dosyasına kaydeder."""
    file_path = get_settings_file(model_name)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(settings_dict, f, indent=4)
