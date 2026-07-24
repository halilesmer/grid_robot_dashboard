"""
================================================================================
🛠️ USOUSD Yarı-Otomatik Dinamik Grid Robotu v2.2
MetaTrader 5 Python API ile çalışan algoritmik ticaret robotu
================================================================================
Yazar: AI Assistant
Versiyon: 2.2 (Dinamik/Kayan Grid & Hayalet Emir Temizliği)
Açıklama: Manuel tetiklemeli, dinamik lotlu, kayan (trailing) grid sistemi
================================================================================
"""

import time
import datetime
import sys
import os
import platform
from statistics import median
import json
import threading

# Global Değişkenleri Başlangıç İçin Tanımlayalım
GRID_STEP = 0.05
TAKE_PROFIT = 0.05
LEVELS_BELOW = 6
LEVELS_ABOVE = 6
DEFAULT_LOT = 0.01
MAX_OPEN_POSITIONS = 999
MAX_PRICE_LIMIT = 120.00
MIN_PRICE_LIMIT = 20.00

def load_dynamic_settings():
    """Her döngüde arayüzden gelen güncel settings.json dosyasını okur"""
    global GRID_STEP, TAKE_PROFIT, LEVELS_BELOW, LEVELS_ABOVE
    global DEFAULT_LOT, MAX_OPEN_POSITIONS, MAX_PRICE_LIMIT, MIN_PRICE_LIMIT
    try:
        with open("settings.json", "r", encoding="utf-8") as f:
            settings = json.load(f)
            GRID_STEP = settings.get("GRID_STEP", 0.05)
            TAKE_PROFIT = settings.get("TAKE_PROFIT", 0.05)
            LEVELS_BELOW = settings.get("LEVELS_BELOW", 6)
            LEVELS_ABOVE = settings.get("LEVELS_ABOVE", 6)
            DEFAULT_LOT = settings.get("DEFAULT_LOT", 0.01)
            MAX_OPEN_POSITIONS = settings.get("MAX_OPEN_POSITIONS", 999)
            MAX_PRICE_LIMIT = settings.get("MAX_PRICE_LIMIT", 120.00)
            MIN_PRICE_LIMIT = settings.get("MIN_PRICE_LIMIT", 20.00)
    except Exception as e:
        pass # Dosya yoksa veya hata olursa varsayılan değerlerle devam et

# ===============================================================================
# 🍏🪟 MAC / WINDOWS UYUMLULUK KÖPRÜSÜ
# ===============================================================================
if platform.system() == "Windows":
    import MetaTrader5 as mt5
    IS_MAC_TEST_MODE = False
else:
    IS_MAC_TEST_MODE = True
    print("⚠️ UYARI: Mac işletim sistemi algılandı. MT5 Sahte (Mock) modda çalışıyor!")
    
class DummyMT5:
        """Mac üzerinde test yapabilmek için HAFIZALI sahte MT5 motoru"""
        def __init__(self):
            self.dummy_orders = [] # Robotun emirleri hatırlayacağı hafıza
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
                bid = 75.00
                ask = 75.05
            return Tick()

        # HAFIZADAKİ EMİRLERİ GÖNDER
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
            
            # Eğer yeni emir ekleniyorsa, hafızaya kaydet
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
                
            # Eğer emir siliniyorsa, hafızadan çıkar
            elif request.get("action") == self.TRADE_ACTION_REMOVE:
                ticket_to_remove = request.get("order")
                self.dummy_orders = [o for o in self.dummy_orders if o.ticket != ticket_to_remove]
                
            return SendResult()

# ===============================================================================
# HIER IST DIE KORREKTUR: Überschreibe den echten Markt NUR auf dem Mac!
if IS_MAC_TEST_MODE:
    mt5 = DummyMT5()
# ===============================================================================
# ===============================================================================

# ═══════════════════════════════════════════════════════════════════════════════
# # ═══════════════════════════════════════════════════════════════════════════════
# 1. KULLANICI AYARLARI PANELİ (DETAYLI AÇIKLAMALI)
# ═══════════════════════════════════════════════════════════════════════════════

# --- GENEL BAĞLANTI AYARLARI ---
BROKER_SERVER = "Eightcap-Demo"   # Sadece bilgi amaçlı log (kayıt) ekranında görünen sunucu adıdır. Kodun çalışmasını etkilemez.
SYMBOL        = "USOUSD"          # Robotun işlem yapacağı enstrüman. Grafiğin sol üstünde yazan isimle birebir aynı olmalıdır (Örn: XAUUSD).
ORDER_TYPE    = "BUY"             # İşlem yönü ("BUY" veya "SELL"). Yükselişten kâr için "BUY", düşüş için "SELL". Robot tek yönlü çalışır.
MAGIC_NUMBER  = 123456            # Robotun T.C. Kimlik Numarası. Robot sadece bu mührü taşıyan kendi işlemlerini yönetir, manuel işlemlerine karışmaz.

# --- GRID (IZGARA) VE İŞLEM AYARLARI ---
GRID_STEP    = 0.05   # Ağın delik genişliği. Emirlerin birbirinden kaç dolar/cent uzaklıkta olacağını belirler (Örn: 0.20 yaparsan her 20 centte bir açar).
TAKE_PROFIT  = 0.05   # Kâr al (TP) mesafesi. Açılan işlemin kaç dolarlık bir kâr gördüğünde otomatik kapanacağını belirler.
STOP_LOSS    = 0      # Zarar kesme (SL) mesafesi. Grid sistemleri maliyet düşürdüğü için genelde "0" (yok) bırakılır.
LEVELS_BELOW = 6      # Merkezin (canlı işlemin) ALTINA kaç tane hazır nöbetçi emir dizileceğini belirler.
LEVELS_ABOVE = 6      # Merkezin (canlı işlemin) ÜSTÜNE kaç tane hazır nöbetçi emir dizileceğini belirler.

# --- GÜVENLİK VE SINIRLANDIRMA AYARLARI ---
MAX_OPEN_POSITIONS = 999     # KALKAN: Robotun aynı anda açabileceği maksimum işlem sayısı. Bu sayıya ulaşırsa yeni emir dizmeyi durdurur.
MAX_PRICE_LIMIT = 120.00   # Tavan Fiyat. Enstrüman bu fiyatın üstüne çıkarsa robot yeni emir açmayı durdurur.
MIN_PRICE_LIMIT =  20.00   # Taban Fiyat. Enstrüman bu fiyatın altına düşerse robot yeni emir açmayı durdurur.
MAX_DEVIATION   =  20      # Fiyat kayması (Slippage) toleransı. Ani haberlerde fiyat zıplarsa emrin reddedilmesini önleyen esneklik payıdır.

# --- DİNAMİK LOT VE KASA YÖNETİMİ ---
DEFAULT_LOT = 0.01   # Aşağıdaki ekstrem eşiklere ulaşılmadığı sürece kullanılacak standart "Güvenli Bölge" lot miktarıdır.

# 🔽 AŞAĞI YÖNLÜ EŞİKLER (fiyat düştükçe artan lot)
DOWN_THRESHOLDS = [
    (60.00, 0.02),   # Fiyat 60 doların altına inerse açılacak limit emirlerin lotunu 0.02 yap (alt alta virgülle yeni satırlar eklenebilir).
]

# 🔼 YUKARI YÖNLÜ EŞİKLER (fiyat yükseldikçe artan lot)
UP_THRESHOLDS = [
    (90.00,  0.01),  # Fiyat 90 doların üstüne çıkarsa açılacak stop emirlerin lotunu 0.01 yap.
]

# --- DÖNGÜ VE KAYIT AYARLARI ---
LOOP_INTERVAL_SECONDS = 1            # Robotun piyasayı kontrol etme ve eksik emir tarama hızı (Saniye cinsinden). 5 saniye idealdir.
MARKET_CLOSED_CHECK_INTERVAL = 60    # Hafta sonu/Piyasa kapalıyken aracı kurumu yormamak için tarama hızını 60 saniyeye (1 dakikaya) düşürür.
LOG_TO_FILE = True                   # Robotun yaptığı işlemleri kalıcı bir metin dosyasına kaydedip kaydetmeyeceği (True=Evet).
LOG_FILE_PATH = "grid_robot_log.txt" # Kayıtların tutulacağı dosyanın adı. Robotun olduğu klasörde otomatik oluşur.

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL DEĞİŞKENLER
# ═══════════════════════════════════════════════════════════════════════════════

REFERENCE_PRICE = None      # Ana referans seviyesi
SYMBOL_INFO = None          # Sembol bilgisi
FILLING_MODE = None         # Broker fill politikası
IS_RUNNING = True
INITIAL_CLEANUP_DONE = False # Robot ilk açıldığında eski emirleri temizledi mi?

# ═══════════════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════════════════════

def log_message(msg, level="INFO"):
    """Log mesajını konsola ve dosyaya yazar."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [{level}] {msg}"
    print(formatted)
    if LOG_TO_FILE:
        try:
            with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")
        except Exception as e:
            print(f"[HATA] Log dosyasına yazılamadı: {e}")

def normalize_price(price):
    """Fiyatı sembolün point değerine göre normalize eder."""
    if SYMBOL_INFO is None:
        return round(price, 2)
    point = SYMBOL_INFO.point
    if point == 0:
        return price
    digits = SYMBOL_INFO.digits
    return round(round(price / point) * point, digits)

def normalize_volume(volume):
    """Lot değerini broker limitlerine göre normalize eder."""
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
    """Güncel piyasa fiyatını döndürür."""
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        return None
    if ORDER_TYPE.upper() == "BUY":
        return tick.ask
    else:
        return tick.bid

def is_market_open():
    """Piyasanın açık olup olmadığını kontrol eder."""
    info = mt5.symbol_info(SYMBOL)
    if info is None:
        return False
    return info.trade_mode == 4

def determine_fill_mode():
    """Broker'ın desteklediği fill politikasını tespit eder."""
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
    """Hedef fiyat seviyesine göre dinamik lot belirler."""
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
    if orders is None: return None  # HATA ÇÖZÜMÜ 2: API Hatası varsa listeyi boşaltma, None dön
    return [o for o in orders if o.magic == MAGIC_NUMBER]

def get_all_robot_positions():
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions is None: return None
    # KURAL 2: Sadece BUY işlemlerini gör, SELL işlemlerini tamamen yok say!
    return [p for p in positions if p.magic == MAGIC_NUMBER and p.type == mt5.POSITION_TYPE_BUY]

def get_all_manual_positions():
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions is None: return None
    # KURAL 2: Sadece BUY işlemlerini gör, SELL işlemlerini tamamen yok say!
    return [p for p in positions if p.magic != MAGIC_NUMBER and p.type == mt5.POSITION_TYPE_BUY]

def get_existing_levels():
    levels = set()
    orders = get_all_robot_orders()
    r_pos = get_all_robot_positions()
    m_pos = get_all_manual_positions()
    
    if orders:
        for order in orders: levels.add(normalize_price(order.price_open))
    if r_pos:
        for pos in r_pos: levels.add(normalize_price(pos.price_open))
    if m_pos:
        for pos in m_pos: levels.add(normalize_price(pos.price_open))
    return levels

def cancel_order(order):
    request = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": order.ticket,
        "symbol": SYMBOL
    }
    result = mt5.order_send(request)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        return True
    return False

def close_position(position):
    """Patron işlemi kapattığında, robotun açık olan pozisyonlarını anında kapatır."""
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None: return False
    
    request = {
        "action": 1, # mt5.TRADE_ACTION_DEAL
        "position": position.ticket,
        "symbol": SYMBOL,
        "volume": position.volume,
        "type": 1 if position.type == 0 else 0, # 0: BUY, 1: SELL
        "price": tick.bid if position.type == 0 else tick.ask,
        "deviation": MAX_DEVIATION,
        "magic": MAGIC_NUMBER,
        "comment": "Robot_Temizlik",
        "type_time": 0, # mt5.ORDER_TIME_GTC
        "type_filling": FILLING_MODE,
    }
    result = mt5.order_send(request)
    if result and result.retcode == 10009: # TRADE_RETCODE_DONE
        return True
    return False

def calculate_reference_price():
    current_price = get_current_market_price()
    if current_price is None: return None
    
    # KURAL 1: Merkez HER ZAMAN güncel piyasa fiyatı olacak.
    # Spam Koruması (Mıknatıs): Fiyat 1-2 cent oynadığında ağ bozulmasın diye, 
    # güncel fiyatı Grid Adımına (örn: 0.50'nin katlarına) sabitliyoruz.
    snapped_price = round(current_price / GRID_STEP) * GRID_STEP
    return normalize_price(snapped_price)


def calculate_grid_levels(reference_price):
    """Merkez fiyata göre KAYAN grid seviyelerini hesaplar."""
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
        
    check = mt5.order_check(request)
    if check is None or check.retcode != 0:
        return False

    result = mt5.order_send(request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        return False
    return True

def modify_position_tp_sl(position, tp_price, sl_price=None):
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": position.ticket,
        "symbol": SYMBOL,
        "tp": tp_price,
    }
    if sl_price is not None and STOP_LOSS > 0:
        request["sl"] = sl_price
        
    result = mt5.order_send(request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        return False
    return True

# ═══════════════════════════════════════════════════════════════════════════════
# ANA DİNAMİK YÖNETİM MOTORU (YENİ)
# ═══════════════════════════════════════════════════════════════════════════════

def manage_dynamic_grid():
    global REFERENCE_PRICE

    robot_positions = get_all_robot_positions()
    manual_positions = get_all_manual_positions()
    robot_orders = get_all_robot_orders()
    
    # 0. KORUMA: API KÖRLÜĞÜ KONTROLÜ
    if robot_positions is None or manual_positions is None or robot_orders is None:
        return False 
        
    total_positions = len(robot_positions) + len(manual_positions)

  # 1. ADIM: MANUEL START KONTROLÜ (PATRON MASADAN KALKTI MI?)
    if not manual_positions:
        silinen_emir = 0
        kapanan_islem = 0
        
        # 1. Bekleyen ufuk emirlerini temizle
        if robot_orders:
            for order in robot_orders:
                if cancel_order(order): silinen_emir += 1
                
        # 2. Aktif olan robot işlemlerini kapat
        if robot_positions:
            for pos in robot_positions:
                if close_position(pos): kapanan_islem += 1
                
        if silinen_emir > 0 or kapanan_islem > 0:
            log_message(f"🛑 Patron işlemi kapattı! Temizlik: {silinen_emir} emir iptal, {kapanan_islem} robot işlemi kapatıldı.")
            log_message("✅ Sistem tamamen sıfırlandı. Yeni bir manuel start bekleniyor...")
            
        # DİKKAT: Bu iki satır if'in İÇİNDE DEĞİL, dışındadır. Her halükarda çalışıp robotu durdurur!
        REFERENCE_PRICE = None
        return True
    
    # 2. YENİ MERKEZİ (GÜNCEL FİYATI) BELİRLE VE GÜNCELLE
    yeni_referans = calculate_reference_price()
    if yeni_referans is None:
        return False

    if REFERENCE_PRICE != yeni_referans:
        if REFERENCE_PRICE is None:
            log_message(f"🎯 Hedef Kilitlendi: Ağ Güncel Fiyata Kuruluyor -> {yeni_referans}")
        else:
            log_message(f"🌊 DİNAMİK AĞ: Fiyat Hareket Etti, Yeni Merkez -> {yeni_referans}")
        REFERENCE_PRICE = yeni_referans

    # Eğer manuel pozisyon varsa ve TP'si yoksa ona TP ekle
    if manual_positions and not robot_positions:
        pos = manual_positions[0]
        if pos.tp == 0.0:
            tp_price = normalize_price(pos.price_open + TAKE_PROFIT) if ORDER_TYPE.upper() == "BUY" else normalize_price(pos.price_open - TAKE_PROFIT)
            if modify_position_tp_sl(pos, tp_price):
                 log_message(f"✅ Manuel BUY işleme Kar Al (TP) eklendi: {tp_price}")

        # 3. YENİ: MAKSİMUM POZİSYON KONTROLÜ (GÜVENLİK KALKANI)
    if total_positions >= MAX_OPEN_POSITIONS:
            if robot_orders:
                log_message(f"🚨 KALKAN AKTİF: Maksimum açık pozisyon limitine ({MAX_OPEN_POSITIONS}) ulaşıldı!")
                log_message("🛡️ Riski sınırlamak için bekleyen tüm ufuk emirleri iptal ediliyor. Yeni emir dizilmeyecek...")
                silinen_kalkan = 0
                for order in robot_orders:
                    if cancel_order(order):
                        silinen_kalkan += 1
                if silinen_kalkan > 0:
                    log_message(f"✅ Marjin koruması için {silinen_kalkan} adet bekleyen emir silindi.")
            return True # Aşağı inip yeni emir dizmesini engellemek için fonksiyonu burada kesiyoruz.

    # 3. İSTENEN DİNAMİK SEVİYELERİ HESAPLA (5 Alt, 5 Üst vs.)
    desired_levels = calculate_grid_levels(REFERENCE_PRICE)

    # 4. HATA ÇÖZÜMÜ: UZAKTA KALAN (SINIR DIŞI) EMİRLERİ SİL
    silinen_emir_sayisi = 0
    for order in robot_orders:
        order_price = normalize_price(order.price_open)
        is_valid = False
        for dl in desired_levels:
            if abs(order_price - dl) <= (SYMBOL_INFO.point * 2 if SYMBOL_INFO else 0.02):
                is_valid = True
                break
                
        # Eğer bu bekleyen emir, yeni merkezin hesapladığı ağın dışındaysa SİL!
        if not is_valid:
            if cancel_order(order):
                silinen_emir_sayisi += 1
                
    if silinen_emir_sayisi > 0:
        log_message(f"🧹 Ağ kaydı: Uzakta kalan/Gereksiz {silinen_emir_sayisi} adet emir silindi.")

    # 5. EKSİK OLAN YENİ UFUK KADEMELERİNİ DOLDUR
    doldurulan = 0
    mevcut_seviyeler = get_existing_levels() 
    
    for level_price in desired_levels:
        if level_price > MAX_PRICE_LIMIT or level_price < MIN_PRICE_LIMIT:
            continue
            
        is_occupied = False
        for exist_lvl in mevcut_seviyeler:
             if abs(level_price - exist_lvl) <= (SYMBOL_INFO.point * 2 if SYMBOL_INFO else 0.02):
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
    log_message("USOUSD Dinamik Grid Robot v2.2 Baslatiliyor...")
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

def get_live_metrics():
    """Web arayüzü (Streamlit) için canlı piyasa ve hesap metriklerini toplar."""
    current_price = get_current_market_price()
    robot_positions = get_all_robot_positions()
    robot_orders = get_all_robot_orders()
    
    profit = 0.0
    open_positions = 0
    pending_orders = 0
    
    if robot_positions:
        open_positions = len(robot_positions)
        # Bütün açık pozisyonların anlık kâr/zararını topla
        profit = sum(pos.profit for pos in robot_positions)
        
    if robot_orders:
        pending_orders = len(robot_orders)
        
    return {
        "profit": profit,
        "open_positions": open_positions,
        "pending_orders": pending_orders,
        "current_price": current_price if current_price else 0.0
    }

def main_loop():
    global IS_RUNNING, INITIAL_CLEANUP_DONE

    if not run_startup_checks():
        log_message("Baslangic kontrolleri basarisiz. Robot durduruluyor.", "ERROR")
        return

    log_message("Robot calismaya basladi. (Durdurmak icin Ctrl+C)")
    log_message("Manuel start bekleniyor... Lutfen manuel islem acin.")

    try:
        while IS_RUNNING:
            load_dynamic_settings() # 👈 YENİ: Her döngüde güncel ayarları yükle!
            if not is_market_open():
                time.sleep(MARKET_CLOSED_CHECK_INTERVAL)
                continue

            # --- YENİ EKLENEN OTOMATİK TEMİZLİK RİTÜELİ ---
            if not INITIAL_CLEANUP_DONE:
                eski_emirler = get_all_robot_orders()
                if eski_emirler:
                    log_message("🚀 Başlangıç Temizliği: Eski ayarlardan kalan tüm bekleyen emirler siliniyor...")
                    for emir in eski_emirler:
                        cancel_order(emir)
                    log_message("✅ Temizlik bitti. Ağ, yeni ayarlarınızla güncel merkeze göre sıfırdan örülecek.")
                INITIAL_CLEANUP_DONE = True
            # ----------------------------------------------

            manage_dynamic_grid()
            
            time.sleep(LOOP_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        log_message("Kullanici tarafindan durduruldu.", "WARN")
    finally:
        log_message("MT5 baglantisi kapatiliyor...")
        mt5.shutdown()
        log_message("Robot sonlandirildi.")


if __name__ == "__main__":
    main_loop()