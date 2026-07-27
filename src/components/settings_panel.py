# components/settings_panel.py
import streamlit as st
import uuid
from src.constants.tooltips import SETTINGS_TOOLTIPS
# Yeni model 3 bileşenimizi içeri alıyoruz:
from src.components.model3_settings import render_model_3_settings 

def render_settings_panel(current_settings, model_name="Model 1"):
    """
    JSON'dan beslenen Grid ve Risk Ayarları Kompakt Form Bileşeni
    """
    st.markdown(f"##### ⚙️ {model_name} Parametreleri")
    
    if model_name == "Model 1":
        return render_model_1_settings(current_settings)
    elif model_name == "Model 2":
        return render_model_2_settings(current_settings)
    elif model_name == "Model 3":
        # Yeni Model 3 fonksiyonumuzu çağırıyoruz
        return render_model_3_settings(current_settings)
    
    return None

# ... (Aşağıda render_model_1_settings ve render_model_2_settings fonksiyonlarınız eskisi gibi kalacak)

def render_model_1_settings(current_settings):
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

def render_model_2_settings(current_settings):
    # Model 2 dynamic zones list in session state
    if "model2_zones" not in st.session_state:
        st.session_state.model2_zones = current_settings.get("ZONES", [])

    with st.form("settings_form_m2"):
        st.markdown("###### ⚖️ Temel İşlem Ayarları")
        t_col1, t_col2, t_col3 = st.columns([1, 1, 1])
        with t_col1:
            order_type_val = current_settings.get("ORDER_TYPE", "BUY")
            order_type = st.selectbox("İşlem Yönü", options=["BUY", "SELL"], index=0 if order_type_val == "BUY" else 1)
        with t_col2:
            symbol = st.text_input("Sembol", value=current_settings.get("SYMBOL", "USOUSD"))
        with t_col3:
            loop_interval = st.number_input("Kontrol Sıklığı (Sn)", value=float(current_settings.get("LOOP_INTERVAL_SECONDS", 1.0)), step=0.1)

        st.markdown("---")
        st.markdown("###### 🎯 Dinamik Bölgeler (Zones)")

        updated_zones = []
        for idx, zone in enumerate(st.session_state.model2_zones):
            st.markdown(f"**Bölge {idx + 1}**")
            # Kolon yapısına Stop Loss eklendi (8 kolon)
            zc1, zc2, zc3, zc4, zc5, zc6, zc7, zc8 = st.columns([1, 1, 1, 1, 1, 1, 1.2, 0.5])
            with zc1:
                z_min = st.number_input(f"Alt Sınır##{idx}", value=float(zone.get("min_price", 0.0)), step=0.1)
            with zc2:
                z_max = st.number_input(f"Üst Sınır##{idx}", value=float(zone.get("max_price", 0.0)), step=0.1)
            with zc3:
                z_grid = st.number_input(f"Grid##{idx}", value=float(zone.get("grid_step", 0.05)), step=0.01)
            with zc4:
                z_lot = st.number_input(f"Lot##{idx}", value=float(zone.get("lot_size", 0.01)), step=0.01)
            with zc5:
                z_tp = st.number_input(f"TP##{idx}", value=float(zone.get("take_profit", 0.05)), step=0.01)
            with zc6:
                z_sl = st.number_input(f"Stop Loss##{idx}", value=float(zone.get("stop_loss", 0.0)), step=0.01)
            with zc7:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                z_clear = st.checkbox(f"Çıkışta Temizle##{idx}", value=bool(zone.get("clear_on_exit", True)))
            with zc8:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                delete_btn = st.checkbox(f"🗑️##del_{idx}")
            
            if not delete_btn:
                updated_zones.append({
                    "min_price": z_min,
                    "max_price": z_max,
                    "grid_step": z_grid,
                    "lot_size": z_lot,
                    "take_profit": z_tp,
                    "stop_loss": z_sl,
                    "clear_on_exit": z_clear
                })

        st.session_state.model2_zones = updated_zones

        col_b1, col_b2 = st.columns([1, 1])
        with col_b1:
            add_zone = st.form_submit_button("➕ Yeni Bölge Ekle")
        with col_b2:
            submitted = st.form_submit_button("💾 Ayarları Güncelle")
            
        if add_zone:
            st.session_state.model2_zones.append({
                "min_price": 90.0,
                "max_price": 100.0,
                "grid_step": 0.05,
                "lot_size": 0.01,
                "take_profit": 0.05,
                "stop_loss": 0.0,
                "clear_on_exit": True
            })
            st.rerun()

        if submitted:
            # Artık sadece gereken veriler dönüyor
            return {
                "ORDER_TYPE": order_type,
                "SYMBOL": symbol,
                "LOOP_INTERVAL_SECONDS": loop_interval,
                "ZONES": updated_zones
            }

    return None