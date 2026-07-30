# src/core/bot_runner.py
import sys
import os
import json
import time
import threading
from pathlib import Path

# Proje kök dizinini Python yoluna ekle ki 'src' klasöründeki modülleri bulabilelim
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.utils.mt5_connection import connect_to_mt5


def export_metrics_loop(bot_engine, account_id):
    """
    Bu fonksiyon arka planda sürekli çalışarak robotun metriklerini okur
    ve Dashboard'un görebilmesi için bir JSON dosyasına yazar.
    """
    metrics_file = os.path.join(project_root, "logs", f"live_metrics_{account_id}.json")
    os.makedirs(os.path.dirname(metrics_file), exist_ok=True)

    while bot_engine.IS_RUNNING:
        if hasattr(bot_engine, "get_live_metrics"):
            try:
                metrics = bot_engine.get_live_metrics()
                with open(metrics_file, "w", encoding="utf-8") as f:
                    json.dump(metrics, f)
            except Exception as e:
                pass  # Okuma hatası anlık olabilir, devam et.
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

    print(f"[{account_id}] İşçi Süreç (Subprocess) başlatılıyor. Motor: {model_name}")

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
    if not connect_to_mt5(active_account):
        print(
            f"Hata: {account_id} için MetaTrader 5'e bağlanılamadı. Süreç sonlandırılıyor."
        )
        sys.exit(1)

    print(f"[{account_id}] MT5 Bağlantısı Başarılı! Robot döngüsü başlıyor...")

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
        print(f"[{account_id}] MT5 Bağlantısı kesiliyor ve süreç kapatılıyor.")


if __name__ == "__main__":
    main()
