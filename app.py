# app.py

import sys
import os
import json
from pathlib import Path
import platform
import time
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
    PAGE_TITLE = "[LIVE] Grid Robot Control"
    PAGE_ICON = "🔴"
else:
    PAGE_TITLE = "[TEST] Grid Robot Control"
    PAGE_ICON = "🟢"

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")

# ==========================================
# 3. KENDİ MODÜLLERİMİZİ İÇE AKTARMA
# ==========================================
from src.utils.bot_manager import is_bot_running, start_bot_process, stop_bot_process
from src.components.account_selector import render_account_selector
from src.components.chart_viewer import render_chart
from src.utils.mt5_connection import connect_to_mt5
from src.components.header import render_header
from src.components.settings_panel import render_settings_panel
from src.components.metrics import render_metrics
from src.components.controls import render_controls
from src.components.log_viewer import render_log_viewer
from src.styles.custom_css import apply_custom_css
from src.utils.config import load_settings, save_settings

import src.core.model_1 as model_1
import src.core.model_2 as model_2
import src.core.model_3 as model_3

def get_live_metrics_from_file(account_id):
    """Liest die aktuellsten Metriken des Subprozesses aus der JSON-Datei."""
    metrics_file = os.path.join("logs", f"live_metrics_{account_id}.json")
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
    }

# ==========================================
# 1. STREAMLIT CONFIG & CSS
# ==========================================
apply_custom_css()

# YENİ: Hesaplara özel SİLİNMEYEN model hafızası
if "account_models_memory" not in st.session_state:
    st.session_state.account_models_memory = {}

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
# MOTOR SEÇİMİNİ HESABA GÖRE BELİRLE
# ==========================================
# Hafızada bu hesap için model yoksa Model 2 yap (VARSAYILAN DEĞİŞTİRİLDİ)
if account_id not in st.session_state.account_models_memory:
    st.session_state.account_models_memory[account_id] = "Model 2"

# Bu hesabın hafızasındaki modeli aktif yapıyoruz
st.session_state.selected_model = st.session_state.account_models_memory[account_id]

# Motoru seçili modele göre ayarla
if st.session_state.selected_model == "Model 1":
    bot_engine = model_1
elif st.session_state.selected_model == "Model 2":
    bot_engine = model_2
else:
    bot_engine = model_3


st.markdown("---")

# ==========================================
# 3. GÜNCEL ÇALIŞMA DURUMUNU SORGULA (CRASH DETECTION)
# ==========================================
# Durumu globalden değil, Bot Manager'dan SADECE bu hesap için soruyoruz
account_is_running = is_bot_running(account_id)


# ==========================================
# 4. AYARLARI VE METRİKLERİ YÜKLE
# ==========================================
current_settings = load_settings(st.session_state.selected_model)

render_header(
    symbol="USOUSD",
    broker=active_account.get("server", "Bilinmeyen Broker"),
    is_market_open=True,
)

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


# ==========================================
# ALT KOKPİT PANELİ
# ==========================================
col_metrics, col_controls = st.columns([2.5, 1.5])


# 🌟 YENİ: Sadece metrikleri 2 saniyede bir canlı güncelleyen parça!
@st.fragment(run_every=2)
def live_metrics_fragment(acc_id):
    # En güncel veriyi JSON dosyasından ANLIK olarak oku
    if is_bot_running(acc_id):
        fresh_data = get_live_metrics_from_file(acc_id)
    else:
        fresh_data = {
            "profit": 0.0,
            "open_positions": 0,
            "pending_orders": 0,
            "current_price": 0.0,
        }

    render_metrics(
        profit=fresh_data["profit"],
        open_positions=fresh_data["open_positions"],
        pending_orders=fresh_data["pending_orders"],
        current_price=fresh_data["current_price"],
    )


with col_metrics:
    # Parçayı (Fragment) sütunun içine yerleştiriyoruz
    live_metrics_fragment(account_id)

with col_controls:
    # EKSİK BIRAKILAN KISIM TAMAMLANDI
    action, chosen_model = render_controls(
        is_running=account_is_running,
        account_id=account_id,
        current_model=st.session_state.selected_model,  # <--- NEU
    )

if chosen_model and chosen_model != st.session_state.selected_model:
    st.session_state.selected_model = chosen_model
    # NEU: Wir speichern die Auswahl in unserem unlöschbaren Gedächtnis
    st.session_state.account_models_memory[account_id] = chosen_model
    st.rerun()


# ==========================================
# BAŞLAT / DURDUR MANTIĞI (SUBPROCESS İLE)
# ==========================================
if action == "TOGGLE":
    if not account_is_running:
        # Önce MT5 bağlantısını test et
        connection_success = connect_to_mt5(active_account)

        if connection_success:
            # Subprocess (Alt Süreç) başlat!
            if start_bot_process(account_id, st.session_state.selected_model):
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
        # Zombi bırakmadan, süreci işletim sistemi seviyesinde öldür
        stop_bot_process(account_id)
        st.toast(f"🛑 {active_account['account_name']} robotu durduruldu!", icon="⚠️")
        st.rerun()


# ==========================================
# AYARLAR VE MAC SİMÜLATÖRÜ
# ==========================================
updated_settings = render_settings_panel(
    current_settings, st.session_state.selected_model, account_id
)

if updated_settings:
    save_settings(updated_settings, st.session_state.selected_model)
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
    sim_file_path = os.path.join("logs", f"simulated_price_{account_id}.json")
    try:
        with open(sim_file_path, "w", encoding="utf-8") as f:
            json.dump({"price": mock_price}, f)
    except Exception:
        pass

# ==========================================
# GRAFİK VE LOG EKRANI (İşletim Sistemine Göre Dinamik)
# ==========================================
if platform.system() != "Windows":
    # Mac ortamında: Grafik ve Log yan yana (Grafik daha geniş)
    col_chart, col_log = st.columns([2, 1])
    with col_chart:
        render_chart(
            current_active_price, current_settings, st.session_state.selected_model
        )
    with col_log:
        render_log_viewer(account_id)
else:
    # Windows ortamında: Grafik GİZLİ, Loglar TAM EKRAN GENİŞLİĞİNDE
    st.markdown("---")
    render_log_viewer(account_id)
