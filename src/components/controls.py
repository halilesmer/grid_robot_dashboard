# components/controls.py
import streamlit as st
from src.constants.tooltips import SETTINGS_TOOLTIPS


def render_controls(is_running: bool, account_id: str = "default"):
    """
    Dinamik Tek Butonlu Kontrol Paneli ve Anında Açılan Tooltip (%100 Multi-Account Uyumlu)
    """
    st.markdown("### 🎮 Robot Kontrol Paneli")

    col_icon, col_btn = st.columns([0.15, 0.85], vertical_alignment="center")

    with col_icon:
        # Tooltip metinleri artık doğrudan Model 2'ye sabitlendi.
        if is_running:
            status_text = SETTINGS_TOOLTIPS["ROBOT_ACTIVE"].format(model="Model 2")
            icon = "🟢"
        else:
            status_text = SETTINGS_TOOLTIPS["ROBOT_PASSIVE"].format(model="Model 2")
            icon = "🔴"

        st.markdown(
            f"""
            <style>
            .instant-tooltip-container {{
                position: relative;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 38px;
                cursor: pointer;
            }}

            .instant-tooltip-container .tooltip-text {{
                visibility: hidden;
                opacity: 0;
                width: max-content;
                background-color: #1e293b;
                color: #f8fafc;
                text-align: center;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: 500;
                position: absolute;
                z-index: 999;
                bottom: 125%;
                left: 50%;
                transform: translateX(-50%);
                box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
                transition: opacity 0s; 
            }}

            .instant-tooltip-container:hover .tooltip-text {{
                visibility: visible;
                opacity: 1;
            }}
            </style>

            <div class="instant-tooltip-container">
                <span style="font-size: 20px; line-height: 1;">{icon}</span>
                <span class="tooltip-text">{status_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_btn:
        button_label = (
            "🛑 Ana Motoru Durdur" if is_running else "🔌 Ana Motoru Çalıştır"
        )
        # Motor çalışıyorsa yeşil (primary), duruyorsa gri (secondary) olsun
        button_type = "primary" if is_running else "secondary"
        button_help = (
            SETTINGS_TOOLTIPS["REMOTE_STOP_SIGNAL"]
            if is_running
            else "MT5 ile iletişim kuran arka plan ticaret motorunu başlatır. "
            + SETTINGS_TOOLTIPS["REMOTE_STOP_SIGNAL"]
        )

        toggle_btn = st.button(
            button_label,
            type=button_type,
            width="stretch",
            help=button_help,
            key=f"toggle_btn_{account_id}",
        )

        if is_running:
            st.caption(
                "📡 Unutma: Mobil MT5'te fiyatı **1$**, hacmi **0.01 lot** olan "
                "**Buy Limit** emri koyun → motor uzaktan durur."
            )

    action = "TOGGLE" if toggle_btn else None
    return action
