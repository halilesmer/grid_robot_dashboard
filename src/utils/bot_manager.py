# src/utils/bot_manager.py
import subprocess
import sys
import os
import streamlit as st

# GLOBALE VARIABLE (Sicher vor Streamlit-Abstürzen!)
_ACTIVE_BOTS = {}


def is_bot_running(account_id: str) -> bool:
    """Belirli bir hesabın robotunun arka planda sağlıklı çalışıp çalışmadığını kontrol eder (Crash Detection)."""
    if account_id in _ACTIVE_BOTS:
        process = _ACTIVE_BOTS[account_id]
        # poll() None dönüyorsa süreç hala hayattadır.
        if process.poll() is None:
            return True
        else:
            # Robot kendi kendine durmuş veya MT5 çökmüş. Temizliğini yap!
            del _ACTIVE_BOTS[account_id]
            return False
    return False


def start_bot_process(account_id: str, model_name: str) -> bool:
    """Belirli bir hesap için izole bir Subprocess (alt süreç) başlatır."""
    if is_bot_running(account_id):
        return True  # Zaten çalışıyor

    try:
        # Her hesaba özel log dosyası oluştur
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, f"bot_{account_id}_error.log")

        # Log dosyasını 'append' (ekleme) modunda aç
        log_file = open(log_file_path, "a", encoding="utf-8")

        # Ayrı bir Python programı olarak botu tetikle.
        # DÜZELTME: "-u" (unbuffered) ekledik ki loglar anında dosyaya yazılsın!
        process = subprocess.Popen(
            [sys.executable, "-u", "src/core/bot_runner.py", account_id, model_name],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Mükemmel izolasyon: Süreci SADECE global değişkene yazıyoruz, session_state'e DEĞİL!
        _ACTIVE_BOTS[account_id] = process
        return True

    except Exception as e:
        # Profesyonel hata yakalama: Çökme durumunda arayüze net bilgi ver
        st.error(
            f"🚨 Sistem Hatası: {account_id} için robot başlatılamadı!\n\nDetay: {str(e)}"
        )
        return False


def stop_bot_process(account_id: str) -> bool:
    """Çalışan robotu güvenli ve temiz bir şekilde (Graceful shutdown) durdurur."""
    if account_id in _ACTIVE_BOTS:
        process = _ACTIVE_BOTS[account_id]
        try:
            process.terminate()  # Güvenli kapanma sinyali gönder
            try:
                process.wait(timeout=3)  # 3 saniye bekle
            except subprocess.TimeoutExpired:
                process.kill()  # Kapanmamakta direnirse zorla kapat (Kill)
        except Exception as e:
            st.error(f"⚠️ Robot durdurulurken pürüz çıktı: {str(e)}")
        finally:
            # İşlem bittiğinde global listeden sil
            del _ACTIVE_BOTS[account_id]
            return True

    return False
