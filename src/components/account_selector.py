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
    # ÇİFT LOGİN (DUPLICATE) KONTROLÜ
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
    # GÜVENLİK DÜZELTMESİ: KeyError riskine karşı .get() kullanıldı
    active_login = active_account.get("login", active_account.get("id", "Bilinmeyen"))

    # Güvenli Fallback (Yedek) İsim Seçimi
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
            st.error(f"🔴 SEÇİLİ HESAP: {active_name} (ID: {active_login})")
        else:
            st.success(f"🟢 Seçili Hesap: {active_name} (ID: {active_login})")

    # 2. Hibrit Buton Menüsü
    MAX_BUTTONS = 4
    num_accounts = len(accounts)
    num_cols = min(num_accounts, MAX_BUTTONS) + (1 if num_accounts > MAX_BUTTONS else 0)
    cols = st.columns(num_cols)

    for i, acc in enumerate(accounts[:MAX_BUTTONS]):
        acc_type = acc.get("env_type", acc.get("type", "DEMO"))

        # HESAP ADI VE ID'SİNİ GÜVENLİ ŞEKİLDE ÇEKİYORUZ
        acc_name = acc.get("account_name", acc.get("name", "Bilinmeyen Hesap"))
        acc_login = acc.get("login", acc.get("id", "Bilinmeyen ID"))

        btn_icon = "🔴" if acc_type == "LIVE" else "🧪"

        # Buton üzerinde ID ve İsim yan yana yazacak
        btn_label = f"{btn_icon} {acc_login} - {acc_name}"

        is_active = str(acc.get("login", acc.get("id"))) == str(active_login)

        if cols[i].button(
            btn_label,
            key=f"btn_{i}_{acc_login}",
            type="primary" if is_active else "secondary",
        ):
            st.session_state.selected_account = acc
            st.rerun()

    # Eğer 4'ten fazla hesap varsa, geri kalanı açılır menüye koy
    if num_accounts > MAX_BUTTONS:
        extra_accounts = accounts[MAX_BUTTONS:]
        extra_options = {}
        for a in extra_accounts:
            a_type = a.get("env_type", a.get("type", "DEMO"))
            a_name = a.get("account_name", a.get("name", "Bilinmeyen Hesap"))
            a_login = a.get("login", a.get("id", "Bilinmeyen ID"))

            # Açılır menüdeki liste elemanlarına da ID ve İsim eklendi
            extra_options[
                f"{'🔴' if a_type=='LIVE' else '🧪'} {a_login} - {a_name}"
            ] = a

        selected_extra_name = cols[MAX_BUTTONS].selectbox(
            "Diğer:",
            options=["Diğer Hesaplar..."] + list(extra_options.keys()),
            label_visibility="collapsed",
        )

        if selected_extra_name != "Diğer Hesaplar...":
            selected_acc = extra_options[selected_extra_name]
            selected_acc_login = selected_acc.get("login", selected_acc.get("id"))
            if str(selected_acc_login) != str(active_login):
                st.session_state.selected_account = selected_acc
                st.rerun()

    return st.session_state.selected_account
