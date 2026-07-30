# src/components/chart_viewer.py
import streamlit as st
import plotly.graph_objects as go


def render_chart(current_price: float, current_settings: dict, model_name: str):
    """
    Çizgi grafik ve grid bölgelerini doğrudan JSON ayarlarından (current_settings) okuyarak çizer.
    Arka plandaki robottan tamamen bağımsız ve güvenlidir.
    """
    st.markdown("### 📈 Canlı Fiyat ve Grid Bölgeleri")

    fig = go.Figure()

    # Fiyat çizgisi (Simüle edilmiş veya anlık fiyat)
    fig.add_trace(
        go.Scatter(
            x=[1, 2, 3],  # Görsel amaçlı kısa bir X ekseni
            y=[current_price, current_price, current_price],
            mode="lines+markers",
            name="Anlık Fiyat",
            line=dict(color="#00b4d8", width=3),
            marker=dict(size=8, color="white"),
        )
    )

    # ==========================================
    # MODEL 1 ÇİZİMLERİ (Statik Grid Çizgileri)
    # ==========================================
    if model_name == "Model 1":
        grid_step = float(current_settings.get("GRID_STEP", 0.05))
        levels_above = int(current_settings.get("LEVELS_ABOVE", 5))
        levels_below = int(current_settings.get("LEVELS_BELOW", 5))

        # Anlık fiyatı merkez alarak sanal gridleri çiziyoruz
        for i in range(1, levels_above + 1):
            level_price = current_price + (i * grid_step)
            fig.add_hline(
                y=level_price, line_dash="dash", line_color="#4ade80", opacity=0.6
            )

        for i in range(1, levels_below + 1):
            level_price = current_price - (i * grid_step)
            fig.add_hline(
                y=level_price, line_dash="dash", line_color="#f87171", opacity=0.6
            )

    # ==========================================
    # MODEL 2 ÇİZİMLERİ (Dinamik Bölgeler / Zones)
    # ==========================================
    elif model_name == "Model 2":
        zones = current_settings.get("ZONES", [])
        for idx, zone in enumerate(zones):
            min_p = float(zone.get("min_price", 0.0))
            max_p = float(zone.get("max_price", 0.0))

            # Belirlenmiş bölgeyi (Zone) grafikte turuncu bir alan olarak boya
            if min_p > 0 and max_p > 0:
                fig.add_hrect(
                    y0=min_p,
                    y1=max_p,
                    fillcolor="rgba(251, 146, 60, 0.2)",
                    layer="below",
                    line_width=2,
                    line_color="#fb923c",
                    annotation_text=f"Bölge {idx+1}",
                    annotation_position="top right",
                    annotation_font_color="#fb923c",
                )

    # Grafik Ayarları
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis_title="Fiyat (USOUSD)",
        xaxis_title="Zaman (Simüle)",
        showlegend=False,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0.1)",
    )

    st.plotly_chart(fig, width="stretch")
