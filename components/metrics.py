# components/metrics.py
import streamlit as st

def render_metrics(profit: float, open_positions: int, pending_orders: int, current_price: float):
    """
    React Component Mantığı: Canlı Bakiye ve İşlem Metrikleri
    """
    st.subheader("📊 Canlı Piyasa ve Hesap Durumu")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Anlık Piyasa Fiyatı", value=f"${current_price:.2f}")
        
    with col2:
        # Kâr pozitifse yeşil, negatifse kırmızı gösterir
        st.metric(
            label="Toplam Anlık Kâr/Zarar", 
            value=f"${profit:.2f}", 
            delta=f"{profit:.2f}$"
        )
        
    with col3:
        st.metric(label="Açık Pozisyonlar", value=open_positions)
        
    with col4:
        st.metric(label="Bekleyen Emirler", value=pending_orders)
        
    st.divider()