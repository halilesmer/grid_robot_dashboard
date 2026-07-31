# src/utils/mt5_connection.py

import platform
import time
import os

# Streamlit sicher importieren, um Subprocess-Abstürze zu verhindern!
try:
    import streamlit as st
    from streamlit.runtime.scriptrunner import get_script_run_ctx
except ImportError:
    st = None


def safe_log(msg, type="error"):
    """Zeigt Fehler im Dashboard an, schreibt sie aber im Hintergrund-Prozess sicher ins Log, ohne abzustürzen!"""
    print(msg)  # Geht immer sicher in die bot_..._error.log Datei
    if st is not None:
        try:
            if get_script_run_ctx() is not None:  # Prüft, ob wir im UI-Dashboard sind
                if type == "error":
                    st.error(msg)
                elif type == "warning":
                    st.warning(msg)
        except Exception:
            pass


try:
    import MetaTrader5 as mt5

    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


def connect_to_mt5(account_config):
    if not account_config:
        safe_log("Bağlanılacak hesap seçilmedi!")
        return False

    if not MT5_AVAILABLE or platform.system() != "Windows":
        safe_log(
            "💻 Mac Ortamı Tespit Edildi: MT5 bağlantısı simüle ediliyor.",
            type="warning",
        )
        return True

    # ==========================================
    # BUNDAN SONRASI SADECE WINDOWS'TA ÇALIŞIR
    # ==========================================

    mt5.shutdown()

    # 1. NAVIGATOR: Welches Terminal soll gestartet werden?
    mt5_path = account_config.get("mt5_path")

    # Prüfen, ob der Pfad in der JSON steht und die Datei auf dem Windows-Server wirklich existiert
    if mt5_path and os.path.exists(mt5_path):
        init_success = mt5.initialize(path=mt5_path)
    else:
        if mt5_path:
            safe_log(
                f"UYARI: Belirtilen MT5 yolu bulunamadı ({mt5_path}). Standart terminal açılıyor...",
                type="warning",
            )
        init_success = mt5.initialize()

    if not init_success:
        safe_log(f"MetaTrader 5 başlatılamadı! Hata Kodu: {mt5.last_error()}")
        return False

    login_id = account_config.get("login")
    password = account_config.get("password")
    server = account_config.get("server")

    if login_id and password and server:
        authorized = mt5.login(login=int(login_id), password=password, server=server)
        if not authorized:
            safe_log(
                f"🔴 MT5 Girişi Başarısız! Hesap No: {login_id}. Hata Kodu: {mt5.last_error()}"
            )
            mt5.shutdown()  # Hata durumunda hafızada asılı kalmaması için kapatıldı
            return False

        # DÜZELTME: Broker sunucusuyla senkronizasyon için MT5'e 1 saniye nefes payı ver
        time.sleep(1.0)
    else:
        time.sleep(2.0)

    # DÜZELTME: Hesap verilerini çekmek için 3 denemeli (Retry) güvenli döngü kuruldu
    account_info = None
    for _ in range(3):
        account_info = mt5.account_info()
        if account_info is not None:
            break
        time.sleep(1.0)

    if account_info is None:
        safe_log(
            "Hesap bilgileri MetaTrader'dan alınamadı! (Auto-Login gecikmiş veya MT5 kapalı olabilir)"
        )
        mt5.shutdown()
        return False

    # Algo Trading Check
    terminal_info = mt5.terminal_info()
    if terminal_info is not None and not terminal_info.trade_allowed:
        safe_log(
            "🚨 KRİTİK HATA: MetaTrader 5'te 'Algo Trading' (Otomatik Ticaret) butonu kapalı!"
        )
        mt5.shutdown()
        return False

    is_mt5_demo = account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO
    env_type = account_config.get("type", account_config.get("env_type", ""))

    if env_type == "LIVE" and is_mt5_demo:
        safe_log(
            "🚨 KRİTİK GÜVENLİK İHLALİ: Canlı (LIVE) ortam seçili ama MT5 hesabı DEMO!"
        )
        mt5.shutdown()
        return False

    if env_type in ["DEMO", "TEST"] and not is_mt5_demo:
        safe_log(
            "🚨 KRİTİK GÜVENLİK İHLALİ: Test (TEST) ortamı seçili ama MT5 hesabı GERÇEK PARALI (LIVE)!"
        )
        mt5.shutdown()
        return False

    return True
