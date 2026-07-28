# components/header.py
import streamlit as st

def render_header(symbol: str, broker: str, is_market_open: bool):
    """
    Header & Status Bar Kompakt Bileşeni
    """
    status = "🟢 Açık" if is_market_open else "🔴 Kapalı"
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### 🤖 Grid Robot Dashboard <span style='font-size: 0.8rem; color: #888;'>v2</span>", unsafe_allow_html=True)
    with col2:
        st.markdown(
            f"<div style='text-align: right; font-size: 0.9rem; font-weight: 500; margin-top: 5px;'>"
            f"<b>{symbol}</b> | {broker} | <span>{status}</span>"
            f"</div>", 
            unsafe_allow_html=True
        )