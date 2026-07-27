# components/chart_viewer.py
import streamlit as st
import plotly.graph_objects as go
from collections import deque
import datetime

def render_chart(current_price, bot_engine=None):
    """
    Canlı fiyat akışını ve botun aktif emir/pozisyon seviyelerini çizen grafik bileşeni.
    """
    # Fiyat geçmişini tutmak için session state kullanalım (Son 100 veri noktası)
    if "price_history_times" not in st.session_state:
        st.session_state.price_history_times = deque(maxlen=100)
        st.session_state.price_history_values = deque(maxlen=100)

    # Geçerli bir fiyat varsa listeye ekle
    if current_price and current_price > 0:
        st.session_state.price_history_times.append(datetime.datetime.now())
        st.session_state.price_history_values.append(current_price)

    if not st.session_state.price_history_values:
        st.info("📊 Grafik için fiyat verisi bekleniyor...")
        return

    # Grafiği Oluştur
    fig = go.Figure()

    # 1. Fiyat Çizgisi
    fig.add_trace(go.Scatter(
        x=list(st.session_state.price_history_times),
        y=list(st.session_state.price_history_values),
        mode='lines',
        name='Fiyat',
        line=dict(color='#29b6f6', width=2)
    ))

    # 2. İşlem ve Emir Seviyelerini Çiz (Bot motoru aktifse)
    if bot_engine:
        try:
            # Model 2 ve Model 3'teki farklı fonksiyon isimlerini dinamik yakala
            orders = []
            positions = []

            if hasattr(bot_engine, 'get_all_robot_orders'):
                orders = bot_engine.get_all_robot_orders() or []
            elif hasattr(bot_engine, 'get_orders'):
                orders = bot_engine.get_orders() or []

            if hasattr(bot_engine, 'get_all_robot_positions'):
                positions = bot_engine.get_all_robot_positions() or []
            elif hasattr(bot_engine, 'get_positions'):
                positions = bot_engine.get_positions() or []

            # Bekleyen Emirleri Çiz (Gri Kesik Çizgiler)
            for o in orders:
                price = getattr(o, 'price_open', 0.0)
                if price > 0:
                    fig.add_hline(
                        y=price, line_dash="dot", line_color="gray", 
                        annotation_text="Bekleyen", opacity=0.5, line_width=1
                    )

            # Açık Pozisyonları Çiz (Yeşil/Kırmızı Düz Çizgiler)
            for p in positions:
                price = getattr(p, 'price_open', 0.0)
                p_type = getattr(p, 'type', 0) # 0: BUY, 1: SELL (MT5 Standart)

                color = "#00e676" if p_type == 0 else "#ff5252"
                label = "BUY Pos" if p_type == 0 else "SELL Pos"

                if price > 0:
                    fig.add_hline(
                        y=price, line_width=2, line_color=color, 
                        annotation_text=label, opacity=0.8
                    )
        except Exception:
            pass # MT5 bağlantısı hatası grafiği çökertmesin

    # Grafik Tasarım Ayarları (Karanlık temaya uygun)
    fig.update_layout(
        title="📈 Canlı USOUSD Fiyat ve Ağ (Grid) Monitörü",
        xaxis_title="Zaman",
        yaxis_title="Fiyat",
        height=450,
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#cfd8dc'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickformat=".2f")
    )

    st.plotly_chart(fig, width="stretch")