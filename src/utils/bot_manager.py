# src/utils/bot_manager.py
import subprocess
import sys
import os
import json
import streamlit as st
import time  # Bekleme (sleep) için eklendi
from pathlib import Path

# Proje dizinini al ki utils klasöründeki dosyalara ulaşabilelim
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Gerekli bağlantı ve temizlik fonksiyonlarını içeri aktar
from src.utils.mt5_connection import connect_to_mt5
from src.utils.trade_utils import cancel_all_pending_orders

import psutil  # 🌟 YENİ: İşletim sistemi süreçlerini okumak için

# 🌟 YENİ: Merkezi yol yöneticisini içeri aktarıyoruz
from src.utils.paths import get_err_log_path, get_pid_path

# ==========================================
# MAC KORUMASI (Crash Önleyici Zırh)
# ==========================================
try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None  # Mac ortamında çökmemesi için mt5 modülünü boş (None) atıyoruz


def is_bot_running(account_id: str) -> bool:
    """Robotun gerçekten (İşletim Sistemi seviyesinde) çalışıp çalışmadığını kontrol eder."""
    pid_file = get_pid_path(account_id)
    if not os.path.exists(pid_file):
        return False

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        # psutil ile o PID'ye sahip sürecin OS üzerinde yaşayıp yaşamadığını kontrol et
        if psutil.pid_exists(pid):
            # Süreç var ama zombi mi?
            p = psutil.Process(pid)
            if p.status() != psutil.STATUS_ZOMBIE:
                return True

        # Eğer buraya geldiyse süreç ölmüştür, çöp (PID) dosyasını temizle
        os.remove(pid_file)
        return False
    except Exception:
        return False


def start_bot_process(account_id: str, model_name: str) -> bool:
    """Belirli bir hesap için izole bir Subprocess (alt süreç) başlatır."""
    if is_bot_running(account_id):
        return True  # Zaten çalışıyor

    log_file = None
    try:
        # Her hesaba özel log dosyası oluştur (Klasör kontrolü paths.py içinde yapılır)
        log_file_path = get_err_log_path(account_id)

        # Log dosyasını 'append' (ekleme) modunda aç
        log_file = open(log_file_path, "a", encoding="utf-8")

        # Ayrı bir Python programı olarak botu tetikle.
        process = subprocess.Popen(
            [sys.executable, "-u", "src/core/bot_runner.py", account_id, model_name],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # 🌟 YENİ: Sürecin ID'sini (PID) kalıcı olarak diske yaz! (RAM sıfırlansa da ölmez)
        pid_file = get_pid_path(account_id)
        with open(pid_file, "w") as f:
            f.write(str(process.pid))

        return True

    except Exception as e:
        # Profesyonel hata yakalama: Çökme durumunda arayüze net bilgi ver
        st.error(
            f"🚨 Sistem Hatası: {account_id} için robot başlatılamadı!\n\nDetay: {str(e)}"
        )
        return False
    finally:
        # GÜVENLİK DÜZELTMESİ: Açılan dosya akışı (file descriptor) hafızada kilitli kalmasın diye kapatılıyor
        if log_file is not None:
            try:
                log_file.close()
            except Exception:
                pass


def stop_bot_process(account_id: str) -> bool:
    """Çalışan robotu KESİN olarak durdurur ve MT5'teki BEKLEYEN emirleri siler."""

    pid_file = get_pid_path(account_id)
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())

            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                if os.name == "nt":
                    # Windows işletim sistemi ise Taskkill ile tüm alt döngüleri acımasızca sonlandır
                    subprocess.call(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    # Mac/Linux sistemleri için
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        process.kill()

                # Subprocess'in gerçekten kapanması için işletim sistemine 1 saniye nefes payı ver
                time.sleep(1.0)

            # İşlem bittiğinde kalıcı dosyayı (PID) sil
            os.remove(pid_file)
        except Exception as e:
            st.error(f"⚠️ Robot durdurulurken pürüz çıktı: {str(e)}")

    # 2. AŞAMA (DÜZELTME): MT5 Temizliği (Robot öldükten sonra arkasını biz temizliyoruz)
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
                if mt5 is not None:
                    # DÜZELTME: Belirli bir magic number kısıtlaması kaldırıldı, hesaptaki tüm bekleyen emirler temizlenecek!
                    cancel_all_pending_orders(mt5)
                    mt5.shutdown()
    except Exception as e:
        st.warning(f"MT5 Bekleyen emir temizliği sırasında hata oluştu: {e}")

    return True
