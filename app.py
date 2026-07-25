# app.py
import streamlit as st
import threading
import time  
import platform 

from components.header import render_header
from components.settings_panel import render_settings_panel
from components.metrics import render_metrics
from components.controls import render_controls
from components.log_viewer import render_log_viewer 
from styles.custom_css import apply_custom_css
from utils.config import load_settings, save_settings
import core.model_1 as model_1
import core.model_2 as model_2
import core.model_3 as model_3 # 👈 BARKOD: Model 3 eklendi

st.set_page_config(
    page_title="Grid Robot Control",
    page_icon="🤖",
    layout="wide"
)

apply_custom_css()

if "robot_running" not in st.session_state:
    st.session_state.robot_running = False

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "Model 1"

# 👈 BARKOD: Aktif olan modeli seç (Model 3 desteği eklendi)
if st.session_state.selected_model == "Model 1":
    bot_engine = model_1
elif st.session_state.selected_model == "Model 2":
    bot_engine = model_2
else:
    bot_engine = model_3

current_settings = load_settings(st.session_state.selected_model)

render_header(symbol="USOUSD", broker="Eightcap-Demo", is_market_open=True)

# Eğer robot çalışıyorsa canlı verileri çek, çalışmıyorsa her şeyi 0 göster
if st.session_state.robot_running:
    # Hata yakalama (Model 3'te get_live_metrics henüz yoksa çökmeyi önler)
    if hasattr(bot_engine, 'get_live_metrics'):
        live_data = bot_engine.get_live_metrics()
    else:
        live_data = {"profit": 0.0, "open_positions": 0, "pending_orders": 0, "current_price": 0.0}
else:
    live_data = {
        "profit": 0.0,
        "open_positions": 0,
        "pending_orders": 0,
        "current_price": 0.0,
    }

render_metrics(
    profit=live_data["profit"],
    open_positions=live_data["open_positions"],
    pending_orders=live_data["pending_orders"],
    current_price=live_data["current_price"],
)

action, chosen_model = render_controls(
    is_running=st.session_state.robot_running,
    current_model=st.session_state.selected_model
)

if chosen_model and chosen_model != st.session_state.selected_model:
    st.session_state.selected_model = chosen_model
    st.rerun()

if action == "TOGGLE":
    st.session_state.robot_running = not st.session_state.robot_running
    
    if st.session_state.robot_running:
        bot_engine.IS_RUNNING = True
        robot_thread = threading.Thread(target=bot_engine.main_loop, daemon=True)
        robot_thread.start()
        st.toast("🚀 Robot başarıyla başlatıldı!", icon="✅")
    else:
        bot_engine.IS_RUNNING = False
        st.toast("🛑 Robot durduruldu!", icon="⚠️")
        
    st.rerun()

updated_settings = render_settings_panel(current_settings, st.session_state.selected_model)

if updated_settings:
    save_settings(updated_settings, st.session_state.selected_model)
    st.success("✅ Ayarlar başarıyla güncellendi ve sisteme kaydedildi!")
    st.rerun()

st.divider()

# 5. Log Gösterici Bileşenini Sayfanın En Altına Ekle
render_log_viewer()

# ==========================================
# CANLI VERİ AKIŞI (AUTO-REFRESH) DÖNGÜSÜ
# ==========================================
if st.session_state.robot_running:
    # Sayfayı 1 saniye bekletip tekrar yukarıdan aşağı okumasını sağlarız.
    # Böylece metrikler ve loglar kendi kendine akar.
    time.sleep(1)
    st.rerun()


# ==========================================
# 🧪 MAC TEST SİMÜLATÖRÜ (Sadece Mac'te Görünür)
# ==========================================
if platform.system() != "Windows":
    st.warning("🧪 Mac Test Modu Aktif - Fiyat Simülatörü", icon="💻")
    # Kullanıcıdan fiyatı kaydırıcı ile al
    mock_price = st.slider(
        "Canlı Fiyatı Belirle (USOUSD)", 
        min_value=20.00, 
        max_value=120.00, 
        value=75.00, 
        step=0.05,
        help="Piyasa kapalıyken robotun tepkilerini test etmek için fiyatı sağa sola kaydırın."
    )
    # Yeni fiyatı tüm motorlara gönder
    if hasattr(model_1, 'set_mock_price'): model_1.set_mock_price(mock_price)
    if hasattr(model_2, 'set_mock_price'): model_2.set_mock_price(mock_price)
    if hasattr(model_3, 'set_mock_price'): model_3.set_mock_price(mock_price) # 👈 BARKOD: Model 3'e sahte fiyat eklendi
    st.divider()
# ==========================================