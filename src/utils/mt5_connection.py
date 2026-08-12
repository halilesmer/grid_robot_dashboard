# src/utils/mt5_connection.py

import platform
import time
import os
import threading  # 🌟 YENİ: Arayüzün kilitlenmemesi için zaman aşımlı bağlantı
import shutil  # 🌟 YENİ EKLENDİ (Dosya kopyalamak için)
import datetime  # 🌟 YENİ EKLENDİ (Tarih formatı için)

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

    # 🌟 BAĞLANTI BAŞARILI OLDUKTAN SONRA LOGLARI YEDEKLE (Opsiyonel olarak buraya ekleyebilirsin)
    # backup_mt5_logs()

    return True


# ==========================================
# 🌟 YENİ: ZAMAN AŞIMLI (TIMEOUT) MT5 BAĞLANTISI — Arayüz Kilitlenmesin!
#
# Streamlit script dosyası TAMAMEN tek iş parçacığında (thread) çalışır.
# connect_to_mt5() doğrudan çağrıldığında, MT5 terminal açılışı veya sunucuya
# giriş (initialize/login) ağ bağlantısı olmadığında ÇOK UZUN sürebilir ve bu
# süre boyunca Tarayıcı ön yüzü donar (kullanıcı hiçbir şey yapamaz).
#
# Bu fonksiyon bağlantıyı ARKA PLANDAN dener ve en fazla 'timeout' saniye bekler.
# Süre dolarsa hemen (False, True) döner → arayüz kilitlenmez, net hata gösterir.
#
# Dönüş: (başarı_bool, zaman_aşımı_bool)
# ==========================================
def connect_to_mt5_with_timeout(account_config, timeout=20):
    """connect_to_mt5'i arka planda çalıştırır; UI'ı kilitlemeden sonuç döner."""
    if not account_config:
        safe_log("Bağlanılacak hesap seçilmedi!")
        return False, False

    # Mac simülasyonu veya MT5 kütüphanesi yoksa zaten anında dönüyoruz (thread'e gerek yok)
    if not MT5_AVAILABLE or platform.system() != "Windows":
        return connect_to_mt5(account_config), False

    result = {}

    def _worker():
        try:
            result["ok"] = connect_to_mt5(account_config)
        except Exception as e:
            result["ok"] = False
            result["err"] = str(e)

    worker = threading.Thread(target=_worker, daemon=True)
    worker.start()
    worker.join(timeout=timeout)

    if worker.is_alive():
        # ⚠️ Zaman aşımı: MT5 hâlâ açılmaya/bağlanmaya çalışıyor.
        # Kullanıcıyı sonsuza dek bekleterek ön yüzü dondurmak YERİNE hata döndür.
        safe_log(
            f"MT5 bağlantısı {timeout} saniye içinde tamamlanamadı (zaman aşımı). "
            "Terminal kapalı veya sunucuya ulaşılamıyor olabilir."
        )
        return False, True

    if result.get("err"):
        safe_log(f"MT5 bağlantı iş parçacığı hatası: {result['err']}")

    return result.get("ok", False), False


# ==========================================
# 🌟 YENİ: MT5 Terminal Loglarını Yedekleme Fonksiyonu
# ==========================================
def backup_mt5_logs(custom_log_dir="logs/mt5"):
    """
    MT5 Terminal loglarını okur ve projedeki logs/mt5 klasörüne kopyalar.
    """
    if not MT5_AVAILABLE or platform.system() != "Windows":
        return  # Mac veya MT5 olmayan ortamlarda pas geç

    # 1. Klasör yoksa oluştur
    if not os.path.exists(custom_log_dir):
        try:
            os.makedirs(custom_log_dir)
        except Exception:
            pass

    # 2. MT5 Terminal bilgilerini çek
    term_info = mt5.terminal_info()
    if term_info is None:
        return

    # 3. MT5 log klasörünün yolunu bul
    mt5_logs_dir = os.path.join(term_info.data_path, "Logs")

    # 4. Bugünün tarihine göre dosya adını oluştur (Örn: 20260810.log)
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    today_log_file = f"{today_str}.log"
    source_log_path = os.path.join(mt5_logs_dir, today_log_file)

    # 5. Dosyayı kendi klasörümüze kopyala
    if os.path.exists(source_log_path):
        target_log_path = os.path.join(custom_log_dir, f"MT5_Terminal_{today_log_file}")
        try:
            # copy2 kullanarak dosya izinleri ve oluşturulma tarihlerini de koruruz
            shutil.copy2(source_log_path, target_log_path)
            # safe_log(f"MT5 Terminal Logu başarıyla yedeklendi.", type="warning")
        except Exception as e:
            safe_log(f"MT5 Log kopyalama hatası: {e}")
