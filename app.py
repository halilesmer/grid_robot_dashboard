# app.py

import sys
import os
import json
from pathlib import Path
import platform
import time
import streamlit as st


def get_current_version():
    """VERSION dosyasından en güncel sürüm numarasını okur."""
    version_file = Path(__file__).parent / "VERSION"
    if os.path.exists(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return "v1.0.0"  # Varsayılan başlangıç sürümü


# ==========================================
# 1. YOL AYARLARI (Python'a src klasörünü gösteriyoruz - EN ÜSTTE OLMALI)
# ==========================================
sys.path.append(str(Path(__file__).parent / "src"))


# ==========================================
# 2. ORTAM VE SAYFA AYARI (İLK STREAMLIT KOMUTU)
# ==========================================
env = os.getenv("ROBOT_ENV", "TEST").upper()

if env == "LIVE":
    PAGE_TITLE = f"🔴 [LIVE] Grid Robot Control ({get_current_version()})"
    PAGE_ICON = "🔴"
else:
    PAGE_TITLE = f"🧪 [TEST] Grid Robot Control ({get_current_version()})"
    PAGE_ICON = "🧪"

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")


# ==========================================
# 3. KENDİ MODÜLLERİMİZİ İÇE AKTARMA
# ==========================================
from src.utils.bot_manager import (
    is_bot_running,
    start_bot_process,
    stop_bot_process,
)
from src.components.account_selector import render_account_selector
from src.components.chart_viewer import render_chart
from src.components.dialogs import confirm_stop_motor_dialog
from src.utils.mt5_connection import (
    connect_to_mt5_with_timeout,
    shutdown_mt5,
)
from src.components.header import render_main_title
from src.components.settings_panel import render_settings_panel
from src.components.log_viewer import render_log_viewer
from src.styles.custom_css import apply_custom_css
from src.utils.config import load_settings, save_settings

# 🌟 YENİ: Merkezi yol yöneticisi
from src.utils.paths import get_metrics_path, get_sim_price_path, get_ui_state_path

import src.core.model_2 as model_2

# 🔍 DONMA TEŞHİSİ: Her script çalıştırmasının aşama sürelerini logs/run_profiler.log'a yazar
from src.utils.profiler import run_start, stage

# 🔍 Yeni script çalıştırması başladı (takılma anında son satır kalan aşamayı gösterir)
run_start(os.getenv("ROBOT_ENV", "TEST"))


def get_live_metrics_from_file(account_id):
    """Liest die aktuellsten Metriken des Subprozesses aus der JSON-Datei."""
    metrics_file = get_metrics_path(account_id)
    if os.path.exists(metrics_file):
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            age = time.time() - os.path.getmtime(metrics_file)
            data.setdefault("mt5_connected", True)
            data.setdefault("startup_error", None)
            # Eski (bayat) bir başlangıç hatası afişi, 30 saniyeden eskiyse gösterilmez
            if data.get("startup_error") and age > 30:
                data["startup_error"] = None
            return data
        except Exception:
            pass  # Wenn die Datei exakt in dieser Millisekunde geschrieben wird
    return {
        "profit": 0.0,
        "open_positions": 0,
        "pending_orders": 0,
        "current_price": 0.0,
        "algo_trading_error": False,
        "remote_paused": False,
        "mt5_connected": True,
        "startup_error": None,
    }


# ==========================================
# 1. STREAMLIT CONFIG & CSS
# ==========================================
apply_custom_css()

# 🌟 YENİ: Başlık En Üste Geldi
render_main_title()
stage("CSS + başlık")

# ==========================================
# 2. ÖNCE HESABI SEÇ (TAM GENİŞLİKTE)
# ==========================================
active_account = render_account_selector()
stage("Hesap seçici")

# Güvenlik: Eğer JSON dosyasında hiç hesap yoksa veya hata varsa programı burada durdur.
if not active_account:
    st.stop()

# Seçili hesabın benzersiz ID'sini alıyoruz
account_id = str(active_account.get("login", "default"))

# ==========================================
# MOTOR SEÇİMİ (TEK KRAL: MODEL 2)
# ==========================================
bot_engine = model_2


st.markdown("---")

# ==========================================
# 3. GÜNCEL ÇALIŞMA DURUMUNU SORGULA (CRASH DETECTION)
# ==========================================
# Durumu globalden değil, Bot Manager'dan SADECE bu hesap için soruyoruz
account_is_running = is_bot_running(account_id)
stage("Bot durumu sorgusu (is_bot_running)")


# ==========================================
# 4. AYARLARI VE METRİKLERİ YÜKLE
# ==========================================
current_settings = load_settings("Model 2")

# Canlı verileri JSON dosyasından çek (Çünkü robot artık Subprocess olarak çalışıyor)
# Dosya her zaman okunur: Başlangıç hatası (startup_error) afişi buradan beslenir.
live_data = get_live_metrics_from_file(account_id)
stage("Ayarlar + metrik yükleme")


# ==========================================
# ALGO TRADING GÜVENLİK UYARISI
# ==========================================
if live_data.get("algo_trading_error", False):
    st.error(
        "🚨 **KRİTİK HATA:** MetaTrader 5'te **'Algo Trading' (Otomatik Ticaret)** kapalı! "
        "Robot emir gönderemiyor. Lütfen MT5 terminalinin üst menüsünden 'Algo Trading' butonunu aktif (yeşil) hale getirin.",
        icon="🚫",
    )

    if account_is_running:
        stop_bot_process(account_id)
        st.toast("🛑 Bağlantı kilitlendi: Algo Trading kapalı!", icon="⚠️")
        st.rerun()


# 🔴 MT5 BAĞLANTISI KOPTU/BULUNAMADI UYARISI (Subprocess'ten gelen canlı durum)
if live_data.get("startup_error"):
    st.error(
        f"🚨 **MT5 BAĞLANTI HATASI:** {live_data.get('startup_error')}",
        icon="🚫",
    )
elif account_is_running and not live_data.get("mt5_connected", True):
    st.error(
        "🚨 **KRİTİK HATA:** MetaTrader 5 ile bağlantı KOPTU! "
        "Robot çalışıyor ama MT5'e ulaşamıyor. "
        "MT5 terminalinin açık ve ağ bağlantınızın aktif olduğunu kontrol edin. "
        "Bağlantı geri gelince robot otomatik olarak devam edecek.",
        icon="🚫",
    )


# 📡 Mobil MT5'ten (Sinyal Emri ile) uzaktan durduruldu mu?
if live_data.get("remote_paused", False) and account_is_running:
    st.warning(
        "📡 **Sistem Mobil MT5'ten UZAKTAN DURDURULDU.** "
        "Bekleyen emirler silindi, açık pozisyonlar korundu. "
        "Tekrar bağlanmak için yukarıdaki **MT5'e Bağlan** butonunu kullanın "
        "(mobil MT5'te 1$ Buy Limit yalnızca durdurmak içindir).",
        icon="⏸️",
    )
stage("Hata/uyarı afişleri")


# 🌟 MT5 bağlantı tetikleyicisi artık settings_panel üzerinden yönetiliyor
action = None
if st.session_state.get(f"motor_toggle_{account_id}"):
    action = "TOGGLE"
    st.session_state[f"motor_toggle_{account_id}"] = False

# ==========================================
# BAŞLAT / DURDUR MANTIĞI (SUBPROCESS İLE)
# ==========================================
if action == "TOGGLE":
    if not account_is_running:
        # Önce MT5 bağlantısını test et.
        # 🌟 YENİ: Zaman aşımlı bağlantı — MT5 açılamaz/ulaşılamazsa arayüz ASLA donmaz!
        with st.spinner("🔄 MT5 terminaline bağlanılıyor..."):
            connection_success, connection_timed_out = connect_to_mt5_with_timeout(
                active_account
            )
        stage("MT5 bağlantı denemesi")

        if connection_success:
            # 🌟 CRİTİK: Test bağlantısını serbest bırak! Alt süreç (bot_runner) aynı
            # terminale bağlanırken IPC timeout (-10005) yaşamamak için arayüz artık
            # terminali meşgul etmemeli.
            shutdown_mt5()
            # Subprocess (Alt Süreç) başlat!
            if start_bot_process(account_id, "Model 2"):
                st.toast(
                    f"🚀 {active_account['account_name']} için robot izole olarak başlatıldı!",
                    icon="✅",
                )
                st.rerun()
            else:
                st.error(
                    "🔴 **Robot Başlatılamadı!** Lütfen hata kayıtlarını (logs) inceleyin.",
                    icon="❌",
                )
        else:
            # 🌟 EKLENDİ: Bağlantı başarısız olursa KALICI ve net hata göster
            if connection_timed_out:
                st.error(
                    "🔴 **MT5 BAĞLANTI ZAMAN AŞIMI!** Terminal açılamadı veya sunucuya "
                    "ulaşılamadı. MT5 terminalinin açık olduğundan ve ağ/internet "
                    "bağlantınızın aktif olduğundan emin olun, sonra tekrar deneyin.",
                    icon="🚨",
                )
            else:
                st.error(
                    "🔴 **MT5 BAĞLANTI HATASI!** Terminal açılamadı veya hesap giriş "
                    "bilgileri (sunucu/şifre) yanlış. Lütfen MT5 terminalinin açık "
                    "olduğunu ve hesap bilgilerinizin doğruluğunu kontrol edin.",
                    icon="🚨",
                )
    else:
        # MT5 bağlantısı kesilir; AÇIK POZİSYONLARA ASLA DOKUNULMAZ.
        confirm_stop_motor_dialog(
            account_id,
            on_stop_func=stop_bot_process,
        )


# ==========================================
# 🌟 GİZLİ BEKÇİ (EVENT-DRIVEN WATCHER)
# ==========================================
@st.fragment(run_every="1.5s")
def remote_signal_watcher(acc_id, is_running):
    if not is_running:
        return
    ui_file = get_ui_state_path(acc_id)
    if not os.path.exists(ui_file):
        return
    try:
        with open(ui_file, "r", encoding="utf-8") as f:
            disk_states = json.load(f)

        ui_state_key = f"ui_zone_states_{acc_id}"
        zones_session_key = f"model2_zones_{acc_id}"

        if zones_session_key in st.session_state and ui_state_key in st.session_state:
            memory_states = st.session_state[ui_state_key]
            need_rerun = False

            for i, z in enumerate(st.session_state[zones_session_key]):
                disk_val = disk_states.get(str(i))
                zone_id = z.get("id")
                mem_val = memory_states.get(zone_id)

                # Sadece MT5'ten sinyal gelir ve diskteki durum hafızadakinden farklı olursa tetikle
                if disk_val in ("AUTO_CLEAR", "PAUSE", "START") and disk_val != mem_val:
                    st.session_state[ui_state_key][zone_id] = disk_val
                    need_rerun = True

            if need_rerun:
                st.rerun()
    except Exception:
        pass


# Bekçiyi panelden hemen önce çalıştır
remote_signal_watcher(account_id, account_is_running)

# ==========================================
# AYARLAR VE MAC SİMÜLATÖRÜ
# ==========================================
updated_settings = render_settings_panel(
    current_settings,
    "Model 2",
    account_id,
    live_data,
    active_account,
    account_is_running,
)

if updated_settings:
    save_settings(updated_settings, "Model 2")
    st.success(f"✅ Ayarlar başarıyla güncellendi ve {account_id} için kaydedildi!")
    st.rerun()

stage("Ayarlar paneli render")

st.divider()

current_active_price = live_data.get("current_price", 0.0)

if platform.system() != "Windows":
    st.warning("💻 Mac Test Modu Aktif - Fiyat Simülatörü")
    mock_price = st.slider(
        "Canlı Fiyatı Belirle (USOUSD)",
        min_value=50.0,
        max_value=150.0,
        value=75.0,
        step=0.10,
    )
    current_active_price = mock_price
    bot_engine.SIMULATED_PRICE = mock_price  # Arayüzün kendi grafiği için

    # YENİ: Alt sürece (backend) fiyatı iletmek için köprü kuruyoruz
    sim_file_path = get_sim_price_path(account_id)
    try:
        tmp_sim = sim_file_path + ".tmp"
        with open(tmp_sim, "w", encoding="utf-8") as f:
            json.dump({"price": mock_price}, f)
        os.replace(tmp_sim, sim_file_path) # Atomik değişim
    except Exception:
        pass

# ==========================================
# GRAFİK VE LOG EKRANI (İşletim Sistemine Göre Dinamik)
# ==========================================
if platform.system() != "Windows":
    # Mac ortamında: Grafik ve Log yan yana (Grafik daha geniş)
    col_chart, col_log = st.columns([2, 1])
    with col_chart:
        render_chart(current_active_price, current_settings, "Model 2")
    with col_log:
        render_log_viewer(account_id)
else:
    # Windows ortamında: Grafik GİZLİ, Loglar TAM EKRAN GENİŞLİĞİNDE
    st.markdown("---")
    render_log_viewer(account_id)

stage("END — Grafik + log ekranı (script sonu)")
