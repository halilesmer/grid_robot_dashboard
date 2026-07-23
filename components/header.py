# components/header.py
import streamlit as st

def render_header(symbol: str, broker: str, is_market_open: bool):
    """
    Header & Status Bar Bileşeni
    """
    st.title("🤖 USOUSD Dinamik Grid Robot Paneli")
    st.caption("v2.2 - Modüler Streamlit Kontrol Paneli")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Sembol", value=symbol)
    with col2:
        st.metric(label="Sunucu", value=broker)
    with col3:
        status_color = "🟢 Açık" if is_market_open else "🔴 Kapalı"
        st.metric(label="Piyasa Durumu", value=status_color)
        
    st.divider()