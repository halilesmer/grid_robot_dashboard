# src/components/log_viewer.py
import streamlit as st
import os
import glob
from collections import deque


MAX_LINES = 20  # Ekranda gösterilecek son satır sayısı
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB Limit


def get_recent_logs(account_id: str):
    """Robotun (Subprocess) o hesaba özel ürettiği logları okur."""
    # YENİ: Artık tek bir global dosya yerine, bu hesaba özel dosyayı okuyoruz!
    log_file = os.path.join("logs", f"bot_{account_id}_error.log")

    if not os.path.exists(log_file):
        return "Henüz bu hesap için robot log kaydı bulunmuyor..."

    if os.path.getsize(log_file) > MAX_FILE_SIZE:
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("[SİSTEM KORUMASI] Dosya çok büyüdüğü için temizlendi.\n")
        except Exception:
            pass

    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            lines = deque(f, maxlen=MAX_LINES)
            return "".join(lines)
    except Exception as e:
        return f"[HATA] Loglar okunamadı: {e}"


def get_latest_mt5_log():
    """MT5'in kendi orijinal günlük sistem logunu bulur ve okur."""
    mt5_log_dir = os.path.expanduser(
        "~\\AppData\\Roaming\\MetaQuotes\\Terminal\\*\\Logs"
    )
    log_files = glob.glob(os.path.join(mt5_log_dir, "*.log"))

    if not log_files:
        return "Windows/MT5 orijinal log dosyası henüz bulunamadı."

    latest_file = max(log_files, key=os.path.getmtime)

    try:
        # MT5 logları UTF-16 formatında tutar
        with open(latest_file, "r", encoding="utf-16", errors="ignore") as f:
            lines = deque(f, maxlen=15)
            return "".join(lines)
    except Exception as e:
        return f"MT5 Log okuma hatası: {e}"


@st.fragment(run_every=3)

def render_log_viewer(account_id: str = "default"):
    """Canlı Log Ekranı Bileşeni (Sekmeli Görünüm)"""
    st.subheader("📟 Sistem ve Terminal Logları")

    # İki farklı sekme oluşturuyoruz
    tab1, tab2 = st.tabs(["🤖 Robot Logları", "🏦 Orijinal MT5 Logları"])

    with tab1:
        st.caption(f"{account_id} hesabının arka plan işlemlerinin son 20 adımı.")
        # YENİ: account_id parametresini fonksiyona gönderiyoruz
        logs = get_recent_logs(account_id)
        st.code(logs, language="bash")

    with tab2:
        st.caption(
            "MetaTrader 5 terminalinin arka planda ürettiği orijinal sistem kayıtları."
        )
        mt5_logs = get_latest_mt5_log()
        st.code(mt5_logs, language="bash")
