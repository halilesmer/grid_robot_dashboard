# src/core/bot_runner.py
import sys
import os
import json
import time
import threading
import io
from pathlib import Path

# Zwingt die Windows-Konsole dazu, UTF-8 (inkl. türkischer Zeichen) zu akzeptieren!
# Zwingt die Windows-Konsole dazu, UTF-8 zu akzeptieren UND sofort auf die Festplatte zu schreiben (Live-Modus)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding="utf-8",
        errors="replace",
        line_buffering=True,
        write_through=True,
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer,
        encoding="utf-8",
        errors="replace",
        line_buffering=True,
        write_through=True,
    )

# Proje kök dizinini Python yoluna ekle ki 'src' klasöründeki modülleri bulabilelim
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.utils.mt5_connection import connect_to_mt5_with_timeout

# 🌟 YENİ: Merkezi yol yöneticisini içeri aktarıyoruz
from src.utils.paths import get_metrics_path, get_sim_price_path

# 🌟 YENİ: MT5 "Source of Truth" senkronizasyonu ve kalıcı state dosyası
from src.utils.state_manager import build_synced_state, save_state, load_state


def export_metrics_loop(bot_engine, account_id):
    """
    Bu fonksiyon arka planda sürekli çalışarak robotun metriklerini okur
    ve Dashboard'un görebilmesi için bir JSON dosyasına yazar.
    Aynı zamanda Mac Test Modunda arayüzden gelen sahte fiyatı okur.
    """
    metrics_file = get_metrics_path(account_id)
    sim_file = get_sim_price_path(account_id)

    while bot_engine.IS_RUNNING:
        # 1. Metrikleri dışarı aktar (Arayüz görsün diye)
        if hasattr(bot_engine, "get_live_metrics"):
            try:
                metrics = bot_engine.get_live_metrics()
                tmp_metrics_file = metrics_file + ".tmp"
                with open(tmp_metrics_file, "w", encoding="utf-8") as f:
                    json.dump(metrics, f)
                os.replace(tmp_metrics_file, metrics_file)
            except Exception as e:
                pass  # Okuma hatası anlık olabilir, devam et.

        # 2. Arayüzden gelen sahte fiyatı (Simülatörü) içeri al
        if sys.platform != "win32" and os.path.exists(sim_file):
            try:
                with open(sim_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    bot_engine.SIMULATED_PRICE = data.get("price", 75.0)
            except Exception:
                pass

        time.sleep(1)


def main():
    # 1. Yöneticiden (bot_manager) gelen argümanları al
    if len(sys.argv) < 3:
        print("Kritik Hata: account_id veya model_name argümanları eksik.")
        sys.exit(1)

    account_id = sys.argv[1]
    model_name = sys.argv[2]

    # Kilit Nokta: config.py'nin Streamlit olmadan da hangi hesapta olduğunu bilmesi için
    # İşletim Sistemi ortam değişkenlerine hesap ID'sini kazıyoruz!
    os.environ["ACTIVE_ACCOUNT_ID"] = account_id

    print(f"[{account_id}] Isci Surec (Subprocess) baslatiliyor. Motor: {model_name}")

    # 2. Hesabı JSON'dan bul (Tam izolasyon)
    accounts_path = os.path.join(project_root, "configs", "accounts.json")
    try:
        with open(accounts_path, "r", encoding="utf-8") as f:
            accounts_data = json.load(f)
            # JSON formatına göre listeyi ayıkla
            if isinstance(accounts_data, list):
                accounts = accounts_data
            else:
                accounts = accounts_data.get("accounts", [])
    except Exception as e:
        print(f"Hesaplar dosyası okunamadı: {e}")
        sys.exit(1)

    # Parametre olarak gelen ID'ye sahip hesabı bul
    active_account = next(
        (acc for acc in accounts if str(acc.get("login")) == account_id), None
    )
    if not active_account:
        print(f"Hata: {account_id} ID'li hesap accounts.json içinde bulunamadı.")
        sys.exit(1)

    # 3. İstenen ticaret motorunu (model) yükle
    if model_name == "Model 1":
        import src.core.model_1 as bot_engine
    elif model_name == "Model 2":
        import src.core.model_2 as bot_engine
    else:
        import src.core.model_3 as bot_engine

    # 4. SADECE bu hesaba özel MT5 Terminaline bağlan
    print(f"[{account_id}] MT5 Terminaline bağlanılıyor...")
    # 🌟 ZAMAN AŞIMI KORUMASI: MT5 açılamazsa alt süreç de sessizce asılı kalmasın!
    connection_success, connection_timed_out = connect_to_mt5_with_timeout(
        active_account
    )
    if not connection_success:
        print(
            f"Hata: {account_id} için MetaTrader 5'e bağlanılamadı. Süreç sonlandırılıyor."
        )
        if connection_timed_out:
            startup_error_msg = (
                "MetaTrader 5 terminali zaman aşımı içinde açılamadı veya sunucuya "
                "ulaşılamadı. Lütfen MT5 terminalinin açık olduğundan ve ağ/internet "
                "bağlantınızın aktif olduğundan emin olun."
            )
        else:
            startup_error_msg = (
                "MetaTrader 5 terminaline giriş yapılamadı, sunucu/şifre bilgileri "
                "hatalı veya Algo Trading kapalı. Lütfen MT5 hesap bilgilerinizi ve "
                "terminal ayarlarını kontrol edin."
            )
        # 🔴 BAĞLANTI HATASINI ARAYÜZE İLET (Kalıcı hata afişi için)
        #    Süreç kapanıyor ama arayüz bu dosyayı okuyup net hata gösterebilecek.
        try:
            metrics_file = get_metrics_path(account_id)
            tmp_metrics_file = metrics_file + ".tmp"
            with open(tmp_metrics_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "profit": 0.0,
                        "open_positions": 0,
                        "pending_orders": 0,
                        "current_price": 0.0,
                        "algo_trading_error": False,
                        "remote_paused": False,
                        "mt5_connected": False,
                        "startup_error": startup_error_msg,
                    },
                    f,
                )
            os.replace(tmp_metrics_file, metrics_file)
        except Exception:
            pass
        sys.exit(1)

    print(f"[{account_id}] MT5 Bağlantısı Başarılı! Robot döngüsü başlıyor...")

    # 🚨 ESKİ PANİK MANTIĞI KALDIRILDI:
    #   Başlangıçta cancel_all_pending_orders(mt5) çağrısı artık YOK.
    #   Port değişimi / arayüz restart'ı / bilgisayar taşınması sonrası
    #   açık pozisyonlar ve bekleyen emirler ASLA kapatılmaz.

    # 🧠 PHASE 2: MT5 "Source of Truth" senkronizasyonu.
    #   Yerel dosyalara körü körüne güvenilmez; MT5'ten Account ID + Magic
    #   üzerinden canlı pozisyonlar/emirler sorgulanır, yerel config ile
    #   birleştirilir ve data/state_{account_id}.json yeniden inşa edilir.
    try:
        synced_state = build_synced_state(bot_engine, account_id, log_func=print)
        save_state(account_id, synced_state)
        print(
            f"[{account_id}] Kalıcı state dosyası yeniden inşa edildi: "
            f"data/state_{account_id}.json"
        )
    except Exception as e:
        print(
            f"[{account_id}] State senkronizasyonu başarısız oldu "
            f"(kritik değil, bot yine de başlatılıyor): {e}"
        )

    # İşlem öncesi motorun hafızasının tamamen temiz olduğundan emin ol
    bot_engine.IS_RUNNING = True
    if hasattr(bot_engine, "INITIAL_CLEANUP_DONE"):
        bot_engine.INITIAL_CLEANUP_DONE = False

    # 5. Metrikleri dışarı aktaran arka plan dinleyicisini başlat
    metrics_thread = threading.Thread(
        target=export_metrics_loop, args=(bot_engine, account_id), daemon=True
    )
    metrics_thread.start()

    # 6. Asıl Robot Döngüsünü başlat (Bu fonksiyon sonsuz döngüdür, süreci hayatta tutar)
    try:
        bot_engine.main_loop()
    except KeyboardInterrupt:
        print(f"[{account_id}] Süreç dışarıdan durduruldu (Graceful Shutdown).")
    finally:
        bot_engine.IS_RUNNING = False
        # 🧠 Kapanış anında son durumu MT5'ten çekip state dosyasına yaz (boş da olsa)
        try:
            final_state = build_synced_state(bot_engine, account_id, log_func=print)
            save_state(account_id, final_state)
        except Exception:
            pass
        print(f"[{account_id}] MT5 Bağlantısı kesiliyor ve süreç kapatılıyor.")


if __name__ == "__main__":
    main()
