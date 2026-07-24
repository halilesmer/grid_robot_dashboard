# components/settings_panel.py
import streamlit as st
from constants.tooltips import SETTINGS_TOOLTIPS

def render_settings_panel(current_settings):
    """
    JSON'dan beslenen Grid ve Risk Ayarları Kompakt Form Bileşeni
    """
    st.markdown("##### ⚙️ Robot Parametreleri")
    
    with st.form("settings_form"):
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            grid_step = st.number_input(
                "Grid Adımı (GRID_STEP)", 
                value=float(current_settings["GRID_STEP"]), step=0.01, format="%.2f", 
                help=SETTINGS_TOOLTIPS["GRID_STEP"]
            )
            take_profit = st.number_input(
                "Kâr Al (TAKE_PROFIT)", 
                value=float(current_settings["TAKE_PROFIT"]), step=0.01, format="%.2f", 
                help=SETTINGS_TOOLTIPS["TAKE_PROFIT"]
            )

        with col2:
            levels_below = st.number_input(
                "Alt Seviye (LEVELS_BELOW)", 
                value=int(current_settings["LEVELS_BELOW"]), step=1, 
                help=SETTINGS_TOOLTIPS["LEVELS_BELOW"]
            )
            levels_above = st.number_input(
                "Üst Seviye (LEVELS_ABOVE)", 
                value=int(current_settings["LEVELS_ABOVE"]), step=1, 
                help=SETTINGS_TOOLTIPS["LEVELS_ABOVE"]
            )

        with col3:
            default_lot = st.number_input(
                "Varsayılan Lot (DEFAULT_LOT)", 
                value=float(current_settings["DEFAULT_LOT"]), step=0.01, format="%.2f", 
                help=SETTINGS_TOOLTIPS["DEFAULT_LOT"]
            )
            max_positions = st.number_input(
                "Maks. Pozisyon (MAX_POSITIONS)", 
                value=int(current_settings["MAX_OPEN_POSITIONS"]), step=1, 
                help=SETTINGS_TOOLTIPS["MAX_OPEN_POSITIONS"]
            )

        with col4:
            min_price = st.number_input(
                "Taban Fiyat (MIN_PRICE)", 
                value=float(current_settings["MIN_PRICE_LIMIT"]), step=1.0, 
                help=SETTINGS_TOOLTIPS["MIN_PRICE_LIMIT"]
            )
            max_price = st.number_input(
                "Tavan Fiyat (MAX_PRICE)", 
                value=float(current_settings["MAX_PRICE_LIMIT"]), step=1.0, 
                help=SETTINGS_TOOLTIPS["MAX_PRICE_LIMIT"]
            )

        col_b1, col_b2 = st.columns([2, 1])
        with col_b1:
            loop_interval = st.number_input(
                "Kontrol Sıklığı Saniye (LOOP_INTERVAL)", 
                value=float(current_settings.get("LOOP_INTERVAL_SECONDS", 1.0)), step=0.1, format="%.1f",
                help=SETTINGS_TOOLTIPS["LOOP_INTERVAL_SECONDS"]
            )

        with col_b2:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "💾 Ayarları Güncelle", 
                use_container_width=True,
                help="Ayarları anında sisteme kaydeder."
            )
                
        if submitted:
            return {
                "GRID_STEP": grid_step,
                "TAKE_PROFIT": take_profit,
                "LEVELS_BELOW": levels_below,
                "LEVELS_ABOVE": levels_above,
                "DEFAULT_LOT": default_lot,
                "MAX_OPEN_POSITIONS": max_positions,
                "MAX_PRICE_LIMIT": max_price,
                "MIN_PRICE_LIMIT": min_price,
                "LOOP_INTERVAL_SECONDS": loop_interval
            }
            
    return None