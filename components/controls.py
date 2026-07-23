# components/controls.py
import streamlit as st

def render_controls(is_running: bool):
    """
    Dinamik Tek Butonlu Kontrol Paneli
    """
    st.subheader("🎮 Robot Kontrol Paneli")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if is_running:
            st.success("🟢 ROBOT AKTİF (Çalışıyor)")
        else:
            st.error("🔴 ROBOT PASİF (Durduruldu)")

    with col2:
        button_label = "⏹️ Robotu Durdur" if is_running else "▶️ Robotu Başlat"
        button_type = "secondary" if is_running else "primary"
        
        toggle_btn = st.button(button_label, type=button_type, use_container_width=True)

    st.divider()
    
    if toggle_btn:
        return "TOGGLE"
        
    return None