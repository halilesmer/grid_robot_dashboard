# src/components/account_selector.py
import streamlit as st
import json
import os
import datetime
from src.components.dialogs import confirm_delete_account_dialog

ACCOUNTS_FILE = "configs/accounts.json"


@st.cache_data(ttl=300)
def get_installed_mt5_terminals():
    """C:/Program Files içindeki MT5 terminal64.exe yollarını hızlıca tarar."""
    terminals = []
    base_path = "C:/Program Files"
    if os.path.exists(base_path):
        try:
            for folder in os.listdir(base_path):
                full_dir = os.path.join(base_path, folder)
                if os.path.isdir(full_dir):
                    exe_path = os.path.join(full_dir, "terminal64.exe")
                    if os.path.exists(exe_path):
                        terminals.append(exe_path.replace("\\", "/"))
        except Exception:
            pass
    return terminals


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

    # 🌟 Popover'ı (Açılır Menü) Kapatma Hilesi
    if st.session_state.get("close_popover"):
        st.session_state.close_popover = False
        import streamlit.components.v1 as components

        components.html(
            "<script>window.parent.document.body.click();</script>", height=0, width=0
        )

    accounts = load_accounts()

    if not accounts:
        st.warning(
            "Hiç hesap bulunamadı! Lütfen '➕ Yeni' butonuna tıklayarak ilk hesabınızı ekleyin."
        )
        st.session_state.selected_account = None

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

    if accounts:
        if (
            "selected_account" not in st.session_state
            or st.session_state.selected_account is None
        ):
            st.session_state.selected_account = accounts[0]

        active_account = st.session_state.selected_account
        active_login = active_account.get(
            "login", active_account.get("id", "Bilinmeyen")
        )
        active_name = active_account.get(
            "account_name", active_account.get("name", "Bilinmeyen Hesap")
        )
        active_type = active_account.get("env_type", active_account.get("type", "DEMO"))
    else:
        active_account = {}
        active_login = "Bilinmeyen"
        active_name = "Hesap Yok"
        active_type = "DEMO"

    if "show_add_form" not in st.session_state:
        st.session_state.show_add_form = False

    is_running = st.session_state.get("robot_running", False)

    # 1. Buton Renk Stili ve Üst Boşluk Temizliği
    st.markdown(
        "<style>"
        ".block-container { padding-top: 2rem !important; } "
        "button[kind='primary'] { background-color: #198754 !important; border-color: #198754 !important; color: white !important; } "
        "button[kind='primary']:hover { background-color: #157347 !important; border-color: #146c43 !important; }"
        "</style>",
        unsafe_allow_html=True,
    )

    # 2. Temiz ve Şık Buton Menüsü
    MAX_BUTTONS = 4
    num_accounts = len(accounts)
    has_extra = 1 if num_accounts > MAX_BUTTONS else 0

    col_ratios = [1] * (min(num_accounts, MAX_BUTTONS) + has_extra) + [0.15]
    cols = st.columns(col_ratios)

    for i, acc in enumerate(accounts[:MAX_BUTTONS]):
        acc_type = acc.get("env_type", acc.get("type", "DEMO"))
        acc_name = acc.get("account_name", acc.get("name", "Bilinmeyen Hesap"))
        acc_login = acc.get("login", acc.get("id", "Bilinmeyen ID"))

        btn_icon = "🔴" if acc_type == "LIVE" else "🧪"
        btn_label = f"{btn_icon} {acc_login} - {acc_name}"
        is_active = str(acc.get("login", acc.get("id"))) == str(active_login)

        if cols[i].button(
            btn_label,
            key=f"btn_{i}_{acc_login}",
            type="primary" if is_active else "secondary",
            width="stretch",
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

    # --- EN SAĞDAKİ ÜÇ NOKTA (POPOVER) MENÜSÜ ---
    with cols[-1].popover("⋮", width="stretch"):

        # 🌟 YENİ: Hesaba ve MT5 Yoluna Özel Dinamik Log Tespiti
        try:
            log_data = None
            today_str = datetime.datetime.now().strftime("%Y%m%d")
            active_login = active_account.get("login", "hesap")
            log_filename = f"MT5_{active_login}_{today_str}.log"
            
            target_log_paths = []

            # 1. MT5 Çalışıyorsa Anlık Data Path'i Al
            try:
                import MetaTrader5 as mt5
                term_info = mt5.terminal_info()
                if term_info and hasattr(term_info, "data_path"):
                    target_log_paths.append(os.path.join(term_info.data_path, "Logs", f"{today_str}.log"))
            except Exception:
                pass

            # 2. Hesabın mt5_path Bilgisinden AppData/MetaQuotes/Terminal Altındaki Gerçek Klasörünü Tara
            active_mt5_path = active_account.get("mt5_path", "")
            if active_mt5_path:
                appdata_base = os.path.expandvars(r"%APPDATA%\MetaQuotes\Terminal")
                if os.path.exists(appdata_base):
                    norm_target_path = os.path.normpath(active_mt5_path).lower()
                    for terminal_hash in os.listdir(appdata_base):
                        hash_dir = os.path.join(appdata_base, terminal_hash)
                        origin_txt = os.path.join(hash_dir, "origin.txt")
                        
                        # origin.txt içindeki yol seçili hesabın mt5_path adresiyle eşleşiyor mu?
                        if os.path.exists(origin_txt):
                            try:
                                with open(origin_txt, "r", encoding="utf-16-le", errors="ignore") as f:
                                    orig_path = f.read().strip().replace("\x00", "").lower()
                                if os.path.normpath(orig_path) == norm_target_path:
                                    target_log_paths.append(os.path.join(hash_dir, "Logs", f"{today_str}.log"))
                                    break
                            except Exception:
                                pass

                # Yedek Yol: Doğrudan Program Files İçindeki Kurulum Dizinine Bak
                term_dir = os.path.dirname(active_mt5_path)
                target_log_paths.append(os.path.join(term_dir, "MQL5", "Logs", f"{today_str}.log"))
                target_log_paths.append(os.path.join(term_dir, "logs", f"{today_str}.log"))

            # Bulunan Yolları Sırayla Kontrol Et
            for l_path in target_log_paths:
                if os.path.exists(l_path):
                    with open(l_path, "rb") as f:
                        log_data = f.read()
                    break

            if log_data:
                st.download_button(
                    label="📥 MT5 Logunu İndir",
                    data=log_data,
                    file_name=log_filename,
                    mime="text/plain",
                    use_container_width=True,
                )
            else:
                st.button("📥 MT5 Logu Bulunamadı", disabled=True, use_container_width=True)
        except Exception:
            st.button("📥 MT5 Logu Okunamadı", disabled=True, use_container_width=True)

        if st.button(
            "✏️ Seçili Hesabı Düzenle",
            width="stretch",
            disabled=not accounts or is_running,
            key="popover_edit_btn",
        ):
            st.session_state.edit_account = active_account
            st.session_state.show_add_form = True
            st.session_state.close_popover = True  # Menüyü kapat
            st.rerun()

        if st.button(
            "🗑️ Seçili Hesabı Sil",
            width="stretch",
            disabled=not accounts or is_running,
            key="popover_delete_btn",
        ):

            def delete_current_account():
                new_accounts = [
                    a
                    for a in accounts
                    if str(a.get("login")) != str(active_account.get("login"))
                ]
                try:
                    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
                        json.dump(
                            {"accounts": new_accounts}, f, indent=4, ensure_ascii=False
                        )

                    st.session_state.selected_account = (
                        new_accounts[0] if new_accounts else None
                    )
                except Exception as e:
                    st.error(f"Silme sırasında hata: {e}")

            confirm_delete_account_dialog(active_name, delete_current_account)

        if st.button(
            "➕ Yeni Hesap Ekle",
            width="stretch",
            type="primary",
            key="popover_add_btn",
        ):
            st.session_state.show_add_form = not st.session_state.show_add_form
            st.session_state.edit_account = None
            st.session_state.close_popover = True  # Menüyü kapat
            st.rerun()
    # ==========================================
    # 3. YENİ HESAP EKLEME / DÜZENLEME FORMU
    # ==========================================
    if st.session_state.show_add_form:
        st.markdown("---")

        edit_acc = st.session_state.get("edit_account") or {}
        is_edit = bool(edit_acc)
        old_login = str(edit_acc.get("login", ""))

        used_terminals = {
            os.path.normpath(a.get("mt5_path", "")).lower(): a.get(
                "account_name", "Bilinmeyen"
            )
            for a in accounts
            if a.get("mt5_path") and str(a.get("login")) != old_login
        }

        found_terminals = get_installed_mt5_terminals()
        terminal_options = ["Farklı Bir Yol (Manuel Gireceğim)"]
        old_mt5_path = edit_acc.get("mt5_path", "")

        for t_path in found_terminals:
            norm_path = os.path.normpath(t_path).lower()
            if norm_path in used_terminals:
                terminal_options.append(
                    f"🔴 Dolu ({used_terminals[norm_path]}) - {t_path}"
                )
            else:
                terminal_options.append(f"🟢 Boşta - {t_path}")

        if (
            is_edit
            and old_mt5_path
            and not any(old_mt5_path in opt for opt in terminal_options)
        ):
            terminal_options.append(f"🟢 Mevcut Adres - {old_mt5_path}")

        with st.container():
            st.markdown(
                f"#### {'✏️ Hesabı Düzenle' if is_edit else '➕ Yeni MT5 Hesabı Ekle'}"
            )
            with st.form("add_new_account_form", clear_on_submit=False):
                col1, col2 = st.columns(2)

                with col1:
                    new_acc_name = st.text_input(
                        "Hesap Adı *",
                        value=edit_acc.get("account_name", ""),
                        placeholder="Örn: Canlı Hesap - 1",
                    )
                    new_login = st.text_input(
                        "Hesap No (Login) *",
                        value=old_login if is_edit else "",
                        placeholder="Örn: 12345678",
                        help="Girdiğiniz bu numara aynı zamanda sistemde Hesap ID'si olarak kullanılacaktır.",
                    )

                    env_opts = ["DEMO", "LIVE"]
                    def_env_idx = (
                        env_opts.index(edit_acc.get("env_type", "DEMO"))
                        if is_edit and edit_acc.get("env_type") in env_opts
                        else 0
                    )
                    new_env = st.selectbox(
                        "Çevre (Ortam) *", env_opts, index=def_env_idx
                    )

                with col2:
                    new_password = st.text_input(
                        "Şifre *",
                        value=edit_acc.get("password", ""),
                        type="password",
                        placeholder="MT5 Şifresi",
                    )
                    new_server = st.text_input(
                        "Sunucu *",
                        value=edit_acc.get("server", ""),
                        placeholder="Örn: Eightcap-Demo",
                    )

                    def_term_idx = 0
                    if is_edit and old_mt5_path:
                        for idx, opt in enumerate(terminal_options):
                            if old_mt5_path in opt:
                                def_term_idx = idx
                                break

                    selected_terminal = st.selectbox(
                        "Bilgisayardaki MT5 Klasörleri (Hızlı Seçim)",
                        terminal_options,
                        index=def_term_idx,
                    )

                    if selected_terminal == "Farklı Bir Yol (Manuel Gireceğim)":
                        auto_path = old_mt5_path if is_edit else ""
                    else:
                        auto_path = selected_terminal.split(" - ")[-1].strip()

                    new_mt5_path = st.text_input(
                        "MT5 Yolu *",
                        value=auto_path,
                        placeholder="C:/Program Files/MetaTrader 5/terminal64.exe",
                    )

                new_notes = st.text_area(
                    "📝 Hesap Notu (İsteğe Bağlı)",
                    value=edit_acc.get("notes", ""),
                    max_chars=1000,
                    placeholder="Bu hesapla ilgili stratejiniz, kısıtlamalarınız veya özel notlar... (Maks. 1000 karakter)",
                    height=100,
                )

                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    submit_btn = st.form_submit_button(
                        "💾 Değişiklikleri Kaydet" if is_edit else "💾 Hesabı Ekle",
                        width="stretch",
                    )
                with btn_col2:
                    cancel_btn = st.form_submit_button(
                        "❌ İptal", width="stretch"
                    )

                if cancel_btn:
                    st.session_state.show_add_form = False
                    st.session_state.edit_account = None
                    st.rerun()

                if submit_btn:
                    if (
                        not new_login
                        or not new_acc_name
                        or not new_password
                        or not new_server
                        or not new_mt5_path
                    ):
                        st.error(
                            "🚨 Lütfen yıldızlı tüm zorunlu alanları eksiksiz doldurun!"
                        )
                    else:
                        other_logins = [x for x in login_ids if x != old_login]
                        if str(new_login) in other_logins:
                            st.error(
                                f"🚫 Hata: '{new_login}' numaralı hesap zaten sisteme kayıtlı!"
                            )
                        else:
                            norm_new_path = os.path.normpath(new_mt5_path).lower()
                            if norm_new_path in used_terminals:
                                st.error(
                                    f"🚨 HATA: Bu MT5 terminali halihazırda '{used_terminals[norm_new_path]}' hesabı tarafından kullanılıyor!"
                                )
                            else:
                                try:
                                    login_val = int(new_login)
                                except ValueError:
                                    login_val = new_login

                                new_account_data = {
                                    "id": str(new_login),
                                    "account_name": new_acc_name,
                                    "env_type": new_env,
                                    "login": login_val,
                                    "password": new_password,
                                    "server": new_server,
                                    "mt5_path": new_mt5_path.replace("\\", "/"),
                                    "notes": new_notes,
                                }

                                if is_edit:
                                    for idx, a in enumerate(accounts):
                                        if str(a.get("login")) == old_login:
                                            accounts[idx] = new_account_data
                                            break
                                else:
                                    accounts.append(new_account_data)

                                try:
                                    with open(
                                        ACCOUNTS_FILE, "w", encoding="utf-8"
                                    ) as f:
                                        json.dump(
                                            {"accounts": accounts},
                                            f,
                                            indent=4,
                                            ensure_ascii=False,
                                        )

                                    st.session_state.selected_account = new_account_data
                                    st.session_state.show_add_form = False
                                    st.session_state.edit_account = None
                                    st.session_state.close_popover = True
                                    st.success(
                                        f"✅ {new_acc_name} başarıyla kaydedildi!"
                                    )
                                    st.rerun()
                                except Exception as e:
                                    st.error(
                                        f"Kayıt sırasında teknik bir hata oluştu: {e}"
                                    )

    return st.session_state.selected_account
