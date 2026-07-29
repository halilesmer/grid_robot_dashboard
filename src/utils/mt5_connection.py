# src/utils/mt5_connection.py

import streamlit as st
import platform
import time

try:
    import MetaTrader5 as mt5

    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


def connect_to_mt5(account_config):
    if not account_config:
        st.error("Bağlanılacak hesap seçilmedi!")
        return False

    if not MT5_AVAILABLE or platform.system() != "Windows":
        st.warning(
            "💻 Mac Ortamı Tespit Edildi: MT5 bağlantısı simüle ediliyor. (Gerçek bağlantı Windows'ta çalışacaktır)."
        )
        return True

    # ==========================================
    # BUNDAN SONRASI SADECE WINDOWS'TA ÇALIŞIR
    # ==========================================

    mt5.shutdown()

    mt5_path = account_config.get("mt5_path")

    if mt5_path:
        init_success = mt5.initialize(path=mt5_path)
    else:
        init_success = mt5.initialize()

    if not init_success:
        st.error(f"MetaTrader 5 başlatılamadı! Hata Kodu: {mt5.last_error()}")
        return False

    login_id = account_config.get("login")
    password = account_config.get("password")
    server = account_config.get("server")

    if login_id and password and server:
        authorized = mt5.login(login=int(login_id), password=password, server=server)
        if not authorized:
            st.error(
                f"🔴 MT5 Girişi Başarısız! Hesap No: {login_id}. Hata Kodu: {mt5.last_error()}"
            )
            return False
    else:
        time.sleep(2.0)

    account_info = mt5.account_info()
    if account_info is None:
        st.error(
            "Hesap bilgileri MetaTrader'dan alınamadı! (Auto-Login gecikmiş veya MT5 kapalı olabilir)"
        )
        mt5.shutdown()
        return False

    # ==========================================
    # YENİ: ALGO TRADING KONTROLÜ (SOFORT-CHECK)
    # ==========================================
    terminal_info = mt5.terminal_info()
    if terminal_info is not None and not terminal_info.trade_allowed:
        st.error(
            "🚨 KRİTİK HATA: MetaTrader 5'te 'Algo Trading' (Otomatik Ticaret) butonu kapalı!"
        )
        st.error(
            "İşlem reddedildi. Lütfen MT5 terminalinin üst menüsündeki 'Algo Trading' butonunu yeşil (aktif) hale getirin ve tekrar deneyin."
        )
        mt5.shutdown()
        return False
    # ==========================================

    is_mt5_demo = account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO
    env_type = account_config.get("type", account_config.get("env_type", ""))

    if env_type == "LIVE" and is_mt5_demo:
        st.error(
            "🚨 KRİTİK GÜVENLİK İHLALİ: Canlı (LIVE) ortam seçili ama MT5 hesabı DEMO!"
        )
        st.error("İşlem reddedildi. Lütfen doğru hesabı seçin.")
        mt5.shutdown()
        return False

    if env_type in ["DEMO", "TEST"] and not is_mt5_demo:
        st.error(
            "🚨 KRİTİK GÜVENLİK İHLALİ: Test (TEST) ortamı seçili ama MT5 hesabı GERÇEK PARALI (LIVE)!"
        )
        st.error("İşlem reddedildi. Lütfen doğru hesabı seçin.")
        mt5.shutdown()
        return False

    return True
