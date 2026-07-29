# components/controls.py
import streamlit as st
from src.constants.tooltips import SETTINGS_TOOLTIPS


def render_controls(is_running: bool, account_id: str = "default"):
    """
    Dinamik Tek Butonlu Kontrol Paneli, Anında Açılan Tooltip ve Motor Seçimi (%100 Multi-Account Uyumlu)
    """
    st.markdown("### 🎮 Robot Kontrol Paneli")

    col1, col2, col3 = st.columns([2.5, 0.8, 2.5], vertical_alignment="center")

    # ==========================================
    # KUSURSUZ İZOLASYON: Hesaba özel hafıza!
    # ==========================================
    model_key = f"selected_model_{account_id}"

    # Eğer bu hesap için henüz bir model seçilmediyse varsayılanı Model 1 yap
    if model_key not in st.session_state:
        st.session_state[model_key] = "Model 1"

    with col1:
        models = ["Model 1", "Model 2", "Model 3"]
        selected_model = st.selectbox(
            "⚙️ Motor Seçimi",
            options=models,
            disabled=is_running,
            label_visibility="collapsed",
            key=model_key,  # Streamlit seçimi otomatik olarak izole edilen bu key'de tutacak!
        )

    with col2:
        # Tooltip metinleri artık dışarıdan gelen current_model'den değil,
        # doğrudan bu hesaba ait olan 'selected_model' üzerinden besleniyor.
        if is_running:
            status_text = SETTINGS_TOOLTIPS["ROBOT_ACTIVE"].format(model=selected_model)
            icon = "🟢"
        else:
            status_text = SETTINGS_TOOLTIPS["ROBOT_PASSIVE"].format(
                model=selected_model
            )
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

    with col3:
        button_label = "⏹️ Durdur" if is_running else "▶️ Başlat"
        button_type = "secondary" if is_running else "primary"

        toggle_btn = st.button(
            button_label,
            type=button_type,
            use_container_width=True,
            key=f"toggle_btn_{account_id}",  # Başlat/Durdur butonu %100 izole edildi
        )

    action = "TOGGLE" if toggle_btn else None
    return action, selected_model
