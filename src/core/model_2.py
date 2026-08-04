import time
import datetime
import platform
import json
import os
from src.utils.trade_utils import safe_send_order, close_position
from src.utils.config import get_settings_file

# ==========================================
# TEMEL DEĞİŞKENLER VE AYARLAR
# ==========================================
LOOP_INTERVAL_SECONDS = 1.0
ZONES = []
ORDER_TYPE = "BUY"  # Sadece ilk başlatma koruması için tutuluyor
SYMBOL = "USOUSD"

# ==========================================
# GLOBAL DEĞİŞKENLER (Bot Manager İçin Zorunlu)
# ==========================================
SYMBOL_INFO = None
FILLING_MODE = None
ACTIVE_ZONE = None
ACTIVE_ZONE_IDX = None

IS_RUNNING = False
INITIAL_CLEANUP_DONE = False
SIMULATED_PRICE = 0.0

active_zones_state = {}  # Hafıza Kurtarma ve Zombi Emir Yönetimi


# ==========================================
# METRİK ARAYÜZÜ (Dashboard için)
# ==========================================
def get_live_metrics():
    metrics = {
        "profit": 0.0,
        "open_positions": 0,
        "pending_orders": 0,
        "current_price": 0.0,
        "algo_trading_error": False,
    }

    if mt5 is None or IS_MAC_TEST_MODE:
        if SIMULATED_PRICE > 0:
            metrics["current_price"] = SIMULATED_PRICE
        return metrics

    terminal_info = mt5.terminal_info()
    if terminal_info is None:
        return metrics

    if not terminal_info.trade_allowed:
        metrics["algo_trading_error"] = True

    positions = mt5.positions_get(symbol=SYMBOL)
    if positions:
        metrics["open_positions"] = len(positions)
        metrics["profit"] = round(sum(pos.profit for pos in positions), 2)

    orders = mt5.orders_get(symbol=SYMBOL)
    if orders:
        metrics["pending_orders"] = len(orders)

    tick = mt5.symbol_info_tick(SYMBOL)
    if tick:
        metrics["current_price"] = tick.bid
    elif SIMULATED_PRICE > 0:
        metrics["current_price"] = SIMULATED_PRICE

    return metrics


# ==========================================
# GÜVENLİ YÜKLEME VE LOGLAMA FONKSİYONLARI
# ==========================================
def load_dynamic_settings():
    global ZONES, LOOP_INTERVAL_SECONDS, SYMBOL

    try:
        settings_file = get_settings_file("Model 2")
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)
            ZONES = settings.get("ZONES", [])
            LOOP_INTERVAL_SECONDS = settings.get("LOOP_INTERVAL_SECONDS", 1.0)

            # Dinamik sembol vizyonu için global sembolü de güncelliyoruz
            if ZONES and "symbol" in ZONES[0]:
                SYMBOL = ZONES[0]["symbol"]
    except Exception:
        pass


def log_message(msg, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [{level}] {msg}"
    print(formatted)


# ===============================================================================
# 🍏🪟 MAC / WINDOWS UYUMLULUK KÖPRÜSÜ
# ===============================================================================
try:
    # 🚨 KESİN KONTROL: Eğer kütüphane varsa KESİNLİKLE gerçek MT5'i kullan!
    import MetaTrader5 as mt5

    IS_MAC_TEST_MODE = False

    def set_mock_price(new_price):
        pass

except ImportError:
    # Gerçek kütüphane YOKSA (Geliştirici Mac'indeysen) Sahte Moda Geç
    IS_MAC_TEST_MODE = True
    print(
        "⚠️ UYARI: MetaTrader5 kütüphanesi bulunamadı! MT5 Sahte (Mock) modda çalışıyor!"
    )
    MOCK_CURRENT_PRICE = 75.00

    def set_mock_price(new_price):
        global MOCK_CURRENT_PRICE
        MOCK_CURRENT_PRICE = new_price

    class DummyMT5:
        def __init__(self):
            self.dummy_orders = []
            self.ticket_counter = 1

        TRADE_ACTION_DEAL = 1
        TRADE_ACTION_PENDING = 5
        TRADE_ACTION_REMOVE = 8
        TRADE_ACTION_SLTP = 6
        ORDER_TYPE_BUY_LIMIT = 2
        ORDER_TYPE_BUY_STOP = 4
        ORDER_TYPE_SELL_LIMIT = 3
        ORDER_TYPE_SELL_STOP = 5
        POSITION_TYPE_BUY = 0
        POSITION_TYPE_SELL = 1
        ORDER_TIME_GTC = 0
        ORDER_FILLING_IOC = 1
        ORDER_FILLING_FOK = 0
        ORDER_FILLING_RETURN = 2
        TRADE_RETCODE_DONE = 10009

        def initialize(self):
            return True

        def shutdown(self):
            pass

        def last_error(self):
            return (1, "Mock Error")

        def terminal_info(self):
            class TerminalInfo:
                trade_allowed = True

            return TerminalInfo()

        def symbol_info(self, symbol):
            class SymbolInfo:
                visible = True
                trade_mode = 4
                filling_mode = 1
                point = 0.01
                digits = 2
                volume_min = 0.01
                volume_max = 100.0
                volume_step = 0.01

            return SymbolInfo()

        def symbol_select(self, symbol, visible):
            return True

        def symbol_info_tick(self, symbol):
            class Tick:
                bid = MOCK_CURRENT_PRICE
                ask = MOCK_CURRENT_PRICE + 0.05

            return Tick()

        def orders_get(self, symbol=None):
            return self.dummy_orders

        def positions_get(self, symbol=None):
            return []

        def order_check(self, request):
            class CheckResult:
                retcode = 0

            return CheckResult()

        def order_send(self, request):
            class SendResult:
                retcode = 10009

            if request.get("action") == self.TRADE_ACTION_PENDING:

                class DummyOrder:
                    def __init__(self, ticket, magic, price, type_):
                        self.ticket = ticket
                        self.magic = magic
                        self.price_open = price
                        self.type = type_

                new_order = DummyOrder(
                    self.ticket_counter,
                    request.get("magic"),
                    request.get("price"),
                    request.get("type"),
                )
                self.dummy_orders.append(new_order)
                self.ticket_counter += 1
            elif request.get("action") == self.TRADE_ACTION_REMOVE:
                ticket_to_remove = request.get("order")
                self.dummy_orders = [
                    o for o in self.dummy_orders if o.ticket != ticket_to_remove
                ]
            return SendResult()


if IS_MAC_TEST_MODE:
    mt5 = DummyMT5()

# ═══════════════════════════════════════════════════════════════════════════════
# KULLANICI AYARLARI
# ═══════════════════════════════════════════════════════════════════════════════

BASE_MAGIC_NUMBER = 200000
MAX_DEVIATION = 20
MARKET_CLOSED_CHECK_INTERVAL = 60
LOG_TO_FILE = True
LOG_FILE_PATH = "logs/grid_robot_log.txt"


def normalize_price(price):
    if SYMBOL_INFO is None:
        return round(price, 2)
    point = SYMBOL_INFO.point
    if point == 0:
        return price
    return round(round(price / point) * point, SYMBOL_INFO.digits)


def normalize_volume(volume):
    if SYMBOL_INFO is None:
        return volume
    volume = max(SYMBOL_INFO.volume_min, min(volume, SYMBOL_INFO.volume_max))
    if SYMBOL_INFO.volume_step > 0:
        steps = round((volume - SYMBOL_INFO.volume_min) / SYMBOL_INFO.volume_step)
        volume = SYMBOL_INFO.volume_min + steps * SYMBOL_INFO.volume_step
    return round(volume, 8)


def get_current_market_price(direction="BUY"):
    global SIMULATED_PRICE
    if IS_MAC_TEST_MODE and SIMULATED_PRICE > 0:
        return SIMULATED_PRICE

    try:
        tick = mt5.symbol_info_tick(SYMBOL)
        if tick is None:
            return None
        return tick.ask if direction == "BUY" else tick.bid
    except Exception as e:
        log_message(f"Fiyat alınamadı: {e}", "ERROR")
        return None


def is_market_open():
    info = mt5.symbol_info(SYMBOL)
    return False if info is None else info.trade_mode == 4


def determine_fill_mode():
    global FILLING_MODE
    if SYMBOL_INFO is None:
        return None
    if SYMBOL_INFO.filling_mode & 2:
        FILLING_MODE = mt5.ORDER_FILLING_IOC
    elif SYMBOL_INFO.filling_mode & 1:
        FILLING_MODE = mt5.ORDER_FILLING_FOK
    else:
        FILLING_MODE = mt5.ORDER_FILLING_RETURN
    return FILLING_MODE


def get_all_robot_orders():
    orders = mt5.orders_get(symbol=SYMBOL)
    if orders is None:
        return None
    return [
        o for o in orders if BASE_MAGIC_NUMBER <= o.magic < BASE_MAGIC_NUMBER + 1000
    ]


def get_all_robot_positions():
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions is None:
        return None
    return [
        p for p in positions if BASE_MAGIC_NUMBER <= p.magic < BASE_MAGIC_NUMBER + 1000
    ]


def get_all_manual_positions():
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions is None:
        return None
    return [
        p
        for p in positions
        if not (BASE_MAGIC_NUMBER <= p.magic < BASE_MAGIC_NUMBER + 1000)
    ]


def get_existing_levels_by_direction(grid_step):
    buy_levels = set()
    sell_levels = set()

    orders = get_all_robot_orders()
    r_pos = get_all_robot_positions()
    m_pos = get_all_manual_positions()

    def add_to_set(price, is_buy):
        snapped = round(price / grid_step) * grid_step
        if is_buy:
            buy_levels.add(normalize_price(snapped))
        else:
            sell_levels.add(normalize_price(snapped))

    if orders:
        for o in orders:
            is_buy = o.type in [mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_BUY_STOP]
            add_to_set(o.price_open, is_buy)
    if r_pos:
        for p in r_pos:
            add_to_set(p.price_open, p.type == mt5.POSITION_TYPE_BUY)
    if m_pos:
        for p in m_pos:
            add_to_set(p.price_open, p.type == mt5.POSITION_TYPE_BUY)

    return buy_levels, sell_levels


def cancel_order(order):
    request = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": order.ticket,
        "symbol": SYMBOL,
    }
    return safe_send_order(mt5, request, log_message)


def modify_position_tp_sl(position, tp_price, sl_price=None):
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": position.ticket,
        "symbol": SYMBOL,
        "tp": tp_price,
    }
    if sl_price is not None and sl_price > 0:
        request["sl"] = sl_price
    return safe_send_order(mt5, request, log_message)


def get_mt5_timeframe(tf_str):
    if IS_MAC_TEST_MODE:
        return 0
    mapping = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }
    return mapping.get(tf_str, mt5.TIMEFRAME_M15)


# 1. ESKİ get_active_zone FONKSİYONUNU BUNUNLA DEĞİŞTİR (Giriş/Çıkış Asimetrisi Çözümü)
def get_active_zone(tick_price):
    for i, zone in enumerate(ZONES):
        z_min = float(zone.get("min_price", 0))
        z_max = float(zone.get("max_price", 0))
        cond = zone.get("exit_condition", "Anlık Fiyat")

        if cond == "Anlık Fiyat":
            if z_min <= tick_price <= z_max:
                return zone, i
        else:
            # Bölgenin kuralı "Mum Kapanışı" ise, giriş için de mum kapanışını kontrol et
            tf_str = zone.get("exit_timeframe", "M15")
            tf = get_mt5_timeframe(tf_str)
            if IS_MAC_TEST_MODE:
                close_price = tick_price
            else:
                rates = mt5.copy_rates_from_pos(SYMBOL, tf, 1, 1)  # Son kapanan mumu al
                if rates is not None and len(rates) > 0:
                    close_price = (
                        rates[0]["close"]
                        if isinstance(rates[0], dict)
                        else getattr(
                            rates[0],
                            "close",
                            (
                                rates[0][4]
                                if isinstance(rates[0], tuple)
                                else rates[0]["close"]
                            ),
                        )
                    )
                else:
                    close_price = tick_price

            if z_min <= close_price <= z_max:
                return zone, i

    return None, None


def send_pending_order(
    price, lot, tp_price, sl_price=None, zone_idx=0, direction="BUY"
):
    current_price = get_current_market_price(direction)
    if current_price is None:
        return False

    if direction == "BUY":
        order_type = (
            mt5.ORDER_TYPE_BUY_LIMIT
            if price < current_price
            else mt5.ORDER_TYPE_BUY_STOP
        )
    else:
        order_type = (
            mt5.ORDER_TYPE_SELL_LIMIT
            if price > current_price
            else mt5.ORDER_TYPE_SELL_STOP
        )

    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": SYMBOL,
        "volume": normalize_volume(lot),
        "type": order_type,
        "price": price,
        "deviation": MAX_DEVIATION,
        "magic": BASE_MAGIC_NUMBER + zone_idx + 1,
        "comment": f"Model2_Zone{zone_idx + 1}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": (
            FILLING_MODE if FILLING_MODE is not None else mt5.ORDER_FILLING_IOC
        ),
        "tp": tp_price,
    }
    if sl_price is not None and sl_price > 0:
        request["sl"] = sl_price

    return safe_send_order(mt5, request, log_message)


# ═══════════════════════════════════════════════════════════════════════════════
# ANA DİNAMİK YÖNETİM MOTORU (MODEL 2)
# ═══════════════════════════════════════════════════════════════════════════════
def process_zone_commands():
    global active_zones_state
    account_id = os.environ.get("ACTIVE_ACCOUNT_ID", "default")

    # Yalnızca Kalıcı UI Hafızasını Oku (Arayüz Köprüsüne Sadık Kalarak)
    ui_states_file = f"logs/ui_states_{account_id}.json"
    if os.path.exists(ui_states_file):
        try:
            with open(ui_states_file, "r", encoding="utf-8") as f:
                ui_states = json.load(f)
                for zone_idx_str, state in ui_states.items():
                    # 🚨 DİKKAT: MT5 Magic eşleşmesi için burası KESİNLİKLE 'int' kalmalı!
                    active_zones_state[int(zone_idx_str)] = state
        except Exception:
            pass


# 2. ESKİ manage_dynamic_grid FONKSİYONUNU BUNUNLA DEĞİŞTİR (Canlı Güncelleme Çözümü)
def manage_dynamic_grid():
    global ACTIVE_ZONE, ACTIVE_ZONE_IDX

    process_zone_commands()

    # CANLI AYAR GÜNCELLEMESİ (Stale Reference Koruması)
    if ACTIVE_ZONE_IDX is not None and ACTIVE_ZONE_IDX < len(ZONES):
        ACTIVE_ZONE = ZONES[ACTIVE_ZONE_IDX]

    robot_positions = get_all_robot_positions()
    robot_orders = get_all_robot_orders()

    if robot_positions is None or robot_orders is None:
        return False

    current_price_buy = get_current_market_price("BUY")
    current_price_sell = get_current_market_price("SELL")
    if current_price_buy is None or current_price_sell is None:
        return False

    current_avg_price = (current_price_buy + current_price_sell) / 2.0

    # 1. ZOMBİ EMİR TEMİZLİĞİ VE BÖLGE KAPATMA
    for order in robot_orders:
        order_zone_idx = order.magic - BASE_MAGIC_NUMBER - 1
        if active_zones_state.get(order_zone_idx, "START") != "START":
            log_message(
                f"🧹 Bölge {order_zone_idx+1} pasif, emir siliniyor. (Bilet: {order.ticket})"
            )
            cancel_order(order)

    for pos in robot_positions:
        pos_zone_idx = pos.magic - BASE_MAGIC_NUMBER - 1
        if active_zones_state.get(pos_zone_idx, "START") == "CLEAR":
            log_message(
                f"🧹 BÖLGE {pos_zone_idx+1} KULLANICI EMRİYLE SIFIRLANIYOR: Pozisyon kapatılıyor."
            )
            close_position(mt5, pos, SYMBOL, log_message)

    robot_orders = get_all_robot_orders()
    robot_positions = get_all_robot_positions()
    if robot_orders is None or robot_positions is None:
        return False

    # 2. KISMİ DOLUM (PARTIAL FILL) KONTROLÜ - ÇİFT YÖNLÜ
    for pos in robot_positions:
        pos_zone_idx = pos.magic - BASE_MAGIC_NUMBER - 1
        if 0 <= pos_zone_idx < len(ZONES):
            target_lot = max(
                0.01, min(5.0, float(ZONES[pos_zone_idx].get("lot_size", 0.01)))
            )
            remaining_lot = round(target_lot - pos.volume, 8)
            vol_min = SYMBOL_INFO.volume_min if SYMBOL_INFO else 0.01

            if remaining_lot >= vol_min:
                has_pending = any(
                    o.magic == pos.magic
                    and abs(o.price_open - pos.price_open)
                    < (SYMBOL_INFO.point * 2 if SYMBOL_INFO else 0.02)
                    for o in robot_orders
                )

                if (
                    not has_pending
                    and active_zones_state.get(pos_zone_idx, "START") == "START"
                ):
                    direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                    log_message(
                        f"🔄 Kısmi Dolum: Bölge {pos_zone_idx+1} | Kalan {remaining_lot} lot ({direction}) emir gönderiliyor."
                    )

                    tp_val = float(ZONES[pos_zone_idx].get("take_profit", 0.05))
                    sl_val = float(ZONES[pos_zone_idx].get("stop_loss", 0.0))

                    if direction == "BUY":
                        tp_price = normalize_price(pos.price_open + tp_val)
                        sl_price = (
                            normalize_price(pos.price_open - sl_val)
                            if sl_val > 0
                            else None
                        )
                    else:
                        tp_price = normalize_price(pos.price_open - tp_val)
                        sl_price = (
                            normalize_price(pos.price_open + sl_val)
                            if sl_val > 0
                            else None
                        )

                    send_pending_order(
                        pos.price_open,
                        remaining_lot,
                        tp_price,
                        sl_price,
                        zone_idx=pos_zone_idx,
                        direction=direction,
                    )

    robot_orders = get_all_robot_orders()

    # 3. BÖLGE ÇIKIŞI VE TEMİZLİK (ANLIK FİYAT VE MUM KAPANIŞI MANTIĞI)
    if ACTIVE_ZONE is not None:
        is_exited = False
        exit_cond = ACTIVE_ZONE.get("exit_condition", "Anlık Fiyat")
        z_min = float(ACTIVE_ZONE.get("min_price", 0))
        z_max = float(ACTIVE_ZONE.get("max_price", 0))

        if exit_cond == "Anlık Fiyat":
            if current_avg_price < z_min or current_avg_price > z_max:
                is_exited = True
        else:
            tf_str = ACTIVE_ZONE.get("exit_timeframe", "M15")
            tf = get_mt5_timeframe(tf_str)
            if IS_MAC_TEST_MODE:
                close_price = current_avg_price
            else:
                rates = mt5.copy_rates_from_pos(SYMBOL, tf, 1, 1)
                if rates is not None and len(rates) > 0:
                    close_price = (
                        rates[0]["close"]
                        if isinstance(rates[0], dict)
                        else getattr(
                            rates[0],
                            "close",
                            (
                                rates[0][4]
                                if isinstance(rates[0], tuple)
                                else rates[0]["close"]
                            ),
                        )
                    )
                else:
                    close_price = current_avg_price

            if close_price < z_min or close_price > z_max:
                is_exited = True

        if is_exited:
            if ACTIVE_ZONE.get("clear_on_exit", True):
                scope = ACTIVE_ZONE.get("clear_scope", "Sadece Emirler")
                log_message(
                    f"🧹 Bölge ({z_min}-{z_max}) dışına çıkıldı ({exit_cond}). Temizlik: {scope}"
                )
                target_magic = BASE_MAGIC_NUMBER + ACTIVE_ZONE_IDX + 1

                for order in robot_orders:
                    if order.magic == target_magic:
                        cancel_order(order)

                if scope == "Emirler + Açık Pozisyonlar":
                    for pos in robot_positions:
                        if pos.magic == target_magic:
                            close_position(mt5, pos, SYMBOL, log_message)

                robot_orders = get_all_robot_orders()
                robot_positions = get_all_robot_positions()

            ACTIVE_ZONE = None
            ACTIVE_ZONE_IDX = None

    # YENİ BÖLGEYE GİRİŞ (Güncellenmiş get_active_zone ile tutarlı)
    new_zone, new_zone_idx = get_active_zone(current_avg_price)
    if ACTIVE_ZONE is None and new_zone is not None:
        ACTIVE_ZONE = new_zone
        ACTIVE_ZONE_IDX = new_zone_idx
        log_message(
            f"📍 Yeni Bölgeye Girildi: Bölge {ACTIVE_ZONE_IDX+1} ({ACTIVE_ZONE.get('min_price')}-{ACTIVE_ZONE.get('max_price')})"
        )

    # 4. KAYAN AĞ (SLIDING GRID) ÖRÜLMESİ VE EKSİK TAMAMLAMA

    # 🛑 GÜVENLİK DUVARI 1: Arayüzden bu bölge Başlatılmadıysa (PAUSE/CLEAR) pas geç
    if (
        ACTIVE_ZONE is None
        or active_zones_state.get(ACTIVE_ZONE_IDX, "START") != "START"
    ):
        return True

    # Ayarları Çek
    z_type = ACTIVE_ZONE.get("order_type", "BUY")
    z_min = float(ACTIVE_ZONE.get("min_price", 0))
    z_max = float(ACTIVE_ZONE.get("max_price", 0))
    grid_step = max(0.01, float(ACTIVE_ZONE.get("grid_step", 0.05)))
    lot_val = max(0.01, min(5.0, float(ACTIVE_ZONE.get("lot_size", 0.01))))
    tp_val = float(ACTIVE_ZONE.get("take_profit", 0.05))
    sl_val = float(ACTIVE_ZONE.get("stop_loss", 0.0))

    # Yeni Arayüz Parametreleri
    levels_below = int(ACTIVE_ZONE.get("levels_below", 5))
    levels_above = int(ACTIVE_ZONE.get("levels_above", 5))
    max_positions_allowed = int(ACTIVE_ZONE.get("max_positions", 10))

    # EĞER 0 GİRİLDİYSE GÜVENLİK İÇİN SINIRI 500 OLARAK BELİRLE
    if max_positions_allowed == 0:
        max_positions_allowed = 500

    # 🛑 GÜVENLİK DUVARI 2: Maksimum Açık Pozisyon Sınırı (Hesap Patlama Koruması)
    target_magic = BASE_MAGIC_NUMBER + ACTIVE_ZONE_IDX + 1
    current_open_positions = len(
        [p for p in robot_positions if p.magic == target_magic]
    )

    if current_open_positions >= max_positions_allowed:
        log_message(
            f"⚠️ DİKKAT: Bölge {ACTIVE_ZONE_IDX+1} Maksimum pozisyon sınırına ulaştı ({max_positions_allowed}). Yeni ağ örülmeyecek!",
            "WARN",
        )
        # Bekleyen emir varsa ve pozisyon sınırı dolduysa, tehlikeyi önlemek için onları da sil
        silinen = 0
        for order in robot_orders:
            if order.magic == target_magic:
                cancel_order(order)
                silinen += 1
        if silinen > 0:
            log_message(
                f"🛡️ Güvenlik Koruması: Sınır aşıldığı için {silinen} bekleyen emir temizlendi."
            )
        return True

    # Merkez Fiyatı (Anchor) Bul: Güncel fiyata en yakın "Grid Katı"
    anchor_price = round(current_avg_price / grid_step) * grid_step

    desired_buy_levels = []
    desired_sell_levels = []

    # --- YENİ: TİTREMEYİ (LOOP) ÖNLEYEN TAMPON BÖLGE ---
    acceptable_buy_levels = []
    acceptable_sell_levels = []
    buffer_steps = 2  # Silme işlemi için 2 kademe fazladan esneklik (Hysteresis)
    # --------------------------------------------------

    # KAYAN PENCEREYİ OLUŞTUR (Sliding Window)
    if z_type in ["BUY", "BOTH"]:
        # Merkezin Kendisi
        if z_min <= anchor_price <= z_max:
            desired_buy_levels.append(normalize_price(anchor_price))

        # Alttaki emirler (Limit)
        for i in range(1, levels_below + 1):
            p = anchor_price - (i * grid_step)
            if z_min <= p <= z_max:
                desired_buy_levels.append(normalize_price(p))
        # Üstteki emirler (Stop)
        for i in range(1, levels_above + 1):
            p = anchor_price + (i * grid_step)
            if z_min <= p <= z_max:
                desired_buy_levels.append(normalize_price(p))

        # Toleranslı Kabul Bölgesi (Silinmeyecek Emirler)
        for i in range(-levels_below - buffer_steps, levels_above + buffer_steps + 1):
            acceptable_buy_levels.append(
                normalize_price(anchor_price + (i * grid_step))
            )

    if z_type in ["SELL", "BOTH"]:
        # Merkezin Kendisi
        if z_min <= anchor_price <= z_max:
            desired_sell_levels.append(normalize_price(anchor_price))

        # Üstteki emirler (Limit)
        for i in range(1, levels_above + 1):
            p = anchor_price + (i * grid_step)
            if z_min <= p <= z_max:
                desired_sell_levels.append(normalize_price(p))
        # Alttaki emirler (Stop)
        for i in range(1, levels_below + 1):
            p = anchor_price - (i * grid_step)
            if z_min <= p <= z_max:
                desired_sell_levels.append(normalize_price(p))

        # Toleranslı Kabul Bölgesi (Silinmeyecek Emirler)
        for i in range(-levels_below - buffer_steps, levels_above + buffer_steps + 1):
            acceptable_sell_levels.append(
                normalize_price(anchor_price + (i * grid_step))
            )

    # Broker kaymalarını tolere etmek için esnek tolerans (Grid'in %40'ı kadar esneklik)
    tolerance = grid_step * 0.4

    # UZAKLAŞAN/GEREKSİZ EMİRLERİ SİL (Pencere Kayması) - YENİ TAMPON BÖLGE İLE
    silinen_emir_sayisi = 0
    for order in robot_orders:
        if order.magic != target_magic:
            continue

        order_price = normalize_price(order.price_open)
        is_valid = False

        if order.type in [mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_BUY_STOP]:
            is_valid = any(
                abs(order_price - al) <= tolerance for al in acceptable_buy_levels
            )
        elif order.type in [mt5.ORDER_TYPE_SELL_LIMIT, mt5.ORDER_TYPE_SELL_STOP]:
            is_valid = any(
                abs(order_price - al) <= tolerance for al in acceptable_sell_levels
            )

        if not is_valid:
            cancel_order(order)
            silinen_emir_sayisi += 1

    if silinen_emir_sayisi > 0:
        log_message(
            f"🧹 Pencere Kaydı: Fiyattan uzaklaşan {silinen_emir_sayisi} adet emir silindi."
        )

    # EKSİK EMİRLERİ TAMAMLA (TP Olanların Yerini Doldurur)
    exist_buy_levels, exist_sell_levels = get_existing_levels_by_direction(grid_step)
    eklenen_emir_sayisi = 0

    # BUY Eksikleri
    for level_price in desired_buy_levels:
        is_occupied = any(abs(level_price - el) <= tolerance for el in exist_buy_levels)
        if not is_occupied:
            tp_price = normalize_price(level_price + tp_val)
            sl_price = normalize_price(level_price - sl_val) if sl_val > 0 else None
            if send_pending_order(
                level_price,
                lot_val,
                tp_price,
                sl_price,
                zone_idx=ACTIVE_ZONE_IDX,
                direction="BUY",
            ):
                eklenen_emir_sayisi += 1

    # SELL Eksikleri
    for level_price in desired_sell_levels:
        is_occupied = any(
            abs(level_price - el) <= tolerance for el in exist_sell_levels
        )
        if not is_occupied:
            tp_price = normalize_price(level_price - tp_val)
            sl_price = normalize_price(level_price + sl_val) if sl_val > 0 else None
            if send_pending_order(
                level_price,
                lot_val,
                tp_price,
                sl_price,
                zone_idx=ACTIVE_ZONE_IDX,
                direction="SELL",
            ):
                eklenen_emir_sayisi += 1

    if eklenen_emir_sayisi > 0:
        log_message(
            f"🌱 Ağ Tazelendi: TP olan/eksik {eklenen_emir_sayisi} adet emir yerleştirildi."
        )

    return True

# ═══════════════════════════════════════════════════════════════════════════════
# BAŞLANGIÇ KONTROLLERİ VE ANA DÖNGÜ
# ═══════════════════════════════════════════════════════════════════════════════


def run_startup_checks():
    global SYMBOL_INFO, FILLING_MODE, active_zones_state
    log_message("=" * 60)
    log_message("USOUSD Çift Yönlü Grid Robot v3.0 (MODEL 2) Baslatiliyor...")
    log_message("=" * 60)

    SYMBOL_INFO = mt5.symbol_info(SYMBOL)
    if SYMBOL_INFO is None or not SYMBOL_INFO.visible:
        log_message(f"Sembol bulunamadi veya seçilemedi: {SYMBOL}", "ERROR")
        mt5.shutdown()
        return False

    if determine_fill_mode() is None:
        mt5.shutdown()
        return False

    if not is_market_open():
        log_message("Piyasa su anda kapali. Acilmasi bekleniyor...", "WARN")
    else:
        tick = mt5.symbol_info_tick(SYMBOL)
        if tick:
            log_message(f"Piyasa acik. Bid: {tick.bid}, Ask: {tick.ask}")

    active_zones_state = {}
    robot_positions = get_all_robot_positions()
    robot_orders = get_all_robot_orders()

    if robot_positions is None or robot_orders is None:
        log_message(
            "Kritik Hata: MT5'ten veri alınamadı. Bağlantı stabil değil.", "ERROR"
        )
        mt5.shutdown()
        return False

    for item in robot_positions + robot_orders:
        active_zones_state[item.magic - BASE_MAGIC_NUMBER - 1] = "START"

    if active_zones_state:
        log_message(
            f"🧠 Hafıza Kurtarıldı: Aktif bölgeler: {list(active_zones_state.keys())}"
        )

    log_message("Tum baslangic kontrolleri basarili!")
    return True


def main_loop():
    global IS_RUNNING, INITIAL_CLEANUP_DONE

    if not run_startup_checks():
        log_message("Baslangic kontrolleri basarisiz. Robot durduruluyor.", "ERROR")
        return

    log_message("Robot calismaya basladi. (Durdurmak icin Ctrl+C)")

    try:
        while IS_RUNNING:
            load_dynamic_settings()

            term_info = mt5.terminal_info()
            if term_info is None or not term_info.trade_allowed:
                time.sleep(10)
                continue

            if not is_market_open():
                time.sleep(MARKET_CLOSED_CHECK_INTERVAL)
                continue

            if not INITIAL_CLEANUP_DONE:
                eski_emirler = get_all_robot_orders()
                if eski_emirler:
                    log_message(
                        "🚀 Başlangıç Temizliği: Eski ayarlardan kalan tüm bekleyen emirler siliniyor..."
                    )
                    for emir in eski_emirler:
                        cancel_order(emir)
                    log_message(
                        "✅ Temizlik bitti. Ağ, yeni ayarlarınızla güncel merkeze göre sıfırdan örülecek."
                    )
                INITIAL_CLEANUP_DONE = True

            try:
                manage_dynamic_grid()
            except Exception as e:
                log_message(
                    f"🚨 Hata (Crash Koruması): manage_dynamic_grid'de hata: {e}",
                    "ERROR",
                )

            time.sleep(LOOP_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        log_message("Kullanici tarafindan durduruldu.", "WARN")
    finally:
        log_message(
            "🛑 Robot durduruldu. Sadece bekleyen nöbetçi emirler temizleniyor. AÇIK POZİSYONLAR BIRAKILDI."
        )
        eski_emirler = get_all_robot_orders()
        if eski_emirler:
            for emir in eski_emirler:
                cancel_order(emir)
        mt5.shutdown()


if __name__ == "__main__":
    main_loop()
