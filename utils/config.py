# utils/config.py
import json
import os

SETTINGS_FILE = "settings.json"

# Dosya yoksa kullanılacak ilk fabrika ayarları
DEFAULT_SETTINGS = {
    "GRID_STEP": 0.05,
    "TAKE_PROFIT": 0.05,
    "LEVELS_BELOW": 6,
    "LEVELS_ABOVE": 6,
    "DEFAULT_LOT": 0.01,
    "MAX_OPEN_POSITIONS": 999,
    "MAX_PRICE_LIMIT": 120.00,
    "MIN_PRICE_LIMIT": 20.00
}

def load_settings():
    """JSON dosyasından ayarları okur, dosya yoksa varsayılanları oluşturur."""
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_SETTINGS

def save_settings(settings_dict):
    """Yeni ayarları JSON dosyasına kaydeder."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings_dict, f, indent=4)