# src/utils/bot_manager.py
import subprocess
import sys
import os
import json
import streamlit as st
from pathlib import Path

# Proje dizinini al ki utils klasöründeki dosyalara ulaşabilelim
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Gerekli bağlantı ve temizlik fonksiyonlarını içeri aktar
from src.utils.mt5_connection import connect_to_mt5
from src.utils.trade_utils import cancel_all_pending_orders
import MetaTrader5 as mt5

# GLOBALE VARIABLE (Sicher vor Streamlit-Abstürzen!)
_ACTIVE_BOTS = {}


def is_bot_running(account_id: str) -> bool:
    """Belirli bir hesabın robotunun arka planda sağlıklı çalışıp çalışmadığını kontrol eder (Crash Detection)."""
    if account_id in _ACTIVE_BOTS:
        process = _ACTIVE_BOTS[account_id]
        # poll() None dönüyorsa süreç hala hayattadır.
        if process.poll() is None:
            return True
        else:
            # Robot kendi kendine durmuş veya MT5 çökmüş. Temizliğini yap!
            del _ACTIVE_BOTS[account_id]
            return False
    return False


def start_bot_process(account_id: str, model_name: str) -> bool:
    """Belirli bir hesap için izole bir Subprocess (alt süreç) başlatır."""
    if is_bot_running(account_id):
        return True  # Zaten çalışıyor

    try:
        # Her hesaba özel log dosyası oluştur
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, f"bot_{account_id}_error.log")

        # Log dosyasını 'append' (ekleme) modunda aç
        log_file = open(log_file_path, "a", encoding="utf-8")

        # Ayrı bir Python programı olarak botu tetikle.
        process = subprocess.Popen(
            [sys.executable, "-u", "src/core/bot_runner.py", account_id, model_name],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Mükemmel izolasyon: Süreci SADECE global değişkene yazıyoruz
        _ACTIVE_BOTS[account_id] = process
        return True

    except Exception as e:
        # Profesyonel hata yakalama: Çökme durumunda arayüze net bilgi ver
        st.error(
            f"🚨 Sistem Hatası: {account_id} için robot başlatılamadı!\n\nDetay: {str(e)}"
        )
        return False


def stop_bot_process(account_id: str) -> bool:
    """Çalışan robotu KESİN olarak durdurur ve MT5'teki BEKLEYEN emirleri siler."""

    # 1. AŞAMA: MT5 Temizliği (Robotu öldürmeden hemen önce MT5'teki bekleyen emirleri temizle)
    try:
        accounts_path = os.path.join(project_root, "configs", "accounts.json")
        if os.path.exists(accounts_path):
            with open(accounts_path, "r", encoding="utf-8") as f:
                accounts_data = json.load(f)
                accounts = (
                    accounts_data
                    if isinstance(accounts_data, list)
                    else accounts_data.get("accounts", [])
                )

            # Kapatılacak hesabı bul
            active_account = next(
                (acc for acc in accounts if str(acc.get("login")) == account_id), None
            )

            # Temizlik için geçici olarak MT5'e bağlanıp emirleri iptal et
            if active_account and connect_to_mt5(active_account):
                cancel_all_pending_orders(
                    mt5
                )  # Aktiflere dokunmaz, sadece bekleyenleri siler
                mt5.shutdown()
    except Exception as e:
        st.warning(f"MT5 Bekleyen emir temizliği sırasında hata oluştu: {e}")

    # 2. AŞAMA: Python Zombi Sürecini Yok Et
    if account_id in _ACTIVE_BOTS:
        process = _ACTIVE_BOTS[account_id]
        try:
            if os.name == "nt":
                # Windows işletim sistemi ise Taskkill ile tüm alt döngüleri acımasızca sonlandır
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                # Mac/Linux sistemleri için
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
        except Exception as e:
            st.error(f"⚠️ Robot durdurulurken pürüz çıktı: {str(e)}")
        finally:
            # İşlem bittiğinde global listeden sil
            if account_id in _ACTIVE_BOTS:
                del _ACTIVE_BOTS[account_id]
            return True

    return False
