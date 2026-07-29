"""
================================================================================
🛠️ USOUSD Yarı-Otomatik Dinamik Grid Robotu v2.2 (MODEL 2)
MetaTrader 5 Python API ile çalışan algoritmik ticaret robotu
================================================================================
Açıklama: 
- 5 ALTIN KURAL UYGULANMIŞTIR.
- Açık işlemlere KESİNLİKLE müdahale edemez, kapatamaz.
- Çoklu-Bölge (Multi-Zone) ve Otonom yapıya sahiptir.
- Ayarlar sadece ait olduğu bölgeye özeldir.
================================================================================
"""

import time
import datetime
import sys
import os
import platform
import json
import threading
from src.utils.trade_utils import safe_send_order, get_algo_status

# Temel Değişkenleri Başlangıç İçin Tanımlayalım
LOOP_INTERVAL_SECONDS = 1.0
ZONES = []
ORDER_TYPE = "BUY"
SYMBOL = "USOUSD"


def load_dynamic_settings():
    """Güncel ayarları MT5 hesap ID'sine göre dinamik olarak okur"""
    global LOOP_INTERVAL_SECONDS, ZONES, ORDER_TYPE, SYMBOL

    # 1. MT5'ten aktif hesabın Login ID'sini alıyoruz
    login_id = "default"
    try:
        if platform.system() == "Windows":
            acc_info = mt5.account_info()
            if acc_info is not None:
                login_id = str(acc_info.login)
    except Exception:
        pass

    # 2. Multi-Account sistemine uygun dosya adını oluşturuyoruz
    file_path = os.path.join("configs", f"settings_{login_id}_Model_2.json")

    # 3. Eğer dosya yoksa, eski isme (fallback) bak
    if not os.path.exists(file_path):
        file_path = os.path.join("configs", "settings_model2.json")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
            LOOP_INTERVAL_SECONDS = settings.get("LOOP_INTERVAL_SECONDS", 1.0)
            ZONES = settings.get("ZONES", [])
            ORDER_TYPE = settings.get("ORDER_TYPE", "BUY")
            SYMBOL = settings.get("SYMBOL", "USOUSD")
    except Exception as e:
        pass


# ===============================================================================
# 🍏🪟 MAC / WINDOWS UYUMLULUK KÖPRÜSÜ
# ===============================================================================
if platform.system() == "Windows":
    import MetaTrader5 as mt5
    IS_MAC_TEST_MODE = False

    def set_mock_price(new_price): 
        pass 
else:
    IS_MAC_TEST_MODE = True
    print("⚠️ UYARI: Mac işletim sistemi algılandı. MT5 Sahte (Mock) modda çalışıyor!")
    
    MOCK_CURRENT_PRICE = 75.00
    
    def set_mock_price(new_price):
        global MOCK_CURRENT_PRICE
        MOCK_CURRENT_PRICE = new_price
        
    class DummyMT5:
        def __init__(self):
            self.dummy_orders = [] 
            self.ticket_counter = 1

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

        def initialize(self): return True
        def shutdown(self): pass
        def last_error(self): return (1, "Mock Error")

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

        def symbol_select(self, symbol, visible): return True

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
                    def __init__(self, ticket, magic, price):
                        self.ticket = ticket
                        self.magic = magic
                        self.price_open = price
                
                new_order = DummyOrder(
                    self.ticket_counter, 
                    request.get("magic"), 
                    request.get("price")
                )
                self.dummy_orders.append(new_order)
                self.ticket_counter += 1
                
            elif request.get("action") == self.TRADE_ACTION_REMOVE:
                ticket_to_remove = request.get("order")
                self.dummy_orders = [o for o in self.dummy_orders if o.ticket != ticket_to_remove]
                
            return SendResult()

if IS_MAC_TEST_MODE:
    mt5 = DummyMT5()

# ═══════════════════════════════════════════════════════════════════════════════
# KULLANICI AYARLARI
# ═══════════════════════════════════════════════════════════════════════════════

MAGIC_NUMBER  = 123456            
MAX_DEVIATION = 20      
MARKET_CLOSED_CHECK_INTERVAL = 60    
LOG_TO_FILE = True                   
LOG_FILE_PATH = "logs/grid_robot_log.txt"

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL DEĞİŞKENLER
# ═══════════════════════════════════════════════════════════════════════════════

REFERENCE_PRICE = None      
SYMBOL_INFO = None          
FILLING_MODE = None         
IS_RUNNING = True
INITIAL_CLEANUP_DONE = False 
ACTIVE_ZONE = None
SIMULATED_PRICE = None

# ═══════════════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════════════════════

def log_message(msg, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [{level}] {msg}"
    print(formatted)
    if LOG_TO_FILE:
        try:
            with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")
        except Exception:
            pass

def normalize_price(price):
    if SYMBOL_INFO is None:
        return round(price, 2)
    point = SYMBOL_INFO.point
    if point == 0:
        return price
    digits = SYMBOL_INFO.digits
    return round(round(price / point) * point, digits)

def normalize_volume(volume):
    if SYMBOL_INFO is None:
        return volume
    min_vol = SYMBOL_INFO.volume_min
    max_vol = SYMBOL_INFO.volume_max
    vol_step = SYMBOL_INFO.volume_step

    volume = max(min_vol, min(volume, max_vol))
    if vol_step > 0:
        steps = round((volume - min_vol) / vol_step)
        volume = min_vol + steps * vol_step
        volume = max(min_vol, min(volume, max_vol))

    return round(volume, 8)

def get_current_market_price():
    global SIMULATED_PRICE
    if SIMULATED_PRICE is not None:
        return SIMULATED_PRICE
        
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        return None
    if ORDER_TYPE.upper() == "BUY":
        return tick.ask
    else:
        return tick.bid

def is_market_open():
    info = mt5.symbol_info(SYMBOL)
    if info is None:
        return False
    return info.trade_mode == 4

def determine_fill_mode():
    global FILLING_MODE
    if SYMBOL_INFO is None:
        return None
    filling_mode = SYMBOL_INFO.filling_mode
    if filling_mode & 2:
        FILLING_MODE = mt5.ORDER_FILLING_IOC
        log_message("Fill politikası: ORDER_FILLING_IOC")
    elif filling_mode & 1:
        FILLING_MODE = mt5.ORDER_FILLING_FOK
        log_message("Fill politikası: ORDER_FILLING_FOK")
    else:
        FILLING_MODE = mt5.ORDER_FILLING_RETURN
        log_message("Fill politikası: ORDER_FILLING_RETURN")
    return FILLING_MODE

def get_pending_order_type(target_price, current_price):
    if ORDER_TYPE.upper() == "BUY":
        return mt5.ORDER_TYPE_BUY_LIMIT if target_price < current_price else mt5.ORDER_TYPE_BUY_STOP
    else:
        return mt5.ORDER_TYPE_SELL_LIMIT if target_price > current_price else mt5.ORDER_TYPE_SELL_STOP

def get_all_robot_orders():
    orders = mt5.orders_get(symbol=SYMBOL)
    if orders is None: return None  
    return [o for o in orders if o.magic == MAGIC_NUMBER]

def get_all_robot_positions():
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions is None: return None
    target_type = mt5.POSITION_TYPE_BUY if ORDER_TYPE.upper() == "BUY" else mt5.POSITION_TYPE_SELL
    return [p for p in positions if p.magic == MAGIC_NUMBER and p.type == target_type]

def get_all_manual_positions():
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions is None: return None
    target_type = mt5.POSITION_TYPE_BUY if ORDER_TYPE.upper() == "BUY" else mt5.POSITION_TYPE_SELL
    return [p for p in positions if p.magic != MAGIC_NUMBER and p.type == target_type]

# DÜZELTME: Kayma (Slippage) yuvarlaması (Dinamik Zone grid_step'i ile)
def get_existing_levels(grid_step):
    levels = set()
    orders = get_all_robot_orders()
    r_pos = get_all_robot_positions()
    m_pos = get_all_manual_positions()

    if orders:
        for order in orders: levels.add(normalize_price(order.price_open))
    if r_pos:
        for pos in r_pos: 
            snapped_price = round(pos.price_open / grid_step) * grid_step
            levels.add(normalize_price(snapped_price))
    if m_pos:
        for pos in m_pos: 
            snapped_price = round(pos.price_open / grid_step) * grid_step
            levels.add(normalize_price(snapped_price))
    return levels


def cancel_order(order):
    request = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": order.ticket,
        "symbol": SYMBOL,
    }
    # Emir iptali de güvenli merkeze emanet
    return safe_send_order(mt5, request, log_message)


# DÜZELTME: Ping-Pong Mıknatısı (Dinamik grid_step entegreli)
def calculate_reference_price(grid_step):
    global REFERENCE_PRICE
    current_price = get_current_market_price()
    if current_price is None: return None
    
    if REFERENCE_PRICE is None:
        snapped_price = round(current_price / grid_step) * grid_step
        return normalize_price(snapped_price)
        
    distance = abs(current_price - REFERENCE_PRICE)
    
    if distance >= grid_step:
        snapped_price = round(current_price / grid_step) * grid_step
        return normalize_price(snapped_price)
        
    return REFERENCE_PRICE

def get_active_zone(price):
    for zone in ZONES:
        if float(zone.get("min_price", 0)) <= price <= float(zone.get("max_price", 0)):
            return zone
    return None

def calculate_grid_levels(reference_price, zone_info):
    levels = []
    if zone_info is None or reference_price is None:
        return levels

    grid_step = float(zone_info["grid_step"])
    z_min = float(zone_info["min_price"])
    z_max = float(zone_info["max_price"])

    p = reference_price + grid_step
    while p <= z_max:
        levels.append(normalize_price(p))
        p += grid_step

    p = reference_price - grid_step
    while p >= z_min:
        levels.append(normalize_price(p))
        p -= grid_step

    return sorted(set(levels))


def send_pending_order(price, lot, tp_price, sl_price=None):
    current_price = get_current_market_price()
    if current_price is None:
        return False
    order_type = get_pending_order_type(price, current_price)

    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": SYMBOL,
        "volume": normalize_volume(lot),
        "type": order_type,
        "price": price,
        "deviation": MAX_DEVIATION,
        "magic": MAGIC_NUMBER,
        "comment": f"GridBot_{ORDER_TYPE}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": (
            FILLING_MODE if FILLING_MODE is not None else mt5.ORDER_FILLING_IOC
        ),
        "tp": tp_price,
    }
    # Model 1'de STOP_LOSS globaldir, Model 2'de fonksiyona gelir.
    # Güvenli atama:
    if sl_price is not None and sl_price > 0:
        request["sl"] = sl_price

    # Loglama yeteneğiyle birlikte gönderiyoruz!
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

    # TP/SL değişikliği de güvenli merkeze emanet
    return safe_send_order(mt5, request, log_message)


# ═══════════════════════════════════════════════════════════════════════════════
# ANA DİNAMİK YÖNETİM MOTORU (MODEL 2)
# ═══════════════════════════════════════════════════════════════════════════════

def manage_dynamic_grid():
    global REFERENCE_PRICE, ACTIVE_ZONE

    robot_positions = get_all_robot_positions()
    manual_positions = get_all_manual_positions()
    robot_orders = get_all_robot_orders()
    
    if robot_positions is None or manual_positions is None or robot_orders is None:
        return False 
        
    current_price = get_current_market_price()
    if current_price is None: return False

    current_zone = get_active_zone(current_price)

    # BÖLGE DEĞİŞİMİ / ÇIKIŞI
    if current_zone != ACTIVE_ZONE:
        if ACTIVE_ZONE is not None:
            zone_clear_flag = ACTIVE_ZONE.get("clear_on_exit", True)
            if zone_clear_flag:
                log_message(f"🧹 Bölge ({ACTIVE_ZONE.get('min_price')}-{ACTIVE_ZONE.get('max_price')}) dışına çıkıldı. Temizlik AÇIK: Eski emirler siliniyor...")
                for order in robot_orders:
                    cancel_order(order)
                robot_orders = get_all_robot_orders()
            else:
                log_message(f"🪤 Bölge ({ACTIVE_ZONE.get('min_price')}-{ACTIVE_ZONE.get('max_price')}) dışına çıkıldı. Temizlik KAPALI: Mevcut bekleyen emirler tuzak olarak bırakıldı.")
                
        ACTIVE_ZONE = current_zone
        # DÜZELTME 1: Yeni bölgeye geçince eski merkez hafızasını sıfırla! (Matematiksel Uyum)
        REFERENCE_PRICE = None

    # BÖLGE KONTROLÜ
    if ACTIVE_ZONE is not None:
        grid_step = float(ACTIVE_ZONE.get("grid_step", 0.05))
        tp_val = float(ACTIVE_ZONE.get("take_profit", 0.05))
        lot_val = float(ACTIVE_ZONE.get("lot_size", 0.01))
        sl_val = float(ACTIVE_ZONE.get("stop_loss", 0.0))
        
        yeni_referans = calculate_reference_price(grid_step)
        if REFERENCE_PRICE != yeni_referans:
            REFERENCE_PRICE = yeni_referans
            log_message(f"📍 BÖLGE İÇİ OTONOM AĞ: Yeni Merkez -> {REFERENCE_PRICE}")
    else:
        REFERENCE_PRICE = None
        return True 

    desired_levels = calculate_grid_levels(REFERENCE_PRICE, ACTIVE_ZONE)
    tolerance = (SYMBOL_INFO.point * 2) if SYMBOL_INFO else 0.02
    
    # UZAKTA KALAN BEKLEYEN EMİRLERİ SİL
    z_min = float(ACTIVE_ZONE.get("min_price", 0))
    z_max = float(ACTIVE_ZONE.get("max_price", 0))

    for order in robot_orders:
        order_price = normalize_price(order.price_open)
        
        # DÜZELTME 2: (Model 2 Özelliği) Eğer emir şu anki aktif bölgenin dışındaysa,
        # ve clear_on_exit = False sayesinde hayatta kalmışsa, ONA DOKUNMA (Tuzak Koruma)
        if not (z_min <= order_price <= z_max):
            continue

        is_valid = False
        for dl in desired_levels:
            if abs(order_price - dl) <= tolerance:
                is_valid = True
                break
                
        if not is_valid:
            cancel_order(order)

    # EKSİK OLAN SEVİYELERİ DOLDUR
    mevcut_seviyeler = get_existing_levels(grid_step) 
    for level_price in desired_levels:
        is_occupied = False
        for exist_lvl in mevcut_seviyeler:
            if abs(level_price - exist_lvl) <= tolerance:
                is_occupied = True
                break
                 
        if not is_occupied:
            if ORDER_TYPE.upper() == "BUY":
                tp_price = normalize_price(level_price + tp_val)
                sl_price = normalize_price(level_price - sl_val) if sl_val > 0 else None
            else:
                tp_price = normalize_price(level_price - tp_val)
                sl_price = normalize_price(level_price + sl_val) if sl_val > 0 else None
                
            send_pending_order(level_price, lot_val, tp_price, sl_price)

    return True

# ═══════════════════════════════════════════════════════════════════════════════
# BAŞLANGIÇ KONTROLLERİ VE ANA DÖNGÜ
# ═══════════════════════════════════════════════════════════════════════════════

def run_startup_checks():
    global SYMBOL_INFO, FILLING_MODE
    log_message("=" * 60)
    log_message("USOUSD Dinamik Grid Robot v2.2 (MODEL 2) Baslatiliyor...")
    log_message("=" * 60)

    log_message("MT5 baglantisi kuruluyor...")
    if not mt5.initialize():
        log_message(f"MT5 baglantisi kurulamadi: {mt5.last_error()}", "ERROR")
        return False
    log_message("MT5 baglantisi kuruldu.")

    SYMBOL_INFO = mt5.symbol_info(SYMBOL)
    if SYMBOL_INFO is None:
        log_message(f"Sembol bulunamadi: {SYMBOL}", "ERROR")
        mt5.shutdown()
        return False

    if not SYMBOL_INFO.visible:
        if not mt5.symbol_select(SYMBOL, True):
            log_message(f"Sembol secilemedi: {SYMBOL}", "ERROR")
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

    log_message("Tum baslangic kontrolleri basarili!")
    return True

# Geri Eklenen Kritik Fonksiyon (Web Dashboard için gereklidir)
def get_live_metrics():
    current_price = get_current_market_price()
    robot_positions = get_all_robot_positions()
    robot_orders = get_all_robot_orders()
    
    profit = 0.0
    open_positions = 0
    pending_orders = 0
    
    if robot_positions:
        open_positions = len(robot_positions)
        profit = sum(pos.profit for pos in robot_positions)
        
    if robot_orders:
        pending_orders = len(robot_orders)
        
    return {
        "profit": profit,
        "open_positions": open_positions,
        "pending_orders": pending_orders,
        "current_price": current_price if current_price else 0.0,
        "algo_trading_error": get_algo_status() # Merkezi bileşenden okuyoruz!
    }

def main_loop():
    global IS_RUNNING, INITIAL_CLEANUP_DONE

    if not run_startup_checks():
        log_message("Baslangic kontrolleri basarisiz. Robot durduruluyor.", "ERROR")
        return

    log_message("Robot calismaya basladi. (Durdurmak icin Ctrl+C)")

    try:
        while IS_RUNNING:
            load_dynamic_settings() 
            if not is_market_open():
                time.sleep(MARKET_CLOSED_CHECK_INTERVAL)
                continue

            if not INITIAL_CLEANUP_DONE:
                eski_emirler = get_all_robot_orders()
                if eski_emirler:
                    log_message("🚀 Başlangıç Temizliği: Eski ayarlardan kalan tüm bekleyen emirler siliniyor...")
                    for emir in eski_emirler:
                        cancel_order(emir)
                    log_message("✅ Temizlik bitti. Ağ, yeni ayarlarınızla güncel merkeze göre sıfırdan örülecek.")
                INITIAL_CLEANUP_DONE = True

            manage_dynamic_grid()
            
            time.sleep(LOOP_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        log_message("Kullanici tarafindan durduruldu.", "WARN")
    finally:
        log_message("🛑 Robot durduruldu. Sadece bekleyen nöbetçi emirler temizleniyor. AÇIK POZİSYONLAR BIRAKILDI.")
        eski_emirler = get_all_robot_orders()
        if eski_emirler:
            for emir in eski_emirler:
                cancel_order(emir)
        log_message("MT5 baglantisi kapatiliyor...")
        mt5.shutdown()
        log_message("Robot sonlandirildi.")

if __name__ == "__main__":
    main_loop()
