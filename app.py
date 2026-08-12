# app.py

import sys
import os
import json
from pathlib import Path
import platform
import time
import sys
import os
from pathlib import Path
import streamlit as st

# ==========================================
# 1. YOL AYARLARI (Python'a src klasörünü gösteriyoruz - EN ÜSTTE OLMALI)
# ==========================================
sys.path.append(str(Path(__file__).parent / "src"))


# ==========================================
# 2. ORTAM VE SAYFA AYARI (İLK STREAMLIT KOMUTU)
# ==========================================
env = os.getenv("ROBOT_ENV", "TEST").upper()

if env == "LIVE":
    PAGE_TITLE = "🔴 [LIVE] Grid Robot Control"
    PAGE_ICON = "🔴"
else:
    PAGE_TITLE = "🧪 [TEST] Grid Robot Control"
    PAGE_ICON = "🧪"

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")


# ==========================================
# 3. KENDİ MODÜLLERİMİZİ İÇE AKTARMA
# ==========================================
from src.utils.bot_manager import (
    is_bot_running,
    start_bot_process,
    stop_bot_process,
    stop_and_close_all,
)
from src.components.account_selector import render_account_selector
from src.components.chart_viewer import render_chart
from src.components.dialogs import confirm_stop_motor_dialog
from src.utils.mt5_connection import connect_to_mt5
from src.components.header import render_main_title
from src.components.settings_panel import render_settings_panel
from src.components.log_viewer import render_log_viewer
from src.styles.custom_css import apply_custom_css
from src.utils.config import load_settings, save_settings

# 🌟 YENİ: Merkezi yol yöneticisi
from src.utils.paths import get_metrics_path, get_sim_price_path

import src.core.model_2 as model_2


def get_live_metrics_from_file(account_id):
    """Liest die aktuellsten Metriken des Subprozesses aus der JSON-Datei."""
    metrics_file = get_metrics_path(account_id)
    if os.path.exists(metrics_file):
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass  # Wenn die Datei exakt in dieser Millisekunde geschrieben wird
    return {
        "profit": 0.0,
        "open_positions": 0,
        "pending_orders": 0,
        "current_price": 0.0,
        "algo_trading_error": False,
        "remote_paused": False,
    }


# ==========================================
# 1. STREAMLIT CONFIG & CSS
# ==========================================
apply_custom_css()

# 🌟 YENİ: Başlık En Üste Geldi
render_main_title()

# ==========================================
# 2. ÖNCE HESABI SEÇ (TAM GENİŞLİKTE)
# ==========================================
active_account = render_account_selector()

# Güvenlik: Eğer JSON dosyasında hiç hesap yoksa veya hata varsa programı burada durdur.
if not active_account:
    st.stop()

# Seçili hesabın benzersiz ID'sini alıyoruz
account_id = str(active_account.get("login", "default"))

# ==========================================
# MOTOR SEÇİMİ (TEK KRAL: MODEL 2)
# ==========================================
bot_engine = model_2


st.markdown("---")

# ==========================================
# 3. GÜNCEL ÇALIŞMA DURUMUNU SORGULA (CRASH DETECTION)
# ==========================================
# Durumu globalden değil, Bot Manager'dan SADECE bu hesap için soruyoruz
account_is_running = is_bot_running(account_id)


# ==========================================
# 4. AYARLARI VE METRİKLERİ YÜKLE
# ==========================================
current_settings = load_settings("Model 2")

# Canlı verileri JSON dosyasından çek (Çünkü robot artık Subprocess olarak çalışıyor)
if account_is_running:
    live_data = get_live_metrics_from_file(account_id)
else:
    live_data = {
        "profit": 0.0,
        "open_positions": 0,
        "pending_orders": 0,
        "current_price": 0.0,
        "algo_trading_error": False,
        "remote_paused": False,
    }


# ==========================================
# ALGO TRADING GÜVENLİK UYARISI
# ==========================================
if live_data.get("algo_trading_error", False):
    st.error(
        "🚨 **KRİTİK HATA:** MetaTrader 5'te **'Algo Trading' (Otomatik Ticaret)** kapalı! "
        "Robot emir gönderemiyor. Lütfen MT5 terminalinin üst menüsünden 'Algo Trading' butonunu aktif (yeşil) hale getirin.",
        icon="🚫",
    )

    if account_is_running:
        stop_bot_process(account_id)
        st.toast("🛑 Motor kilitlendi: Algo Trading kapalı!", icon="⚠️")
        st.rerun()


# 📡 Mobil MT5'ten (Sinyal Emri ile) uzaktan durduruldu mu?
if live_data.get("remote_paused", False) and account_is_running:
    st.warning(
        "📡 **Motor Mobil MT5'ten UZAKTAN DURDURULDU.** "
        "Bekleyen emirler silindi, açık pozisyonlar korundu. "
        "Tekrar başlatmak için yukarıdaki **MOTOR** butonunu kullanın "
        "(mobil MT5'te 1$ Buy Limit yalnızca durdurmak içindir).",
        icon="⏸️",
    )


# 🌟 Ana Motor tetikleyicisi artık settings_panel üzerinden yönetiliyor
action = None
if st.session_state.get(f"motor_toggle_{account_id}"):
    action = "TOGGLE"
    st.session_state[f"motor_toggle_{account_id}"] = False

# ==========================================
# BAŞLAT / DURDUR MANTIĞI (SUBPROCESS İLE)
# ==========================================
if action == "TOGGLE":
    if not account_is_running:
        # Önce MT5 bağlantısını test et
        connection_success = connect_to_mt5(active_account)

        if connection_success:
            # Subprocess (Alt Süreç) başlat!
            if start_bot_process(account_id, "Model 2"):
                st.toast(
                    f"🚀 {active_account['account_name']} için robot izole olarak başlatıldı!",
                    icon="✅",
                )
                st.rerun()
            else:
                st.toast(
                    "🔴 Hata: Robot başlatılamadı! Lütfen hata kayıtlarını (logs) inceleyin.",
                    icon="❌",
                )
        else:
            # EKLENDİ: Bağlantı başarısız olursa kullanıcıya bildir!
            st.toast(
                "🔴 MT5 Bağlantı Hatası! Terminal açılamadı veya bilgiler yanlış.",
                icon="❌",
            )
    else:
        # 🚀 PHASE 4: Kapatma SADECE kullanıcının açık seçimiyle yapılır.
        # "Durdur" -> süreç kapanır, pozisyonlar/emirler korunur.
        # "Durdur ve Tümünü Kapat" -> süreç kapanır + tüm robot pozisyonları kapatılır.
        confirm_stop_motor_dialog(
            account_id,
            on_stop_func=stop_bot_process,
            on_stop_close_func=stop_and_close_all,
        )


# ==========================================
# AYARLAR VE MAC SİMÜLATÖRÜ
# ==========================================
updated_settings = render_settings_panel(
    current_settings,
    "Model 2",
    account_id,
    live_data,
    active_account,
    account_is_running,
)

if updated_settings:
    save_settings(updated_settings, "Model 2")
    st.success(f"✅ Ayarlar başarıyla güncellendi ve {account_id} için kaydedildi!")
    st.rerun()

st.divider()

current_active_price = live_data.get("current_price", 0.0)

if platform.system() != "Windows":
    st.warning("💻 Mac Test Modu Aktif - Fiyat Simülatörü")
    mock_price = st.slider(
        "Canlı Fiyatı Belirle (USOUSD)",
        min_value=50.0,
        max_value=150.0,
        value=75.0,
        step=0.10,
    )
    current_active_price = mock_price
    bot_engine.SIMULATED_PRICE = mock_price  # Arayüzün kendi grafiği için

    # YENİ: Alt sürece (backend) fiyatı iletmek için köprü kuruyoruz
    sim_file_path = get_sim_price_path(account_id)
    try:
        tmp_sim = sim_file_path + ".tmp"
        with open(tmp_sim, "w", encoding="utf-8") as f:
            json.dump({"price": mock_price}, f)
        os.replace(tmp_sim, sim_file_path) # Atomik değişim
    except Exception:
        pass

# ==========================================
# GRAFİK VE LOG EKRANI (İşletim Sistemine Göre Dinamik)
# ==========================================
if platform.system() != "Windows":
    # Mac ortamında: Grafik ve Log yan yana (Grafik daha geniş)
    col_chart, col_log = st.columns([2, 1])
    with col_chart:
        render_chart(current_active_price, current_settings, "Model 2")
    with col_log:
        render_log_viewer(account_id)
else:
    # Windows ortamında: Grafik GİZLİ, Loglar TAM EKRAN GENİŞLİĞİNDE
    st.markdown("---")
    render_log_viewer(account_id)
