# src/utils/paths.py
import os
import re
from pathlib import Path

# Projenin kök dizinini dinamik olarak bul (proje taşınsa da çalışır)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

CONFIGS_DIR = os.path.join(PROJECT_ROOT, "configs")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")


def _ensure_dir(path):
    """Verilen klasörün var olduğundan emin olur."""
    os.makedirs(path, exist_ok=True)
    return path


def _ensure_logs_dir():
    return _ensure_dir(LOGS_DIR)


def _ensure_configs_dir():
    return _ensure_dir(CONFIGS_DIR)


def _ensure_data_dir():
    return _ensure_dir(DATA_DIR)


def safe_account_id(account_id) -> str:
    """Güvenlik: Hesap ID dosya adı olarak kullanılacağı için
    sadece rakamları kabul eder. (MT5 login numaraları tamamen sayısaldır)"""
    cleaned = re.sub(r"\D", "", str(account_id))
    return cleaned or "unknown"


# ══════════════════════════════════════════════════════════
# 1. HESAP AYARLARI (configs/) — Sadece MT5 Login ID'ye bağlı
# ══════════════════════════════════════════════════════════
def get_settings_path(account_id: str, model_name: str = "Model 2") -> str:
    """Örn: configs/settings_7946558_Model_2.json
    Model adı korundu çünkü Grid'de Model 1/2/3 farklı şablonlara sahip.
    Dosya adında port veya makine adı YOK."""
    safe_model = model_name.replace(" ", "_")
    safe = safe_account_id(account_id)
    return os.path.join(_ensure_configs_dir(), f"settings_{safe}_{safe_model}.json")


# ══════════════════════════════════════════════════════════
# 2. SİSTEM DURUMU / HAFIZA (data/) — Kaynağı MT5, adı Account ID
# ══════════════════════════════════════════════════════════
def get_state_path(account_id: str) -> str:
    """Örn: data/state_7946558.json
    Açık pozisyonlar, bekleyen emirler, aktif bölgeler, PID, zaman damgası."""
    safe = safe_account_id(account_id)
    return os.path.join(_ensure_data_dir(), f"state_{safe}.json")


# ══════════════════════════════════════════════════════════
# 3. LOGLAR VE CANLI KÖPRÜLER (logs/) — Hesap bazlı, port'suz
# ══════════════════════════════════════════════════════════
def get_err_log_path(account_id: str) -> str:
    safe = safe_account_id(account_id)
    return os.path.join(_ensure_logs_dir(), f"err_{safe}.log")


def get_ui_state_path(account_id: str) -> str:
    safe = safe_account_id(account_id)
    return os.path.join(_ensure_logs_dir(), f"ui_{safe}.json")


def get_metrics_path(account_id: str) -> str:
    safe = safe_account_id(account_id)
    return os.path.join(_ensure_logs_dir(), f"met_{safe}.json")


def get_sim_price_path(account_id: str) -> str:
    safe = safe_account_id(account_id)
    return os.path.join(_ensure_logs_dir(), f"sim_{safe}.json")


def get_pid_path(account_id: str) -> str:
    safe = safe_account_id(account_id)
    return os.path.join(_ensure_logs_dir(), f"pid_{safe}.txt")