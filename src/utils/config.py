# src/utils/config.py
import json
import os
import streamlit as st

# 🌟 YENİ: Merkezi yol yöneticisi (hesap bazlı dosya yolları)
from src.utils.paths import get_settings_path

# Standardwerte bleiben erhalten
DEFAULT_SETTINGS_MODEL1 = {
    "GRID_STEP": 0.05,
    "TAKE_PROFIT": 0.05,
    "LEVELS_BELOW": 6,
    "LEVELS_ABOVE": 6,
    "DEFAULT_LOT": 0.01,
    "MAX_OPEN_POSITIONS": 999,
    "MAX_PRICE_LIMIT": 120.00,
    "MIN_PRICE_LIMIT": 20.00,
    "LOOP_INTERVAL_SECONDS": 1.9,
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
    "ZONES": [],
}


def get_settings_file(model_name: str) -> str:
    """Generiert einen einzigartigen Dateinamen basierend auf Konto-ID und Modell."""
    account_id = "default"

    # 1. ÖNCE Çevresel Değişkene (Subprocess/Arka Plan) bak
    if "ACTIVE_ACCOUNT_ID" in os.environ:
        account_id = os.environ["ACTIVE_ACCOUNT_ID"]
    else:
        # 2. YOKSA Streamlit arayüzünde (App.py) olduğumuzu varsay ve oradan çek
        try:
            if (
                "selected_account" in st.session_state
                and st.session_state.selected_account
            ):
                account_id = str(
                    st.session_state.selected_account.get("login", "default")
                )
        except Exception:
            pass

    # 🌟 YENİ: Yol üretimi tek merkezden (paths.py) — port bağımlılığı yok
    return get_settings_path(account_id, model_name)


def get_default_settings(model_name: str) -> dict:
    return (
        DEFAULT_SETTINGS_MODEL1 if model_name == "Model 1" else DEFAULT_SETTINGS_MODEL2
    )


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
    except Exception:
        return default_settings


def save_settings(settings_dict, model_name: str = "Model 1"):
    """Yeni ayarları JSON dosyasına kaydeder."""
    file_path = get_settings_file(model_name)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(settings_dict, f, indent=4)
