# styles/custom_css.py
import streamlit as st

def apply_custom_css():
    """
    Streamlit arayüzünü son derece kompakt, derli toplu ve modern yapan CSS
    """
    st.markdown("""
        <style>
        /* Sayfa genişliğini 1200px'e sabitleme ve ortalama */
        .block-container {
            max-width: 1200px !important;
            margin-left: auto !important;
            margin-right: auto !important;
            padding-top: 1.2rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }

        /* Dikey eleman aralıklarını (gap) sıkılaştırma */
        div[data-testid="stVerticalBlock"] > div {
            gap: 0.4rem !important;
        }

        /* Divider (Çizgi) boşluklarını azaltma */
        hr {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }

        /* Form elemanları ve etiket aralıklarını küçültme */
        div[data-testid="stForm"] {
            padding: 0.8rem 1rem !important;
            border-radius: 8px !important;
        }

        .stNumberInput label, .stSelectbox label {
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            margin-bottom: 2px !important;
        }

        .stNumberInput input {
            padding: 4px 8px !important;
            height: 36px !important;
        }

        /* stMetric kartlarını daha küçük ve derli toplu yapma */
        div[data-testid="stMetric"] {
            padding: 4px 8px !important;
        }

        div[data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
            font-weight: 500 !important;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.25rem !important;
            font-weight: 700 !important;
        }

        /* Tooltip (Help Popover) metinlerinin boyutunu düzenleme */
        div[data-baseweb="popover"] p, 
        div[data-baseweb="tooltip"] div,
        .stTooltipContent {
            font-size: 1rem !important;
            line-height: 1.4 !important;
        }
        
        div[data-testid="stTooltipIcon"] svg {
            width: 15px !important;
            height: 15px !important;
        }
        </style>
    """, unsafe_allow_html=True)