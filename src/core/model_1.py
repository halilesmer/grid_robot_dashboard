import time
import datetime
import platform
import json
from src.utils.trade_utils import safe_send_order
import time
from src.utils.config import get_settings_file

# ==========================================
# GLOBALE STEUERUNGSVARIABLEN (Zwingend für den Bot-Manager)
# ==========================================
# Global Değişkenleri Başlangıç İçin Tanımlayalım
GRID_STEP = 0.05
TAKE_PROFIT = 0.05
LEVELS_BELOW = 6
LEVELS_ABOVE = 6
DEFAULT_LOT = 0.01
MAX_OPEN_POSITIONS = 999
MAX_PRICE_LIMIT = 120.00
MIN_PRICE_LIMIT = 20.00
IS_RUNNING = False
INITIAL_CLEANUP_DONE = False
SIMULATED_PRICE = 0.0  # Für den Mac-Testmodus


def load_dynamic_settings():
    """Her döngüde arka plan sürecine ait doğru settings.json dosyasını okur"""
    # Not: Buradaki global değişkenler senin model_2'deki değişkenlerinle aynı olmalı (ZONES vb.)
    global TAKE_PROFIT, MAX_OPEN_POSITIONS, ZONES, LOOP_INTERVAL_SECONDS
    try:
        # DÜZELTME: Model 2 için hesaba özel JSON dosyasını buluyor!
        settings_file = get_settings_file("Model 2")
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)
            TAKE_PROFIT = settings.get("TAKE_PROFIT", 0.05)
            MAX_OPEN_POSITIONS = settings.get("MAX_OPEN_POSITIONS", 999)
            ZONES = settings.get("ZONES", [])
            LOOP_INTERVAL_SECONDS = settings.get("LOOP_INTERVAL_SECONDS", 1.0)
    except Exception as e:
        pass


# ===============================================================================
# 🍏🪟 MAC / WINDOWS UYUMLULUK KÖPRÜSÜ
# ===============================================================================
if platform.system() == "Windows":
    import MetaTrader5 as mt5
    IS_MAC_TEST_MODE = False
else:
    IS_MAC_TEST_MODE = True
    print("⚠️ UYARI: Mac işletim sistemi algılandı. MT5 Sahte (Mock) modda çalışıyor!")

# ===============================================================================
# 🍏🪟 MAC / WINDOWS UYUMLULUK KÖPRÜSÜ VE FİYAT SİMÜLATÖRÜ
# ===============================================================================
if platform.system() == "Windows":
    import MetaTrader5 as mt5
    IS_MAC_TEST_MODE = False
    
    # Windows'ta hata vermemesi için boş bir fonksiyon
    def set_mock_price(new_price): 
        pass 
else:
    IS_MAC_TEST_MODE = True
    print("⚠️ UYARI: Mac işletim sistemi algılandı. MT5 Sahte (Mock) modda çalışıyor!")
    
    # Sahte motorun varsayılan fiyatı
    MOCK_CURRENT_PRICE = 75.00
    
    # Arayüzden (slider) gelen yeni fiyatı motora ileten fonksiyon
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

        # Fiyat artık sabit değil, simülatörden (MOCK_CURRENT_PRICE) geliyor!
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

BROKER_SERVER = "Eightcap-Demo"   
SYMBOL        = "USOUSD"          
ORDER_TYPE    = "BUY"             
MAGIC_NUMBER  = 123456            

STOP_LOSS    = 0      
MAX_DEVIATION   =  20      

DOWN_THRESHOLDS = [
    (60.00, 0.02),   
]

UP_THRESHOLDS = [
    (90.00,  0.01),  
]

LOOP_INTERVAL_SECONDS = 1            
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

# ═══════════════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════════════════════


def log_message(msg, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [{level}] {msg}"
    # DÜZELTME: Sadece print yapıyoruz. bot_manager.py bunu otomatik yakalayıp log dosyasına yazar!
    print(formatted)


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

def get_lot_for_price(price):
    for threshold_price, threshold_lot in reversed(UP_THRESHOLDS):
        if price >= threshold_price:
            return normalize_volume(threshold_lot)
    for threshold_price, threshold_lot in reversed(DOWN_THRESHOLDS):
        if price < threshold_price:
            return normalize_volume(threshold_lot)
    return normalize_volume(DEFAULT_LOT)

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

def get_existing_levels():
    levels = set()
    orders = get_all_robot_orders()
    r_pos = get_all_robot_positions()
    m_pos = get_all_manual_positions()

    # 1. Bekleyen emirlerin fiyatı nettir (kayma yoktur), doğrudan ekle.
    if orders:
        for order in orders: 
            levels.add(normalize_price(order.price_open))

    # 2. CANLI İŞLEMLERDE SPREAD/SLIPPAGE (KAYMA) OLUR!
    # İşlem 85.007'de açılmış olsa bile robot onu 85.000 çizgisi olarak algılamalı.
    # Bu yüzden fiyatı en yakın Grid (Ağ) aralığına yuvarlayarak listeye ekliyoruz.
    if r_pos:
        for pos in r_pos: 
            snapped_price = round(pos.price_open / GRID_STEP) * GRID_STEP
            levels.add(normalize_price(snapped_price))

    if m_pos:
        for pos in m_pos: 
            snapped_price = round(pos.price_open / GRID_STEP) * GRID_STEP
            levels.add(normalize_price(snapped_price))

    return levels

# KURAL 4 UYARINCA `close_position` FONKSİYONU KODDAN TAMAMEN SİLİNMİŞTİR.
# Yalnızca bekleyen emirleri silecek olan fonksiyon (cancel_order) bırakılmıştır.


def cancel_order(order):
    request = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": order.ticket,
        "symbol": SYMBOL,
    }
    # Emir iptali de güvenli merkeze emanet
    return safe_send_order(mt5, request, log_message)


def calculate_reference_price():
    current_price = get_current_market_price()
    if current_price is None: return None
    
    # 1. Eğer robot yeni başlıyorsa ve merkez yoksa doğrudan hesapla
    if REFERENCE_PRICE is None:
        snapped_price = round(current_price / GRID_STEP) * GRID_STEP
        return normalize_price(snapped_price)
        
    # 2. PİNG-PONG (TİTREME) KORUMASI:
    # Fiyat, mevcut merkezden en az "1 Grid Adımı" kadar uzaklaşmadan 
    # ağın merkezini kesinlikle değiştirme ve emirleri silme!
    distance = abs(current_price - REFERENCE_PRICE)
    
    if distance >= GRID_STEP:
        snapped_price = round(current_price / GRID_STEP) * GRID_STEP
        return normalize_price(snapped_price)
        
    # Fiyat yeterince uzaklaşmadıysa (sadece milimetrik dalgalanıyorsa) eski merkezi koru.
    return REFERENCE_PRICE

def calculate_grid_levels(reference_price):
    levels = []
    for i in range(1, LEVELS_BELOW + 1):
        levels.append(normalize_price(reference_price - (i * GRID_STEP)))
    for i in range(1, LEVELS_ABOVE + 1):
        levels.append(normalize_price(reference_price + (i * GRID_STEP)))
    return sorted(set(levels))


def send_pending_order(price, lot, tp_price, sl_price=None):
    current_price = get_current_market_price()
    if current_price is None:
        return False
    order_type = get_pending_order_type(price, current_price)

    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": SYMBOL,
        "volume": lot,
        "type": order_type,
        "price": price,
        "deviation": MAX_DEVIATION,
        "magic": MAGIC_NUMBER,
        "comment": f"GridBot_{ORDER_TYPE}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": FILLING_MODE,
        "tp": tp_price,
    }
    if sl_price is not None and STOP_LOSS > 0:
        request["sl"] = sl_price

    # Eski kalabalık kodlar tamamen silindi.
    # Artık sadece merkezi trade_utils bileşenimize yolluyoruz:
    return safe_send_order(mt5, request)


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
# ANA DİNAMİK YÖNETİM MOTORU
# ═══════════════════════════════════════════════════════════════════════════════

def manage_dynamic_grid():
    global REFERENCE_PRICE

    robot_positions = get_all_robot_positions()
    manual_positions = get_all_manual_positions()
    robot_orders = get_all_robot_orders()
    
    if robot_positions is None or manual_positions is None or robot_orders is None:
        return False 
        
    total_positions = len(robot_positions) + len(manual_positions)

    # 1. KURAL: BEKLEME (STANDBY) KİLİDİ 
    if REFERENCE_PRICE is None:
        if not manual_positions and not robot_positions:
            return True 
            
        yeni_referans = calculate_reference_price()
        if yeni_referans is None: return False
        REFERENCE_PRICE = yeni_referans
        log_message(f"🎯 Hedef Kilitlendi: İlk islem saptandi. Ağ Güncel Fiyata Kuruluyor -> {REFERENCE_PRICE}")

    # 2. VE 5. KURAL: KESİNTİSİZ KÖR TAKİP (Kayan Ağ)
    yeni_referans = calculate_reference_price()
    if yeni_referans is not None and REFERENCE_PRICE != yeni_referans:
        log_message(f"🌊 DİNAMİK AĞ: Fiyat Hareket Etti, Yeni Merkez -> {yeni_referans}")
        REFERENCE_PRICE = yeni_referans

    # 3. KURAL: MANUEL İŞLEME TP EKLENMESİ
    if manual_positions and not robot_positions:
        pos = manual_positions[0]
        if pos.tp == 0.0:
            tp_price = normalize_price(pos.price_open + TAKE_PROFIT) if ORDER_TYPE.upper() == "BUY" else normalize_price(pos.price_open - TAKE_PROFIT)
            if modify_position_tp_sl(pos, tp_price):
                log_message(f"✅ Manuel {ORDER_TYPE} islemine Kar Al (TP) eklendi: {tp_price}")

    # GÜVENLİK KALKANI
    if total_positions >= MAX_OPEN_POSITIONS:
        if robot_orders:
            log_message(f"🚨 KALKAN AKTİF: Maksimum açık pozisyon limitine ({MAX_OPEN_POSITIONS}) ulaşıldı!")
            silinen_kalkan = 0
            for order in robot_orders:
                if cancel_order(order): 
                    silinen_kalkan += 1
            if silinen_kalkan > 0:
                log_message(f"✅ Marjin koruması için {silinen_kalkan} adet bekleyen emir silindi.")
        return True

    desired_levels = calculate_grid_levels(REFERENCE_PRICE)

    # -----------------------------------------------------------------------
    # HATA BURADAYDI: Toleransı eski keskin (0.02) formata geri çevirdik!
    tolerance = (SYMBOL_INFO.point * 2) if SYMBOL_INFO else 0.02
    # -----------------------------------------------------------------------
    
    # 6. UZAKTA KALAN (SINIR DIŞI) BEKLEYEN EMİRLERİ SİL
    silinen_emir_sayisi = 0
    
    for order in robot_orders:
        order_price = normalize_price(order.price_open)
        is_valid = False
        for dl in desired_levels:
            if abs(order_price - dl) <= tolerance:
                is_valid = True
                break
                
        if not is_valid:
            if cancel_order(order): 
                silinen_emir_sayisi += 1
                
    if silinen_emir_sayisi > 0:
        log_message(f"🧹 Ağ kaydı: Uzakta kalan/Gereksiz {silinen_emir_sayisi} adet bekleyen emir silindi.")

    # 7. EKSİK OLAN YENİ UFUK KADEMELERİNİ DOLDUR (EMİR DİZME)
    doldurulan = 0
    mevcut_seviyeler = get_existing_levels() 
    
    for level_price in desired_levels:
        if level_price > MAX_PRICE_LIMIT or level_price < MIN_PRICE_LIMIT:
            continue
            
        is_occupied = False
        for exist_lvl in mevcut_seviyeler:
            if abs(level_price - exist_lvl) <= tolerance:
                is_occupied = True
                break
                 
        if not is_occupied:
            lot = get_lot_for_price(level_price)
            if ORDER_TYPE.upper() == "BUY":
                tp_price = normalize_price(level_price + TAKE_PROFIT)
                sl_price = normalize_price(level_price - STOP_LOSS) if STOP_LOSS > 0 else None
            else:
                tp_price = normalize_price(level_price - TAKE_PROFIT)
                sl_price = normalize_price(level_price + STOP_LOSS) if STOP_LOSS > 0 else None
                
            if send_pending_order(level_price, lot, tp_price, sl_price):
                doldurulan += 1

    if doldurulan > 0:
        log_message(f"🌱 Ağ kaydı: {doldurulan} adet yeni nöbetçi emir ufuk çizgisine eklendi.")
        
    return True
# ═══════════════════════════════════════════════════════════════════════════════
# BAŞLANGIÇ KONTROLLERİ VE ANA DÖNGÜ
# ═══════════════════════════════════════════════════════════════════════════════

def run_startup_checks():
    global SYMBOL_INFO, FILLING_MODE
    log_message("=" * 60)
    log_message("USOUSD Dinamik Grid Robot v2 Baslatiliyor...")
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


# ==========================================
# METRIK-SCHNITTSTELLE FÜR DAS DASHBOARD
# ==========================================
def get_live_metrics():
    """
    Sammelt Echtzeit-Daten (Profit, Positionen, Preis) direkt aus dem
    MetaTrader 5 Terminal und reicht sie an den bot_runner weiter.
    """
    metrics = {
        "profit": 0.0,
        "open_positions": 0,
        "pending_orders": 0,
        "current_price": 0.0,
        "algo_trading_error": False,
    }

    # 1. Terminal-Status prüfen (Algo Trading an?)
    terminal_info = mt5.terminal_info()
    if terminal_info is None:
        return metrics

    if not terminal_info.trade_allowed:
        metrics["algo_trading_error"] = True

    # 2. Offene Positionen und Profit berechnen
    # HINWEIS: Falls du ein dynamisches Symbol nutzt, ersetze "USOUSD" durch deine Symbol-Variable
    positions = mt5.positions_get(symbol="USOUSD")
    if positions:
        metrics["open_positions"] = len(positions)
        metrics["profit"] = round(sum(pos.profit for pos in positions), 2)

    # 3. Ausstehende (Pending) Orders zählen
    orders = mt5.orders_get(symbol="USOUSD")
    if orders:
        metrics["pending_orders"] = len(orders)

    # 4. Aktuellen Preis abfragen
    tick = mt5.symbol_info_tick("USOUSD")
    if tick:
        metrics["current_price"] = tick.bid
    elif SIMULATED_PRICE > 0:
        # Fallback für den Mac-Simulator im Dashboard
        metrics["current_price"] = SIMULATED_PRICE

    return metrics


def main_loop():
    global IS_RUNNING, INITIAL_CLEANUP_DONE

    if not run_startup_checks():
        log_message("Baslangic kontrolleri basarisiz. Robot durduruluyor.", "ERROR")
        return

    log_message("Robot calismaya basladi. (Durdurmak icin Ctrl+C)")
    log_message("Manuel start bekleniyor... Lutfen manuel islem acin.")

    try:
        while IS_RUNNING:
            load_dynamic_settings() 
            if not is_market_open():
                time.sleep(MARKET_CLOSED_CHECK_INTERVAL)
                continue

            # 4. KURAL (ŞİDDETLİ KONTROL): İLK AÇILIŞTA YALNIZCA EMİRLER TEMİZLENİR
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
        # KAPANIŞ RİTÜELİ: KESİNLİKLE POZİSYONLARA DOKUNULMAZ, SADECE EMİRLER SİLİNİR
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
