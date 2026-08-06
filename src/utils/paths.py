# src/utils/paths.py
import os
from pathlib import Path

# Projenin kök dizinini dinamik olarak bul
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")


def _ensure_logs_dir():
    """Logs klasörünün var olduğundan emin olur."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    return LOGS_DIR


def get_err_log_path(account_id: str) -> str:
    return os.path.join(_ensure_logs_dir(), f"err_{account_id}.log")


def get_cmd_path(account_id: str) -> str:
    return os.path.join(_ensure_logs_dir(), f"cmd_{account_id}.json")


def get_ui_state_path(account_id: str) -> str:
    return os.path.join(_ensure_logs_dir(), f"ui_{account_id}.json")


def get_metrics_path(account_id: str) -> str:
    return os.path.join(_ensure_logs_dir(), f"met_{account_id}.json")


def get_sim_price_path(account_id: str) -> str:
    return os.path.join(_ensure_logs_dir(), f"sim_{account_id}.json")
