# src/utils/mt5_connection.py

import streamlit as st
import platform

# MT5 kütüphanesini sadece Windows'ta içe aktarmayı deneriz. Mac'te çökmeyi önleriz.
try:
    import MetaTrader5 as mt5

    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


def connect_to_mt5(account_config):
    """
    Kullanıcının seçtiği hesap bilgileriyle MT5'e bağlanır ve güvenlik kontrollerini yapar.
    Mac ortamında ise çökmeyi önlemek için bağlantıyı simüle eder.
    """
    if not account_config:
        st.error("Bağlanılacak hesap seçilmedi!")
        return False

    # EĞER BİLGİSAYAR MAC İSE (Simülasyon Modu)
    if not MT5_AVAILABLE or platform.system() != "Windows":
        st.warning(
            "💻 Mac Ortamı Tespit Edildi: MT5 bağlantısı simüle ediliyor. (Gerçek bağlantı Windows'ta çalışacaktır)."
        )
        return True  # Mac'te arayüzü test edebilmen için bağlantıyı başarılı sayıyoruz

    # ==========================================
    # BUNDAN SONRASI SADECE WINDOWS'TA ÇALIŞIR
    # ==========================================

    # 1. MT5 Terminalini Başlat
    if not mt5.initialize():
        st.error(f"MetaTrader 5 başlatılamadı! Hata Kodu: {mt5.last_error()}")
        return False

    login_id = int(account_config["login"])
    password = account_config["password"]
    server = account_config["server"]
    env_type = account_config["env_type"]  # 'TEST' veya 'LIVE'

    # 2. Seçilen Hesaba Giriş Yap
    authorized = mt5.login(login=login_id, password=password, server=server)

    if not authorized:
        st.error(
            f"🔴 MT5 Girişi Başarısız! Hesap No: {login_id}. Hata Kodu: {mt5.last_error()}"
        )
        return False

    # 3. GÜVENLİK SİGORTASI (Çapraz Kontrol)
    account_info = mt5.account_info()
    if account_info is None:
        st.error("Hesap bilgileri MetaTrader'dan alınamadı!")
        mt5.shutdown()
        return False

    # MT5'in bize söylediği hesap türü (Demo mu Gerçek mi?)
    is_mt5_demo = account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO

    # Kural 1: LIVE seçilmişse ama hesap DEMO ise
    if env_type == "LIVE" and is_mt5_demo:
        st.error(
            "🚨 KRİTİK GÜVENLİK İHLALİ: Canlı (LIVE) ortam seçili ama MT5 hesabı DEMO!"
        )
        st.error("İşlem reddedildi. Lütfen doğru hesabı seçin.")
        mt5.shutdown()
        return False

    # Kural 2: TEST seçilmişse ama hesap GERÇEK (LIVE) ise
    if env_type == "TEST" and not is_mt5_demo:
        st.error(
            "🚨 KRİTİK GÜVENLİK İHLALİ: Test (TEST) ortamı seçili ama MT5 hesabı GERÇEK PARALI (LIVE)!"
        )
        st.error("İşlem reddedildi. Lütfen doğru hesabı seçin.")
        mt5.shutdown()
        return False

    # Her şey yolundaysa
    return True
