# components/controls.py
import streamlit as st
from src.constants.tooltips import SETTINGS_TOOLTIPS


def render_controls(
    is_running: bool, account_id: str = "default", current_model: str = "Model 1"
):
    """
    Dinamik Tek Butonlu Kontrol Paneli, Anında Açılan Tooltip ve Motor Seçimi (%100 Multi-Account Uyumlu)
    """
    st.markdown("### 🎮 Robot Kontrol Paneli")

    col1, col2, col3 = st.columns([2.5, 0.8, 2.5], vertical_alignment="center")

    with col1:
        models = ["Model 1", "Model 2", "Model 3"]

        # Finde heraus, an welcher Position (Index) das aktuelle Modell steht
        try:
            default_index = models.index(current_model)
        except ValueError:
            default_index = 0

        selected_model = st.selectbox(
            "⚙️ Motor Seçimi",
            options=models,
            index=default_index,  # NEU: Wir erzwingen die Auswahl per Index!
            disabled=is_running,
            label_visibility="collapsed",
            key=f"selectbox_motor_{account_id}",
        )

    with col2:
        # Tooltip metinleri artık dışarıdan gelen selected_model üzerinden besleniyor.
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
        # --- BUTON GÜNCELLEMESİ BURADA ---
        button_label = (
            "🛑 Ana Motoru Durdur" if is_running else "🔌 Ana Motoru Çalıştır"
        )
        button_type = "secondary" if is_running else "primary"
        button_help = (
            "Arka plan motorunu tamamen kapatır. Açık pozisyonlara dokunulmaz."
            if is_running
            else "MT5 ile iletişim kuran arka plan ticaret motorunu başlatır."
        )

        toggle_btn = st.button(
            button_label,
            type=button_type,
            use_container_width=True,
            help=button_help,
            key=f"toggle_btn_{account_id}",
        )

    action = "TOGGLE" if toggle_btn else None
    return action, selected_model
