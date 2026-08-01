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
ORDER_TYPE = "BUY"
SYMBOL = "USOUSD"

# ==========================================
# GLOBAL DEĞİŞKENLER (Bot Manager İçin Zorunlu)
# ==========================================
REFERENCE_PRICE = None
SYMBOL_INFO = None
FILLING_MODE = None
ACTIVE_ZONE = None
ACTIVE_ZONE_IDX = None

IS_RUNNING = False
INITIAL_CLEANUP_DONE = False
SIMULATED_PRICE = 0.0

active_zones_state = {} # Hafıza Kurtarma ve Zombi Emir Yönetimi



# ==========================================
# METRİK ARAYÜZÜ (Dashboard için)
# ==========================================
def get_live_metrics():
    """
    Dashboard'un arka planda okuyabilmesi için güncel verileri toplar.
    """
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

    # 1. Terminal-Status prüfen
    terminal_info = mt5.terminal_info()
    if terminal_info is None:
        return metrics

    if not terminal_info.trade_allowed:
        metrics["algo_trading_error"] = True

    # 2. Offene Positionen und Profit
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions:
        metrics["open_positions"] = len(positions)
        metrics["profit"] = round(sum(pos.profit for pos in positions), 2)

    # 3. Bekleyen Emirler
    orders = mt5.orders_get(symbol=SYMBOL)
    if orders:
        metrics["pending_orders"] = len(orders)

    # 4. Fiyat
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
    """Her döngüde arka plan sürecine ait doğru settings.json dosyasını okur"""
    # DİKKAT: Hangi modeldeysen o modelin global değişkenlerini buraya yazmalısın!
    global ZONES, LOOP_INTERVAL_SECONDS

    try:
        # İŞTE BURASI! Pylance'ın beklediği kullanım tam olarak bu satır:
        settings_file = get_settings_file(
            "Model 2"
        )  # model_1.py dosyasındaysan buraya "Model 1" yaz!

        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)

            # Model 2'nin kendi ayarları (Model 1'deysen GRID_STEP, TAKE_PROFIT vs. yazmalısın)
            ZONES = settings.get("ZONES", [])
            LOOP_INTERVAL_SECONDS = settings.get("LOOP_INTERVAL_SECONDS", 1.0)
    except Exception:
        pass


def log_message(msg, level="INFO"):
    """Sadece print yapar. bot_manager.py bunu yakalayıp log dosyasına aktarır."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [{level}] {msg}"
    print(formatted)


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
    if IS_MAC_TEST_MODE and SIMULATED_PRICE > 0:
        return SIMULATED_PRICE

    try:
        tick = mt5.symbol_info_tick(SYMBOL)
        if tick is None:
            return None
        if ORDER_TYPE.upper() == "BUY":
            return tick.ask
        else:
            return tick.bid
    except Exception as e:
        log_message(f"Fiyat alınamadı (Bağlantı koptu): {e}", "ERROR")
        return None

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
    return [o for o in orders if BASE_MAGIC_NUMBER <= o.magic < BASE_MAGIC_NUMBER + 1000]

def get_all_robot_positions():
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions is None: return None
    target_type = mt5.POSITION_TYPE_BUY if ORDER_TYPE.upper() == "BUY" else mt5.POSITION_TYPE_SELL
    return [p for p in positions if BASE_MAGIC_NUMBER <= p.magic < BASE_MAGIC_NUMBER + 1000 and p.type == target_type]

def get_all_manual_positions():
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions is None: return None
    target_type = mt5.POSITION_TYPE_BUY if ORDER_TYPE.upper() == "BUY" else mt5.POSITION_TYPE_SELL
    return [p for p in positions if not (BASE_MAGIC_NUMBER <= p.magic < BASE_MAGIC_NUMBER + 1000) and p.type == target_type]

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
    for i, zone in enumerate(ZONES):
        if float(zone.get("min_price", 0)) <= price <= float(zone.get("max_price", 0)):
            return zone, i
    return None, None

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


def send_pending_order(price, lot, tp_price, sl_price=None, zone_idx=0):
    current_price = get_current_market_price()
    if current_price is None:
        return False
    order_type = get_pending_order_type(price, current_price)

    magic_num = BASE_MAGIC_NUMBER + zone_idx + 1
    
    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": SYMBOL,
        "volume": normalize_volume(lot),
        "type": order_type,
        "price": price,
        "deviation": MAX_DEVIATION,
        "magic": magic_num,
        "comment": f"Model2_Zone{zone_idx + 1}",
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

def process_zone_commands():
    """UI'dan gelen zone komutlarını (Başlat/Beklet/Temizle) okur ve uygular."""
    global active_zones_state
    account_id = os.environ.get("ACTIVE_ACCOUNT_ID", "default")
    commands_file = f"logs/commands_{account_id}.json"
    
    if os.path.exists(commands_file):
        try:
            with open(commands_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return # Dosya henüz boşsa bir sonraki turda dene
                commands = json.loads(content)
            
            # Her bir zone komutu için işlem yap
            for zone_idx_str, command in commands.items():
                zone_idx = int(zone_idx_str)
                state = command.get("state", "START") # START, PAUSE, CLEAR
                
                # Durum değişikliğini kaydet
                active_zones_state[zone_idx] = state
                
            # İşlenmiş komut dosyasını sil ki tekrar tekrar işlenmesin
            os.remove(commands_file)
        except json.JSONDecodeError:
            # Race condition: Streamlit dosyayı yazarken yarıda yakaladık
            pass # Bir sonraki turda tekrar okumayı deneyecek
        except Exception as e:
            log_message(f"Komutlar işlenirken hata: {e}", "ERROR")

def manage_dynamic_grid():
    global REFERENCE_PRICE, ACTIVE_ZONE, ACTIVE_ZONE_IDX

    process_zone_commands()

    robot_positions = get_all_robot_positions()
    manual_positions = get_all_manual_positions()
    robot_orders = get_all_robot_orders()

    if robot_positions is None or manual_positions is None or robot_orders is None:
        return False 

    current_price = get_current_market_price()
    if current_price is None: return False

    # 1. Zombi Emir Temizliği (Garbage Collection) ve CLEAR Pozisyon Kapatma
    for order in robot_orders:
        order_zone_idx = order.magic - BASE_MAGIC_NUMBER - 1
        if active_zones_state.get(order_zone_idx, "START") != "START":
            log_message(f"🧹 Zombi Emir Temizliği: Bölge {order_zone_idx+1} pasif, emir siliniyor. (Bilet: {order.ticket})")
            cancel_order(order)
            
    # CLEAR olan bölgeler için pozisyonları kapat
    for pos in robot_positions:
        pos_zone_idx = pos.magic - BASE_MAGIC_NUMBER - 1
        if active_zones_state.get(pos_zone_idx, "START") == "CLEAR":
            log_message(f"🧹 BÖLGE {pos_zone_idx+1} TEMİZLENİYOR: Pozisyon kapatılıyor (Bilet: {pos.ticket})")
            close_position(mt5, pos, SYMBOL, log_message)
            
    # Listeyi güncelle
    robot_orders = get_all_robot_orders()
    robot_positions = get_all_robot_positions() # Pozisyonlar da kapanmış olabilir
    if robot_orders is None or robot_positions is None:
        return False
    
    # 2. Kısmi Dolum (Partial Fill) Kontrolü
    # Her pozisyon için, volume kontrolü yap.
    for pos in robot_positions:
        pos_zone_idx = pos.magic - BASE_MAGIC_NUMBER - 1
        if 0 <= pos_zone_idx < len(ZONES):
            target_lot = max(0.01, min(5.0, float(ZONES[pos_zone_idx].get("lot_size", 0.01))))
            
            # Hassasiyet sorunu: Float kaynaklı mikro farklar için round kullan
            remaining_lot = round(target_lot - pos.volume, 8)
            
            # Eğer gerçekleşen hacim hedeflenenden küçükse ve min volume sınırından büyükse
            vol_min = SYMBOL_INFO.volume_min if SYMBOL_INFO else 0.01
            if remaining_lot >= vol_min:
                # Kalan hacim için limit emir var mı diye bak
                has_pending = False
                for order in robot_orders:
                    if order.magic == pos.magic and abs(order.price_open - pos.price_open) < (SYMBOL_INFO.point * 2 if SYMBOL_INFO else 0.02):
                        has_pending = True
                        break
                
                if not has_pending and active_zones_state.get(pos_zone_idx, "START") == "START":
                    log_message(f"🔄 Kısmi Dolum Tespit Edildi: Bölge {pos_zone_idx+1} | Kalan {remaining_lot} lot için emir gönderiliyor.")
                    
                    if ORDER_TYPE.upper() == "BUY":
                        tp_price = normalize_price(pos.price_open + float(ZONES[pos_zone_idx].get("take_profit", 0.05)))
                        sl_val = float(ZONES[pos_zone_idx].get("stop_loss", 0.0))
                        sl_price = normalize_price(pos.price_open - sl_val) if sl_val > 0 else None
                    else:
                        tp_price = normalize_price(pos.price_open - float(ZONES[pos_zone_idx].get("take_profit", 0.05)))
                        sl_val = float(ZONES[pos_zone_idx].get("stop_loss", 0.0))
                        sl_price = normalize_price(pos.price_open + sl_val) if sl_val > 0 else None
                        
                    send_pending_order(pos.price_open, remaining_lot, tp_price, sl_price, zone_idx=pos_zone_idx)

    # Listeyi tekrar güncelle
    robot_orders = get_all_robot_orders()

    current_zone, current_zone_idx = get_active_zone(current_price)

    # BÖLGE DEĞİŞİMİ / ÇIKIŞI
    if current_zone != ACTIVE_ZONE:
        if ACTIVE_ZONE is not None:
            zone_clear_flag = ACTIVE_ZONE.get("clear_on_exit", True)
            if zone_clear_flag:
                log_message(f"🧹 Bölge ({ACTIVE_ZONE.get('min_price')}-{ACTIVE_ZONE.get('max_price')}) dışına çıkıldı. Temizlik AÇIK: Eski emirler siliniyor...")
                for order in robot_orders:
                    # Sadece çıktığımız bölgenin emirlerini silmek daha güvenli olabilir
                    target_magic = BASE_MAGIC_NUMBER + ACTIVE_ZONE_IDX + 1
                    if order.magic == target_magic:
                        cancel_order(order)
                robot_orders = get_all_robot_orders()
            else:
                log_message(f"🪤 Bölge ({ACTIVE_ZONE.get('min_price')}-{ACTIVE_ZONE.get('max_price')}) dışına çıkıldı. Temizlik KAPALI: Mevcut bekleyen emirler tuzak olarak bırakıldı.")

        ACTIVE_ZONE = current_zone
        ACTIVE_ZONE_IDX = current_zone_idx
        # DÜZELTME 1: Yeni bölgeye geçince eski merkez hafızasını sıfırla! (Matematiksel Uyum)
        REFERENCE_PRICE = None

    # BÖLGE KONTROLÜ
    if ACTIVE_ZONE is not None:
        # Eski ham okuma satırlarını siliyoruz, yerine bu GÜVENLİK KİLİDİ kısmını koyuyoruz:
        raw_grid = float(ACTIVE_ZONE.get("grid_step", 0.05))
        raw_lot = float(ACTIVE_ZONE.get("lot_size", 0.01))

        # Sınırlandırmalar:
        # Grid en az 0.05 olabilir (Sınırsız üst limit)
        # Lot en az 0.01, en çok 5.0 olabilir.
        grid_step = max(0.05, raw_grid)
        lot_val = max(0.01, min(5.0, raw_lot))

        tp_val = float(ACTIVE_ZONE.get("take_profit", 0.05))
        sl_val = float(ACTIVE_ZONE.get("stop_loss", 0.0))

        yeni_referans = calculate_reference_price(grid_step)
        if REFERENCE_PRICE != yeni_referans:
            REFERENCE_PRICE = yeni_referans
            log_message(f"📍 BÖLGE İÇİ OTONOM AĞ: Yeni Merkez -> {REFERENCE_PRICE}")
            
        # Eğer bölge PAUSE (Beklet) durumundaysa yeni emir dizilimi yapma
        if active_zones_state.get(ACTIVE_ZONE_IDX, "START") != "START":
            return True
            
    else:
        REFERENCE_PRICE = None
        return True

    desired_levels = calculate_grid_levels(REFERENCE_PRICE, ACTIVE_ZONE)
    tolerance = (SYMBOL_INFO.point * 2) if SYMBOL_INFO else 0.02

    # UZAKTA KALAN BEKLEYEN EMİRLERİ SİL
    z_min = float(ACTIVE_ZONE.get("min_price", 0))
    z_max = float(ACTIVE_ZONE.get("max_price", 0))

    silinen_emir_sayisi = 0  # <--- YENİ: Sayaç eklendi

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
            silinen_emir_sayisi += (
                1  
            )

    # <--- YENİ: Döngü bitince (for ile aynı hizada) log yazdır
    if silinen_emir_sayisi > 0:
        log_message(
            f"🧹 Ağ kaydı: Uzakta kalan/Gereksiz {silinen_emir_sayisi} adet bekleyen emir silindi."
        )

    # EKSİK OLAN SEVİYELERİ DOLDUR
    mevcut_seviyeler = get_existing_levels(grid_step) 

    eklenen_emir_sayisi = 0  # <--- YENİ: Sayaç eklendi

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

            # <--- YENİ: Sadece 'send_pending_order' yazan satırı aşağıdaki gibi if içine al
            if send_pending_order(level_price, lot_val, tp_price, sl_price, zone_idx=ACTIVE_ZONE_IDX):
                eklenen_emir_sayisi += 1

    # <--- YENİ: Döngü bitince (for ile aynı hizada) log yazdır
    if eklenen_emir_sayisi > 0:
        log_message(
            f"🌱 Ağ kaydı: {eklenen_emir_sayisi} adet yeni nöbetçi emir ufuk çizgisine eklendi."
        )

    return True

# ═══════════════════════════════════════════════════════════════════════════════
# BAŞLANGIÇ KONTROLLERİ VE ANA DÖNGÜ
# ═══════════════════════════════════════════════════════════════════════════════


def run_startup_checks():
    global SYMBOL_INFO, FILLING_MODE
    log_message("=" * 60)
    log_message("USOUSD Dinamik Grid Robot v2.2 (MODEL 2) Baslatiliyor...")
    log_message("=" * 60)

    # DİKKAT: mt5.initialize() bloğu TAMAMEN SİLİNDİ!
    # Çünkü bot_runner.py bu bağlantıyı bize özel MT5 path'i ile zaten kurdu.

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

    # 2. Uyanış Taraması ve Hafıza Kurtarma (State Recovery)
    global active_zones_state
    active_zones_state = {}
    
    robot_positions = get_all_robot_positions()
    robot_orders = get_all_robot_orders()
    
    # 1. Eğer mt5 sunucusu o anda koptuysa None döner. Kesinlikle listeye atayıp devam etme!
    if robot_positions is None or robot_orders is None:
        log_message("Kritik Hata: MT5'ten mevcut pozisyon veya emir listesi alınamadı (None döndü). Bağlantı stabil değil, başlangıç reddedildi.", "ERROR")
        mt5.shutdown()
        return False
    
    # Hangi bölgelerde işlem/emir varsa onları START olarak kabul et.
    for pos in robot_positions:
        zone_idx = pos.magic - BASE_MAGIC_NUMBER - 1
        active_zones_state[zone_idx] = "START"
        
    for order in robot_orders:
        zone_idx = order.magic - BASE_MAGIC_NUMBER - 1
        active_zones_state[zone_idx] = "START"
        
    if active_zones_state:
        log_message(f"🧠 Hafıza Kurtarıldı: Aktif bölgeler: {list(active_zones_state.keys())}")

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
            
            # 6. Kritik Hata (Crash / Disconnect) Koruması
            term_info = mt5.terminal_info()
            if term_info is None or not term_info.trade_allowed:
                log_message("⚠️ Terminal kapalı veya Algo Trading devre dışı! Bağlantı bekleniyor...", "WARN")
                time.sleep(10)
                continue
                
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

            try:
                manage_dynamic_grid()
            except Exception as e:
                log_message(f"🚨 Hata (Crash Koruması): manage_dynamic_grid'de hata: {e}", "ERROR")
            
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
