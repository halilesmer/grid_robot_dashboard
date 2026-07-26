# app.py
import streamlit as st
import threading
import time  
import platform 
from components.chart_viewer import render_chart

from components.header import render_header
from components.settings_panel import render_settings_panel
from components.metrics import render_metrics
from components.controls import render_controls
from components.log_viewer import render_log_viewer 
from styles.custom_css import apply_custom_css
from utils.config import load_settings, save_settings
import core.model_1 as model_1
import core.model_2 as model_2
import core.model_3 as model_3 

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

if st.session_state.selected_model == "Model 1":
    bot_engine = model_1
elif st.session_state.selected_model == "Model 2":
    bot_engine = model_2
else:
    bot_engine = model_3

current_settings = load_settings(st.session_state.selected_model)

render_header(symbol="USOUSD", broker="Eightcap-Demo", is_market_open=True)

if st.session_state.robot_running:
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

# ==========================================
# 1. ÖNCE SİMÜLATÖRÜ OKU (Eğer Mac ise)
# ==========================================
current_active_price = live_data.get("current_price", 0.0)

if platform.system() != "Windows":
    st.warning("💻 Mac Test Modu Aktif - Fiyat Simülatörü")
    mock_price = st.slider(
        "Canlı Fiyatı Belirle (USOUSD)", 
        min_value=50.0, max_value=150.0, value=75.0, step=0.10
    )
    current_active_price = mock_price 
    
    # BARKOD: Kaydırıcıdaki fiyatı robotun beynine zorla enjekte et!
    bot_engine.SIMULATED_PRICE = mock_price

# ==========================================
# 2. SONRA GRAFİĞİ VE LOGLARI ÇİZ
# ==========================================
col_chart, col_log = st.columns([2, 1])

with col_chart:
    render_chart(current_active_price, bot_engine)

with col_log:
    render_log_viewer()

# ==========================================
# CANLI VERİ AKIŞI (AUTO-REFRESH) DÖNGÜSÜ
# ==========================================
if st.session_state.robot_running:
    time.sleep(1)
    st.rerun()