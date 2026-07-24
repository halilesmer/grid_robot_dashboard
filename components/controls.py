# components/controls.py
import streamlit as st

def render_controls(is_running: bool, current_model: str = "Model 1"):
    """
    Dinamik Tek Butonlu Kontrol Paneli ve Motor Seçimi
    """
    st.subheader("🎮 Robot Kontrol Paneli")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        selected_model = st.selectbox(
            "⚙️ Motor Seçimi",
            options=["Model 1", "Model 2"],
            index=0 if current_model == "Model 1" else 1,
            disabled=is_running,
            help="Robot çalışırken motor değiştirilemez."
        )

    with col2:
        if is_running:
            st.success(f"🟢 ROBOT AKTİF ({current_model})")
        else:
            st.error(f"🔴 ROBOT PASİF ({current_model})")

    with col3:
        button_label = "⏹️ Robotu Durdur" if is_running else "▶️ Robotu Başlat"
        button_type = "secondary" if is_running else "primary"
        
        toggle_btn = st.button(button_label, type=button_type, use_container_width=True)

    st.divider()
    
    action = "TOGGLE" if toggle_btn else None
    return action, selected_model