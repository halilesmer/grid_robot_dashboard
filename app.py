# app.py
import streamlit as st
from components.header import render_header
from components.settings_panel import render_settings_panel
from components.metrics import render_metrics
from components.controls import render_controls
from styles.custom_css import apply_custom_css  # 👈 Yeni stil modülümüz

st.set_page_config(
    page_title="Grid Robot Control",
    page_icon="🤖",
    layout="wide"
)

if "robot_running" not in st.session_state:
    st.session_state.robot_running = False

# 1. Header Bileşeni
render_header(
    symbol="USOUSD", 
    broker="Eightcap-Demo", 
    is_market_open=True
)

# 2. Canlı Metrikler Bileşeni
render_metrics(
    profit=12.50, 
    open_positions=3, 
    pending_orders=12, 
    current_price=76.45
)

# 3. Kontrol Paneli (Dinamik Tek Buton)
action = render_controls(is_running=st.session_state.robot_running)

if action == "TOGGLE":
    # Durumu tersine çevir (True ise False, False ise True yap)
    st.session_state.robot_running = not st.session_state.robot_running
    
    if st.session_state.robot_running:
        st.toast("🚀 Robot başarıyla başlatıldı!", icon="✅")
    else:
        st.toast("🛑 Robot durduruldu!", icon="⚠️")
        
    st.rerun()

# 4. Ayar Paneli Bileşeni
updated_settings = render_settings_panel()

if updated_settings:
    st.success("✅ Ayarlar başarıyla güncellendi!")
    st.json(updated_settings)