import streamlit as st
import os
import json
from src.constants.tooltips import SETTINGS_TOOLTIPS
from src.components.dialogs import confirm_clear_dialog

def render_zone_controls(account_id: str, zones: list):
    """
    Her bir bölge (zone) için Başlat, Beklet ve Temizle butonlarını barındıran kontrol paneli.
    Butonlara basıldığında `logs/commands_{account_id}.json` dosyasına komut yazar.
    """
    st.markdown("### 🎛️ Bölge (Zone) Kontrolleri")

    if not zones:
        st.info("Henüz ayarlanmış bir bölge bulunmuyor.")
        return

    # Komutların yazılacağı dosya yolu
    commands_file = f"logs/commands_{account_id}.json"

    # Komut yazma yardımcı fonksiyonu
    def update_zone_command(zone_idx, state):
        # Olası bir State (Durum) kaybını önlemek için dosyayı fonksiyon tetiklendiğinde taze okuyoruz!
        current_commands = {}
        if os.path.exists(commands_file):
            try:
                with open(commands_file, "r", encoding="utf-8") as f:
                    current_commands = json.load(f)
            except Exception:
                pass

        current_commands[str(zone_idx)] = {"state": state}
        os.makedirs(os.path.dirname(commands_file), exist_ok=True)

        # Race condition önleme: atomik yazma işlemi
        tmp_file = commands_file + ".tmp"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(current_commands, f)
            os.replace(tmp_file, commands_file)
            st.toast(f"Bölge {zone_idx + 1} için '{state}' komutu gönderildi.", icon="✅")
        except Exception as e:
            st.error(f"Komut gönderilirken hata oluştu: {e}")

    # Header
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    col1.markdown("**Bölge**")
    col2.markdown("**Başlat**")
    col3.markdown("**Beklet**")
    col4.markdown("**Temizle**")
    st.markdown("---")

    for idx, zone in enumerate(zones):
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

        with c1:
            st.markdown(f"**Bölge {idx + 1}**\n<br/><small>${zone.get('min_price')} - ${zone.get('max_price')}</small>", unsafe_allow_html=True)

        with c2:
            if st.button("▶️ Başlat", key=f"start_btn_{account_id}_{idx}", help=SETTINGS_TOOLTIPS.get("ZONE_START", "Bölgeyi aktif hale getirir, emir göndermeye başlar.")):
                update_zone_command(idx, "START")

        with c3:
            if st.button("⏸️ Beklet", key=f"pause_btn_{account_id}_{idx}", help=SETTINGS_TOOLTIPS.get("ZONE_PAUSE", "Bekleyen emirleri iptal eder ama açık pozisyonlara dokunmaz.")):
                update_zone_command(idx, "PAUSE")

        with c4:
            if st.button(
                "🗑️ Temizle",
                type="primary",
                key=f"clear_btn_{account_id}_{idx}",
                help=SETTINGS_TOOLTIPS.get(
                    "ZONE_CLEAR",
                    "Bekleyen emirleri siler ve AÇIK POZİSYONLARI piyasa fiyatından kapatır.",
                ),
            ):
                confirm_clear_dialog(lambda i=idx: update_zone_command(i, "CLEAR"))

        st.markdown("---")
