# src/components/account_selector.py
import streamlit as st
import json
import os

ACCOUNTS_FILE = "configs/accounts.json"


def load_accounts():
    """configs/accounts.json dosyasından hesap listesini okur ve formatı güvenceye alır."""
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("accounts", [])
            return []
    except Exception as e:
        st.error(f"Hesap dosyası okunamadı: {e}")
        return []


def render_account_selector():
    """Ana ekran için hibrit (Button + Selectbox) hesap seçim menüsünü oluşturur."""
    accounts = load_accounts()

    if not accounts:
        st.warning("Hesap bulunamadı! configs/accounts.json eksik.")
        st.session_state.selected_account = None
        return None
    # ==========================================
    # YENİ: ÇİFT LOGİN (DUPLICATE) KONTROLÜ
    # ==========================================
    login_ids = [str(acc.get("login")) for acc in accounts if acc.get("login")]
    duplicate_logins = set([x for x in login_ids if login_ids.count(x) > 1])

    if duplicate_logins:
        dup_str = ", ".join(duplicate_logins)
        st.error(
            f"🚨 **DİKKAT - AYNI HESAP ID'Sİ TEKRARLIYOR:** `accounts.json` dosyasında şu Login ID'leri birden fazla kez kullanılmış: **{dup_str}**.\n\n"
            "Lütfen dosyayı kontrol edip mükerrer (çift) kayıtları silin veya ID'leri düzeltin!"
        )

    if (
        "selected_account" not in st.session_state
        or st.session_state.selected_account is None
    ):
        st.session_state.selected_account = accounts[0]

    active_account = st.session_state.selected_account
    active_login = active_account.get("login")

    # Sicherer Fallback für Namen und Typ
    active_name = active_account.get(
        "account_name", active_account.get("name", "Bilinmeyen Hesap")
    )
    active_type = active_account.get("env_type", active_account.get("type", "DEMO"))

    is_running = st.session_state.get("robot_running", False)

    st.markdown("### 🏢 MT5 Hesap Seçimi")

    # 1. Görsel Güvenlik Geri Bildirimi
    if is_running:
        if active_type == "LIVE":
            st.markdown(
                f'<div class="status-container"><div class="pulsing-red"></div> <span>🚨 DİKKAT: CANLI HESAPTA İŞLEM YAPILIYOR [ {active_name} ]</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="status-container"><div class="pulsing-green"></div> <span>🟢 TEST ORTAMI AKTİF [ {active_name} ]</span></div>',
                unsafe_allow_html=True,
            )
    else:
        if active_type == "LIVE":
            st.error(f"🔴 SEÇİLİ HESAP: CANLI HESAP! (ID: {active_login})")
        else:
            st.success(f"🟢 Seçili Hesap: Test Ortamı (ID: {active_login})")

    # 2. Hibrit Buton Menüsü
    MAX_BUTTONS = 4
    num_accounts = len(accounts)
    num_cols = min(num_accounts, MAX_BUTTONS) + (1 if num_accounts > MAX_BUTTONS else 0)
    cols = st.columns(num_cols)

    for i, acc in enumerate(accounts[:MAX_BUTTONS]):
        acc_type = acc.get("env_type", acc.get("type", "DEMO"))
        acc_name = acc.get("account_name", acc.get("name", "Bilinmeyen Hesap"))

        btn_icon = "🔴" if acc_type == "LIVE" else "🧪"
        btn_label = f"{btn_icon} {acc_name.split(' ')[0]}"  # İlk kelime
        is_active = acc["login"] == active_login

        if cols[i].button(
            btn_label,
            key=f"btn_{i}_{acc['login']}",
            type="primary" if is_active else "secondary",
        ):
            if is_running:
                st.toast(
                    "⚠️ Lütfen hesap değiştirmeden önce robotu durdurun!", icon="🚫"
                )
            else:
                st.session_state.selected_account = acc
                st.rerun()

    # Dropdown für restliche Konten
    if num_accounts > MAX_BUTTONS:
        extra_accounts = accounts[MAX_BUTTONS:]
        extra_options = {}
        for a in extra_accounts:
            a_type = a.get("env_type", a.get("type", "DEMO"))
            a_name = a.get("account_name", a.get("name", "Bilinmeyen Hesap"))
            extra_options[f"{'🔴' if a_type=='LIVE' else '🧪'} {a_name}"] = a

        selected_extra_name = cols[MAX_BUTTONS].selectbox(
            "Diğer:",
            options=["Diğer Hesaplar..."] + list(extra_options.keys()),
            label_visibility="collapsed",
        )

        if selected_extra_name != "Diğer Hesaplar...":
            selected_acc = extra_options[selected_extra_name]
            if selected_acc["login"] != active_login:
                if is_running:
                    st.toast(
                        "⚠️ Lütfen hesap değiştirmeden önce robotu durdurun!", icon="🚫"
                    )
                else:
                    st.session_state.selected_account = selected_acc
                    st.rerun()

    return st.session_state.selected_account
