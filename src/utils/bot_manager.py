# src/utils/bot_manager.py
import subprocess
import sys
import os
import json
import streamlit as st
import time  # Bekleme (sleep) için eklendi
from pathlib import Path

# Proje dizinini al ki utils klasöründeki dosyalara ulaşabilelim
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Gerekli bağlantı ve temizlik fonksiyonlarını içeri aktar
from src.utils.mt5_connection import connect_to_mt5
from src.utils.trade_utils import cancel_all_pending_orders, close_position

import psutil  # 🌟 YENİ: İşletim sistemi süreçlerini okumak için

# 🌟 YENİ: Merkezi yol yöneticisini içeri aktarıyoruz
from src.utils.paths import get_err_log_path, get_pid_path

# ==========================================
# MAC KORUMASI (Crash Önleyici Zırh)
# ==========================================
try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None  # Mac ortamında çökmemesi için mt5 modülünü boş (None) atıyoruz

# Robot emirlerinin magic aralığı (model_2.py BASE_MAGIC_NUMBER ile aynı)
BOT_MAGIC_MIN = 200000
BOT_MAGIC_MAX = 201000


def _read_pid(account_id: str):
    """PID dosyasını okur. Yoksa veya bozuksa None döner."""
    pid_file = get_pid_path(account_id)
    if not os.path.exists(pid_file):
        return None
    try:
        with open(pid_file, "r") as f:
            return int(f.read().strip())
    except Exception:
        return None


def _is_our_runner(pid: int, account_id: str) -> bool:
    """Verilen PID gerçekten BU hesaba ait canlı bir bot_runner mı?

    🔍 Kimlik doğrulama: PID + komut satırı (bot_runner.py + hesap ID).
    Port değiştiğinde veya dosyalar başka bilgisayara taşındığında PID yeni bir
    sürece verilmiş olsa bile, gerçekten bizim bot'umuz değilse 'çalışıyor' denmez
    ve öldürülmez. (is_bot_running ve stop_bot_process ortak kullanır.)
    """
    try:
        if not psutil.pid_exists(pid):
            return False

        p = psutil.Process(pid)
        if p.status() == psutil.STATUS_ZOMBIE:
            return False

        try:
            cmdline = " ".join(p.cmdline() or [])
        except Exception:
            cmdline = ""

        if "bot_runner.py" not in cmdline:
            return False
        if account_id not in cmdline:
            return False
        return True
    except Exception:
        return False


def is_bot_running(account_id: str) -> bool:
    """Robotun gerçekten (İşletim Sistemi seviyesinde) çalışıp çalışmadığını kontrol eder.

    🔍 GÜNCELLEME: PID + komut satırı doğrulaması. Port değiştiğinde veya dosyalar
    başka bilgisayara taşındığında PID yeniden kullanılsa bile, gerçekten bizim
    bot_runner.py'imiz değilse 'çalışıyor' denmez.
    """
    pid = _read_pid(account_id)
    if pid is None:
        return False

    if not _is_our_runner(pid, account_id):
        # Başka bir süreç bu PID'yi kapmış olabilir → çöp dosyayı temizle
        self_cleanup(account_id)
        return False

    return True


def self_cleanup(account_id: str):
    """Çalışmayan bir bota ait PID dosyasını temizler. (Sadece dosya, MT5'e dokunmaz)"""
    try:
        os.remove(get_pid_path(account_id))
    except OSError:
        pass


def _detached_popen(cmd, stdout, stderr, env):
    """Streamlit'ten BAĞIMSIZ bir süreç başlatır.

    🚀 PHASE 3: Alt süreç yeni bir oturumda (session) açılır;
    Streamlit kapanır / port değişir / bilgisayar yeniden başlatılır (VM)
    ana arayüz çökse bile bot süreci YAŞAMAYA DEVAM EDER.
    """
    if os.name == "nt":
        return subprocess.Popen(
            cmd,
            stdout=stdout,
            stderr=stderr,
            text=True,
            env=env,
            creationflags=(
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            ),
        )
    return subprocess.Popen(
        cmd,
        stdout=stdout,
        stderr=stderr,
        text=True,
        env=env,
        start_new_session=True,  # Yeni oturum: ana arayüzden gelen sinyallerden izole
    )


def start_bot_process(account_id: str, model_name: str) -> bool:
    """Belirli bir hesap için izole bir Subprocess (alt süreç) başlatır."""
    if is_bot_running(account_id):
        return True  # Zaten çalışıyor

    log_file = None
    try:
        # Her hesaba özel log dosyası oluştur (Klasör kontrolü paths.py içinde yapılır)
        log_file_path = get_err_log_path(account_id)

        # Log dosyasını 'append' (ekleme) modunda aç
        log_file = open(log_file_path, "a", encoding="utf-8")

        # Ortam değişkenini arayüzden bağımsız şekilde alt sürece ilet
        env = dict(os.environ)
        env["ACTIVE_ACCOUNT_ID"] = account_id

        # Ayrı bir Python programı olarak botu tetikle. (Detach edilmiş süreç)
        process = _detached_popen(
            [sys.executable, "-u", "src/core/bot_runner.py", account_id, model_name],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env,
        )

        # 🌟 YENİ: Sürecin ID'sini (PID) kalıcı olarak diske yaz! (RAM sıfırlansa da ölmez)
        pid_file = get_pid_path(account_id)
        with open(pid_file, "w") as f:
            f.write(str(process.pid))

        return True

    except Exception as e:
        # Profesyonel hata yakalama: Çökme durumunda arayüze net bilgi ver
        st.error(
            f"🚨 Sistem Hatası: {account_id} için robot başlatılamadı!\n\nDetay: {str(e)}"
        )
        return False
    finally:
        # GÜVENLİK DÜZELTMESİ: Açılan dosya akışı (file descriptor) hafızada kilitli kalmasın diye kapatılıyor
        if log_file is not None:
            try:
                log_file.close()
            except Exception:
                pass


def stop_bot_process(account_id: str) -> bool:
    """
    🟡 Botu YALNIZCA durdurur. Hiçbir pozisyon veya bekleyen emre DOKUNMAZ.

    🚀 PHASE 4: MT5'e bağlanıp emir silme / pozisyon kapatma mantığı KALDIRILDI.
    İşlemler broker'da olduğu gibi kalır; bot kapatılır, arkasında iz bırakılmaz.
    """
    pid = _read_pid(account_id)

    # Güvenlik: Sadece GERÇEKTEN bu hesabın bot_runner sürecini öldür.
    # Bayat PID dosyası başka bir sürece verilmişse ona dokunma.
    if pid is not None and _is_our_runner(pid, account_id):
        try:
            if os.name == "nt":
                # Windows işletim sistemi ise Taskkill ile tüm alt döngüleri sonlandır
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                # Mac/Linux sistemleri için
                process = psutil.Process(pid)
                process.terminate()
                try:
                    process.wait(timeout=3)
                except psutil.TimeoutExpired:
                    process.kill()

            # Subprocess'in gerçekten kapanması için işletim sistemine 1 saniye nefes payı ver
            time.sleep(1.0)
        except Exception as e:
            st.error(f"⚠️ Robot durdurulurken pürüz çıktı: {str(e)}")

    self_cleanup(account_id)
    return True


def stop_and_close_all(account_id: str) -> bool:
    """
    🔴 YALNIZCA kullanıcı Streamlit'ten açıkça "Durdur ve Tümünü Kapat" butonuna
    bastığında çağrılır.

    Botu durdurur, ardından hesaptaki TÜM robot pozisyonlarını ve bekleyen emirleri
    piyasa fiyatından kapatır. (Phase 4: Kapama yapabilen TEK otomatik aksiyon.)
    """
    stop_bot_process(account_id)

    try:
        accounts_path = os.path.join(project_root, "configs", "accounts.json")
        if not os.path.exists(accounts_path):
            return True
        with open(accounts_path, "r", encoding="utf-8") as f:
            accounts_data = json.load(f)
            accounts = (
                accounts_data
                if isinstance(accounts_data, list)
                else accounts_data.get("accounts", [])
            )

        active_account = next(
            (acc for acc in accounts if str(acc.get("login")) == account_id), None
        )
        if not active_account or mt5 is None:
            return True

        if connect_to_mt5(active_account):
            try:
                # 1. TÜM robot açık pozisyonları kapat
                positions = mt5.positions_get()
                if positions:
                    for pos in positions:
                        if BOT_MAGIC_MIN <= pos.magic < BOT_MAGIC_MAX:
                            close_position(mt5, pos, pos.symbol)

                # 2. Robotun bekleyen emirlerini sil
                cancel_all_pending_orders(mt5)
            finally:
                mt5.shutdown()
        else:
            st.warning("⚠️ MT5'e bağlanılamadı, pozisyonlar kapatılamadı!")
    except Exception as e:
        st.warning(f"⚠️ Tümünü kapatma sırasında hata oluştu: {e}")

    return True