# components/metrics.py
import streamlit as st

def render_metrics(profit: float, open_positions: int, pending_orders: int, current_price: float):
    """
    Kompakt Canlı Piyasa ve Hesap Durumu Bileşeni
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Fiyat", value=f"${current_price:.2f}")
        
    with col2:
        st.metric(
            label="Anlık Kâr/Zarar", 
            value=f"${profit:.2f}", 
            delta=f"{profit:.2f}$" if profit != 0 else None
        )
        
    with col3:
        st.metric(label="Açık Pozisyon", value=open_positions)
        
    with col4:
        st.metric(label="Bekleyen Emir", value=pending_orders)