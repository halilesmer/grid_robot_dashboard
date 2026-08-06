# src/components/header.py
import streamlit as st


def render_main_title():
    """
    Sadece ana başlığı en üste ve ortaya hizalı şekilde çizer.
    """
    st.markdown(
        "<h1 style='text-align: center; font-size: 1.75rem; margin-bottom: 0; padding: 0;'>🤖 Grid Robot Dashboard <span style='font-size: 1rem; color: #888;'>v2</span></h1>",
        unsafe_allow_html=True,
    )
