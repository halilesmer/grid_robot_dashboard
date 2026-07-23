# styles/custom_css.py
import streamlit as st

def apply_custom_css():
    """
    Streamlit arayüzü ve Tooltip (Bilgi Baloncuğu) font boyutunu büyüten CSS
    """
    st.markdown("""
        <style>
        /* Tooltip (Help Popover) metinlerinin boyutunu en az 4 numara büyütür (14px -> 18px / 1.15rem) */
        div[data-baseweb="popover"] p, 
        div[data-baseweb="tooltip"] div,
        .stTooltipContent {
            font-size: 1.15rem !important;
            line-height: 1.5 !important;
        }
        
        /* Tooltip simgesinin (?) kendisini de biraz daha belirginleştirir */
        div[data-testid="stTooltipIcon"] svg {
            width: 18px !important;
            height: 18px !important;
        }
        </style>
    """, unsafe_allow_html=True)