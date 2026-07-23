# components/log_viewer.py
import streamlit as st
import os
from collections import deque

LOG_FILE = "grid_robot_log.txt"
MAX_LINES = 20  # Ekranda sadece en son 20 işlemi göster
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 Megabayt (Bayt cinsinden)

def get_recent_logs():
    """
    Log dosyasını çökmeye karşı korumalı bir şekilde okur.
    """
    if not os.path.exists(LOG_FILE):
        return "Henüz log kaydı bulunmuyor. Robotun başlaması bekleniyor..."
        
    # KORUMA 1: Dosya boyutu 2 MB'ı geçtiyse eski kayıtları temizle
    if os.path.getsize(LOG_FILE) > MAX_FILE_SIZE:
        try:
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                f.write("[SİSTEM KORUMASI] Dosya çok büyüdüğü için geçmiş loglar temizlendi.\n")
        except Exception:
            pass

    # KORUMA 2: Tüm dosyayı RAM'e almadan sadece son 20 satırı oku
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = deque(f, maxlen=MAX_LINES)
            return "".join(lines)
    except Exception as e:
        return f"[HATA] Loglar okunamadı: {e}"

def render_log_viewer():
    """
    Canlı Log Ekranı Bileşeni
    """
    st.subheader("📟 Canlı Sistem Logları")
    st.caption("Robotun arka planda yaptığı işlemlerin son 20 adımı (Güvenlik Kalkanı Aktif).")
    
    # Logları çek
    logs = get_recent_logs()
    
    # Terminal görünümü vermek için 'st.code' bileşenini kullanıyoruz
    st.code(logs, language="bash")