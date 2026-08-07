# src/components/metrics.py
import streamlit as st


def render_global_metrics(profit: float, current_price: float):
    """Sadece Fiyat ve Kâr/Zarar gösteren global özet barı"""
    c1, c2 = st.columns(2)
    with c1:
        st.metric(label="Anlık Fiyat", value=f"${current_price:.2f}")
    with c2:
        st.metric(
            label="Toplam Kâr/Zarar",
            value=f"${profit:.2f}",
            delta=f"{profit:.2f}$" if profit != 0 else None,
        )
