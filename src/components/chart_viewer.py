# src/components/chart_viewer.py
import streamlit as st
import plotly.graph_objects as go
import random


def render_chart(current_price: float, current_settings: dict, model_name: str):
    """
    Çizgi grafik ve grid bölgelerini doğrudan JSON ayarlarından (current_settings) okuyarak çizer.
    TradingView Dark Theme stili ve HAFIZALI (iz bırakan) gerçek zaman serisi mantığı uygulanmıştır.
    """
    st.markdown("### 📈 Canlı Fiyat ve Grid Bölgeleri")

    fig = go.Figure()

    # ==========================================
    # 1. HAFIZALI GEÇMİŞ VERİ YÖNETİMİ (Gerçekçi Chart Hareketi)
    # ==========================================
    # Eğer grafiğin hafızası henüz yoksa (ilk açılış)
    if "chart_price_history" not in st.session_state:
        # Ekran boş görünmesin diye geriye dönük 100 mumluk bir sahte dalga oluşturuyoruz
        history_len = 100
        random.seed(42)
        prices = []
        sim = current_price - 2.0
        for _ in range(history_len - 1):
            sim += random.uniform(-0.05, 0.05)
            prices.append(sim)

        # Dalganın sonunu tam olarak şu anki fiyata pürüzsüz bağlamak için hizalıyoruz
        offset = current_price - prices[-1]
        st.session_state["chart_price_history"] = [p + offset for p in prices]

    # YENİ FİYATI HAFIZAYA EKLE (İz bırakma mantığı burası)
    # Slider'dan veya canlı veriden gelen fiyat geçmişin ucuna eklenir, eski noktalar YERİNDE KALIR.
    st.session_state["chart_price_history"].append(current_price)

    # Bellek şişmesin diye sadece son 150 hareketi (mumu) ekranda tutuyoruz
    if len(st.session_state["chart_price_history"]) > 150:
        st.session_state["chart_price_history"].pop(0)

    y_data = st.session_state["chart_price_history"]
    x_data = list(range(len(y_data)))

    # ==========================================
    # 2. FİYAT ÇİZGİSİ
    # ==========================================
    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=y_data,
            mode="lines",
            name="Anlık Fiyat",
            line=dict(color="#d1d4dc", width=1.5),
            hoverinfo="y",
        )
    )

    # 3. ANLIK FİYAT YATAY ÇİZGİSİ (En sağdaki hedef etiketi)
    fig.add_hline(
        y=current_price,
        line_dash="dash",
        line_color="#a3a3a3",
        line_width=1,
        annotation_text=f"{current_price:.2f}",
        annotation_position="right",
        annotation_font=dict(color="white", size=12),
        annotation_bgcolor="#363a45",
    )

    # ==========================================
    # MODEL 1 ÇİZİMLERİ (Statik Grid Çizgileri)
    # ==========================================
    if model_name == "Model 1":
        grid_step = float(current_settings.get("GRID_STEP", 0.05))
        levels_above = int(current_settings.get("LEVELS_ABOVE", 5))
        levels_below = int(current_settings.get("LEVELS_BELOW", 5))

        for i in range(1, levels_above + 1):
            level_price = current_price + (i * grid_step)
            fig.add_hline(
                y=level_price, line_dash="dot", line_color="#4ade80", opacity=0.4
            )

        for i in range(1, levels_below + 1):
            level_price = current_price - (i * grid_step)
            fig.add_hline(
                y=level_price, line_dash="dot", line_color="#f87171", opacity=0.4
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
                    fillcolor="rgba(251, 146, 60, 0.1)",
                    layer="below",
                    line_width=1,
                    line_color="rgba(251, 146, 60, 0.5)",
                    annotation_text=f"Bölge {idx+1}",
                    annotation_position="top left",
                    annotation_font_color="rgba(251, 146, 60, 0.8)",
                )

    # ==========================================
    # TRADINGVIEW STİLİ GRAFİK AYARLARI
    # ==========================================
    fig.add_annotation(
        text="USOUSD 30",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.55,
        showarrow=False,
        font=dict(size=60, color="rgba(255, 255, 255, 0.04)", family="Arial"),
        align="center",
    )
    fig.add_annotation(
        text="Spot WTI Crude Oil",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.45,
        showarrow=False,
        font=dict(size=30, color="rgba(255, 255, 255, 0.04)", family="Arial"),
        align="center",
    )

    fig.update_layout(
        height=450,
        margin=dict(l=10, r=60, t=10, b=10),
        showlegend=False,
        template="plotly_dark",
        paper_bgcolor="#131722",
        plot_bgcolor="#131722",
        hovermode="x unified",
        xaxis=dict(
            showgrid=True,
            gridcolor="#2B2B43",
            zeroline=False,
            showticklabels=False,
            spikemode="across",
            spikesnap="cursor",
            showline=False,
            spikedash="dash",
            spikecolor="#787B86",
            spikethickness=1,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#2B2B43",
            zeroline=False,
            side="right",
            tickfont=dict(color="#787B86"),
            spikemode="across",
            spikesnap="cursor",
            showline=False,
            spikedash="dash",
            spikecolor="#787B86",
            spikethickness=1,
            tickformat=".2f",
        ),
    )

    st.plotly_chart(fig, use_container_width=True)
