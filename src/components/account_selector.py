import streamlit as st
import json
import os

ACCOUNTS_FILE = "configs/accounts.json"


def load_accounts():
    """configs/accounts.json dosyasından hesap listesini okur."""
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Hesap dosyası okunamadı: {e}")
        return []


def render_account_selector():
    """Ana ekran için hesap seçim kutusunu oluşturur."""
    accounts = load_accounts()

    if not accounts:
        st.warning("Hesap bulunamadı! configs/accounts.json eksik.")
        st.session_state.selected_account = None
        return None

    # Menüde göstermek için hesap isimlerini hazırlayalım
    account_options = {
        f"{acc['account_name']} [{acc['env_type']}]": acc for acc in accounts
    }

    st.markdown("### 🏦 MT5 Hesap Seçimi")

    # Kullanıcının seçimi (sidebar kelimesi kaldırıldı)
    selected_name = st.selectbox(
        "İşlem Yapılacak Hesap:",
        options=list(account_options.keys()),
        label_visibility="collapsed",  # Başlığı gizleyip daha şık yaptık
    )

    selected_account = account_options[selected_name]
    st.session_state.selected_account = selected_account

    # Görsel Güvenlik Geri Bildirimi
    if selected_account["env_type"] == "LIVE":
        st.error(f"🔴 DİKKAT: CANLI HESAP! (ID: {selected_account['login']})")
    else:
        st.success(f"🟢 Test Ortamı (ID: {selected_account['login']})")

    return selected_account
