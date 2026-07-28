# src/utils/mt5_connection.py

import streamlit as st
import platform
import time  # 👈 FEHLTE VORHER: Wichtig für den Auto-Login Delay!

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

    # ÖNCEKİ BAĞLANTIYI KES (Multi-Account için zorunlu)
    mt5.shutdown()

    mt5_path = account_config.get("mt5_path")

    # 1. MT5 Terminalini Özel Yoldan (Path) Başlat
    if mt5_path:
        init_success = mt5.initialize(path=mt5_path)
    else:
        init_success = mt5.initialize()

    if not init_success:
        st.error(f"MetaTrader 5 başlatılamadı! Hata Kodu: {mt5.last_error()}")
        return False

    # 2. Seçilen Hesaba Giriş Yap
    login_id = account_config.get("login")
    password = account_config.get("password")
    server = account_config.get("server")

    if login_id and password and server:
        # Şifre varsa zorla giriş yap
        authorized = mt5.login(login=int(login_id), password=password, server=server)
        if not authorized:
            st.error(
                f"🔴 MT5 Girişi Başarısız! Hesap No: {login_id}. Hata Kodu: {mt5.last_error()}"
            )
            return False
    else:
        # 👈 DER EHRLICHE FIX: Şifre yoksa MT5'in otomatik giriş yapmasını bekle!
        # Terminalin sunucuya bağlanması ve verileri çekmesi için 2 saniye süre veriyoruz.
        time.sleep(2.0)

    # 3. GÜVENLİK SİGORTASI (Çapraz Kontrol)
    account_info = mt5.account_info()
    if account_info is None:
        st.error(
            "Hesap bilgileri MetaTrader'dan alınamadı! (Auto-Login gecikmiş veya MT5 kapalı olabilir)"
        )
        mt5.shutdown()
        return False

    # MT5'in bize söylediği hesap türü (Demo mu Gerçek mi?)
    is_mt5_demo = account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO

    # JSON'dan gelen ortam türü ('type' veya eski adıyla 'env_type')
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
