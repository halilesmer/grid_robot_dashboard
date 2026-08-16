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
        return False, "[CONFIG] Bağlanılacak hesap seçilmedi veya hesap bilgisi eksik."

    if not MT5_AVAILABLE or platform.system() != "Windows":
        safe_log(
            "💻 Mac Ortamı Tespit Edildi: MT5 bağlantısı simüle ediliyor.",
            type="warning",
        )
        return True, None

    # ==========================================
    # BUNDAN SONRASI SADECE WINDOWS'TA ÇALIŞIR
    # ==========================================

    mt5.shutdown()

    # 1. NAVIGATOR: Welches Terminal soll gestartet werden?
    mt5_path = account_config.get("mt5_path")
    init_success = False

    def _kill_zombie_mt5(path):
        """Yardımcı Fonksiyon: Kilitlenmiş MT5'i işletim sistemi seviyesinde öldürür."""
        if not path or not os.path.exists(path):
            return
        try:
            import psutil
            import subprocess

            target_exe = os.path.basename(path).lower()
            for proc in psutil.process_iter(["pid", "name", "exe"]):
                try:
                    if proc.info["name"] and proc.info["name"].lower() == target_exe:
                        exe_path = proc.info.get("exe")
                        if (
                            exe_path
                            and os.path.normpath(exe_path).lower()
                            == os.path.normpath(path).lower()
                        ):
                            safe_log(
                                f"Asılı kalan MT5 terminali tespit edildi. Öldürülüyor... PID: {proc.info['pid']}",
                                type="warning",
                            )
                            subprocess.call(
                                ["taskkill", "/F", "/PID", str(proc.info["pid"])],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                            time.sleep(2.0)
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    pass
        except ImportError:
            pass

    # ==============================================================
    # 🌟 GİRİŞ BİLGİLERİNİ GÜVENLİ ŞEKİLDE HAZIRLA (Try-Except ile)
    # ==============================================================
    raw_login = account_config.get("login")
    password = account_config.get("password")
    server = account_config.get("server")
    login_id = 0

    if raw_login and password and server:
        try:
            login_id = int(raw_login)
            password = str(password)
            server = str(server)
        except ValueError:
            safe_log(
                f"🔴 BAĞLANTI HATASI: Hesap numarası (Login) sadece rakamlardan oluşmalıdır! Girilen değer: '{raw_login}'",
                type="error",
            )
            return False, f"[CONFIG] Hesap numarası geçersiz: '{raw_login}' (sadece rakam olmalı)"

    # ==============================================================
    # 🌟 AŞAMA 1: OTO-LOGIN İLE BAŞLATMA (mt5.initialize)
    # ==============================================================
    # PORTABLE=TRUE : Farklı Windows kullanıcıları (Admin vs Standart) arasındaki IPC ve AppData çakışmalarını önler!
    init_kwargs = {"timeout": 120000, "portable": True}

    if mt5_path and os.path.exists(mt5_path):
        init_kwargs["path"] = mt5_path
    elif mt5_path:
        safe_log(
            f"UYARI: Belirtilen MT5 yolu bulunamadı ({mt5_path}). Standart terminal açılıyor...",
            type="warning",
        )

    # Eğer hesap bilgileri tamsa, MT5 açılırken doğrudan hesaba giriş yapsın diye parametreleri ekliyoruz
    if login_id > 0:
        init_kwargs.update({"login": login_id, "password": password, "server": server})

    init_success = mt5.initialize(**init_kwargs)

    # 🌟 ZOMBİ AVCISI (Kurtarma): Eğer ilk bağlantı başarısız olursa (IPC hatası vb.), terminal asılı kalmış demektir. Öldür ve tekrar dene!
    if not init_success:
        last_err = mt5.last_error()
        safe_log(
            f"İlk bağlantı başarısız (Hata: {last_err}). Terminal kilitli olabilir. Kurtarma protokolü başlatılıyor...",
            type="warning",
        )

        _kill_zombie_mt5(mt5_path)

        safe_log(
            "Terminal sıfırdan başlatılıyor. Bu işlem VPS hızına bağlı olarak 1-2 dakika sürebilir...",
            type="warning",
        )
        init_kwargs["timeout"] = 150000
        init_success = mt5.initialize(**init_kwargs)

    if not init_success:
        last_err = mt5.last_error()
        if last_err[0] == -10003:
            safe_log(
                f"🔴 MT5 IPC Bağlantısı Reddedildi! (Hata: {last_err}). Python (VS Code/Streamlit) ile MT5'in aynı yönetici (Run as Admin) yetkisine sahip olduğundan emin olun."
            )
            return False, f"[INIT] MT5 başlatılamadı. IPC Bağlantısı Reddedildi (hata kodu: {last_err[0]})"
        else:
            safe_log(
                f"🔴 MetaTrader 5 başlatılamadı! Lütfen terminal yolunu kontrol edin. Hata Kodu: {last_err}"
            )
            return False, f"[INIT] MT5 başlatılamadı. Hata kodu: {last_err[0]} ({last_err[1]})"

    # ==============================================================
    # 🌟 AŞAMA 2: OTO-LOGIN ZORLAMASI (mt5.login) - Açık terminal garantisi
    # ==============================================================
    if login_id > 0:
        # IPC TIMEOUT (-10005) KORUMASI: Terminal yeni açılıyorsa login'e ilk denemede
        # yanıt veremeyebilir. 3 kez deneyip pes etmeden önce terminale nefes payı veriyoruz.
        authorized = False
        last_err = mt5.last_error()

        for attempt in range(1, 4):
            authorized = mt5.login(login=login_id, password=password, server=server)
            if authorized:
                break
            last_err = mt5.last_error()
            if attempt < 3:
                time.sleep(1.5)

        if not authorized:
            err_code = last_err[0]
            err_msg = f"🔴 MT5 Girişi Başarısız! (Hata: {last_err})"

            # 🌟 ÖZEL HATA MESAJLARI (UI Çökmesini Engeller ve Açıklar)
            if (
                err_code == 1002 or err_code == 2
            ):  # 1002: Geçersiz parametre, 2: Common error
                err_msg = f"🔴 BAĞLANTI HATASI: Hesap No ({login_id}), Şifre veya Sunucu adı ({server}) YANLIŞ! Bilgileri kontrol edin."
                phase_msg = f"[LOGIN] Giriş yapılamadı. Hesap {login_id}, şifre veya sunucu '{server}' hatalı (hata kodu: {err_code})"
            elif err_code == -10005:
                err_msg = "🔴 BAĞLANTI HATASI: Terminal çok yavaş açıldı (IPC Timeout). Lütfen tekrar bağlan butonuna basın."
                phase_msg = f"[LOGIN] IPC Timeout (-10005) — Terminal çok yavaş açıldı, login zaman aşımına uğradı"
            elif err_code == 10004:
                err_msg = "🔴 BAĞLANTI HATASI: Sunucuya bağlantı kurulamadı (Requote/No Connection). Aracı kurum sunucusu kapalı olabilir."
                phase_msg = f"[LOGIN] Sunucuya bağlanılamadı. '{server}' sunucusu yanıt vermiyor (hata kodu: {err_code})"
            else:
                phase_msg = f"[LOGIN] Giriş başarısız. Hata kodu: {err_code} ({last_err[1]})"

            safe_log(err_msg, type="error")
            mt5.shutdown()  # Hata durumunda hafızada asılı kalmaması için kapatıldı
            return False, phase_msg

        # Broker sunucusuyla senkronizasyon (fiyatların yüklenmesi) için MT5'e 1 saniye nefes payı ver
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
        return False, "[ACCOUNT] Hesap bilgisi alınamadı. MT5 terminali senkronize olamadı (3 deneme başarısız)"

    # Algo Trading Check
    terminal_info = mt5.terminal_info()
    if terminal_info is not None and not terminal_info.trade_allowed:
        safe_log(
            "🚨 KRİTİK HATA: MetaTrader 5'te 'Algo Trading' (Otomatik Ticaret) butonu kapalı!"
        )
        mt5.shutdown()
        return False, "[TERMINAL] Algo Trading kapalı! MT5 üst menüsünden 'Algo Trading' butonunu aktif (yeşil) yapın."

    is_mt5_demo = account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO
    env_type = account_config.get("type", account_config.get("env_type", ""))

    if env_type == "LIVE" and is_mt5_demo:
        safe_log(
            "🚨 KRİTİK GÜVENLİK İHLALİ: Canlı (LIVE) ortam seçili ama MT5 hesabı DEMO!"
        )
        mt5.shutdown()
        return False, "[SECURITY] Ortam uyuşmazlığı: Robot LIVE modunda ama MT5 hesabı DEMO."

    if env_type in ["DEMO", "TEST"] and not is_mt5_demo:
        safe_log(
            "🚨 KRİTİK GÜVENLİK İHLALİ: Test (TEST) ortamı seçili ama MT5 hesabı GERÇEK PARALI (LIVE)!"
        )
        mt5.shutdown()
        return False, "[SECURITY] Ortam uyuşmazlığı: Robot TEST modunda ama MT5 hesabı GERÇEK PARALI (LIVE)."

    # 🌟 BAĞLANTI BAŞARILI OLDUKTAN SONRA LOGLARI YEDEKLE (Opsiyonel olarak buraya ekleyebilirsin)
    # backup_mt5_logs()

    return True, None


def shutdown_mt5():
    """MT5 bağlantı oturumunu serbest bırakır.

    Arayüz (frontend) "test bağlantısı" yaptıktan sonra artık terminali meşgul
    etmemelidir; aksi halde alt süreç (bot_runner) aynı terminale bağlanmaya
    çalışırken IPC çakışması (-10005 IPC timeout) yaşanabilir.
    """
    if MT5_AVAILABLE and platform.system() == "Windows":
        try:
            mt5.shutdown()
        except Exception:
            pass


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
    """connect_to_mt5'i arka planda çalıştırır; UI'ı kilitlemeden sonuç döner.
    
    Dönüş: (başarı_bool, zaman_aşımı_bool, hata_detayı_str_or_None)
    """
    if not account_config:
        safe_log("Bağlanılacak hesap seçilmedi!")
        return False, False, "[CONFIG] Bağlanılacak hesap seçilmedi."

    # Mac simülasyonu veya MT5 kütüphanesi yoksa zaten anında dönüyoruz (thread'e gerek yok)
    if not MT5_AVAILABLE or platform.system() != "Windows":
        ok, detail = connect_to_mt5(account_config)
        return ok, False, detail

    result = {}

    def _worker():
        try:
            result["ok"], result["detail"] = connect_to_mt5(account_config)
        except Exception as e:
            result["ok"] = False
            result["detail"] = f"[CRITICAL] Bağlantı iş parçacığı çöktü: {e}"
            result["err"] = str(e)

    worker = threading.Thread(target=_worker, daemon=True)
    worker.start()
    worker.join(timeout=timeout)

    if worker.is_alive():
        # ⚠️ Zaman aşımı: MT5 hâlâ açılmaya/bağlanmaya çalışıyor.
        # Kullanıcıyı sonsuza dek bekleterek ön yüzü dondurmak YERİNE hata döndür.
        timeout_msg = (
            f"[TIMEOUT] MT5 bağlantısı {timeout} saniye içinde tamamlanamadı. "
            "Terminal kapalı, sunucuya ulaşılamıyor veya ilk kez açılışta sembol listesi indiriliyor olabilir."
        )
        safe_log(timeout_msg)
        return False, True, timeout_msg

    if result.get("err"):
        safe_log(f"MT5 bağlantı iş parçacığı hatası: {result['err']}")

    return result.get("ok", False), False, result.get("detail")


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
