"""
================================================================================
🛠️ USOUSD Yarı-Otomatik Dinamik Grid Robotu v3.0 (MODEL 3)
- Çift Yönlü (Hedge) Çalışma
- Zaman Dilimine (TF) Bağlı Akıllı Mum Kapanışı SL
- Bölge Yakma (Burn Zone) Özelliği
================================================================================
"""

import time
import datetime
import os
import platform
import json

# Temel Değişkenler
LOOP_INTERVAL_SECONDS = 1.0
ZONES = []
SYMBOL = "USOUSD"

def load_dynamic_settings():
    global LOOP_INTERVAL_SECONDS, ZONES, SYMBOL
    try:
        with open("settings_model3.json", "r", encoding="utf-8") as f:
            settings = json.load(f)
            LOOP_INTERVAL_SECONDS = settings.get("LOOP_INTERVAL_SECONDS", 1.0)
            ZONES = settings.get("ZONES", [])
            SYMBOL = settings.get("SYMBOL", "USOUSD")
    except Exception:
        pass

def save_burned_state_to_json():
    """Bölge yandığında durumu kalıcı olarak JSON'a geri yazar."""
    try:
        with open("settings_model3.json", "r", encoding="utf-8") as f:
            settings = json.load(f)
            
        settings["ZONES"] = ZONES
        
        with open("settings_model3.json", "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        log_message(f"JSON kaydetme hatası: {e}", "ERROR")

# ===============================================================================
# 🍏🪟 MAC / WINDOWS UYUMLULUK KÖPRÜSÜ
# ===============================================================================
if platform.system() == "Windows":
    import MetaTrader5 as mt5
    IS_MAC_TEST_MODE = False
else:
    IS_MAC_TEST_MODE = True
    print("⚠️ UYARI: Mac işletim sistemi algılandı. MT5 Sahte (Mock) modda çalışıyor!")
    MOCK_CURRENT_PRICE = 75.00
    
    class DummyMT5:
        TRADE_ACTION_PENDING = 5
        TRADE_ACTION_REMOVE = 8
        TRADE_ACTION_DEAL = 1
        ORDER_TYPE_BUY_LIMIT = 2
        ORDER_TYPE_BUY_STOP = 4
        ORDER_TYPE_SELL_LIMIT = 3
        ORDER_TYPE_SELL_STOP = 5
        POSITION_TYPE_BUY = 0
        POSITION_TYPE_SELL = 1
        ORDER_TIME_GTC = 0
        ORDER_FILLING_FOK = 0
        TRADE_RETCODE_DONE = 10009
        
        TIMEFRAME_M15 = 15
        TIMEFRAME_H1 = 16385
        TIMEFRAME_H4 = 16388
        TIMEFRAME_D1 = 16408

        def __init__(self):
            self.dummy_orders = [] 
            self.ticket_counter = 1

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
        def orders_get(self, symbol=None): return self.dummy_orders
        def positions_get(self, symbol=None): return []
        def order_check(self, request):
            class CheckResult: retcode = 0
            return CheckResult()
        def order_send(self, request):
            class SendResult: retcode = 10009
            if request.get("action") == self.TRADE_ACTION_PENDING:
                class DummyOrder:
                    def __init__(self, t, m, p, type):
                        self.ticket = t
                        self.magic = m
                        self.price_open = p
                        self.type = type
                self.dummy_orders.append(DummyOrder(self.ticket_counter, request.get("magic"), request.get("price"), request.get("type")))
                self.ticket_counter += 1
            elif request.get("action") == self.TRADE_ACTION_REMOVE:
                tk = request.get("order")
                self.dummy_orders = [o for o in self.dummy_orders if o.ticket != tk]
            return SendResult()
        
        # Sahte mum verisi
        def copy_rates_from_pos(self, symbol, timeframe, start, count):
            class DummyRate:
                def __init__(self):
                    self.close = MOCK_CURRENT_PRICE
            return [DummyRate()]

    mt5 = DummyMT5()

# ===============================================================================
# GLOBAL DEĞİŞKENLER VE YARDIMCILAR
# ===============================================================================
MAGIC_NUMBER = 300000 
MAX_DEVIATION = 20      
LOG_FILE_PATH = "grid_robot_m3_log.txt"
SYMBOL_INFO = None          
FILLING_MODE = mt5.ORDER_FILLING_FOK         
IS_RUNNING = True

TF_MAP = {
    "M15": mt5.TIMEFRAME_M15 if not IS_MAC_TEST_MODE else 15,
    "H1": mt5.TIMEFRAME_H1 if not IS_MAC_TEST_MODE else 16385,
    "H4": mt5.TIMEFRAME_H4 if not IS_MAC_TEST_MODE else 16388,
    "D1": mt5.TIMEFRAME_D1 if not IS_MAC_TEST_MODE else 16408,
}

def log_message(msg, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [{level}] {msg}"
    print(formatted)
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except: pass

def normalize_price(price):
    if SYMBOL_INFO is None: return round(price, 2)
    point = SYMBOL_INFO.point
    if point == 0: return price
    return round(round(price / point) * point, SYMBOL_INFO.digits)

def normalize_volume(volume):
    if SYMBOL_INFO is None: return volume
    return round(max(SYMBOL_INFO.volume_min, min(volume, SYMBOL_INFO.volume_max)), 2)

def get_current_price(is_buy):
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None: return None
    return tick.ask if is_buy else tick.bid

def get_orders():
    orders = mt5.orders_get(symbol=SYMBOL)
    return [o for o in orders if o.magic == MAGIC_NUMBER] if orders else []

def get_positions():
    pos = mt5.positions_get(symbol=SYMBOL)
    return [p for p in pos if p.magic == MAGIC_NUMBER] if pos else []

def cancel_order(ticket):
    mt5.order_send({"action": mt5.TRADE_ACTION_REMOVE, "order": ticket, "symbol": SYMBOL})

def close_position(pos):
    """Zarardaki işlemi piyasa fiyatından kapatır."""
    tick = mt5.symbol_info_tick(SYMBOL)
    if not tick: return
    
    type_dict = {
        mt5.POSITION_TYPE_BUY: mt5.ORDER_TYPE_SELL,
        mt5.POSITION_TYPE_SELL: mt5.ORDER_TYPE_BUY
    }
    price = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask
    
    req = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": pos.volume,
        "type": type_dict[pos.type],
        "position": pos.ticket,
        "price": price,
        "deviation": MAX_DEVIATION,
        "magic": MAGIC_NUMBER,
        "comment": "Model3_SL_Close",
        "type_filling": FILLING_MODE,
    }
    mt5.order_send(req)

def send_pending_order(price, lot, tp, sl, is_buy):
    curr = get_current_price(is_buy)
    if not curr: return
    
    if is_buy:
        o_type = mt5.ORDER_TYPE_BUY_LIMIT if price < curr else mt5.ORDER_TYPE_BUY_STOP
    else:
        o_type = mt5.ORDER_TYPE_SELL_LIMIT if price > curr else mt5.ORDER_TYPE_SELL_STOP

    req = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": SYMBOL,
        "volume": normalize_volume(lot),
        "type": o_type,
        "price": price,
        "deviation": MAX_DEVIATION,
        "magic": MAGIC_NUMBER,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": FILLING_MODE,
        "tp": tp,
    }
    if sl > 0: req["sl"] = sl
    mt5.order_send(req)

# ===============================================================================
# MODEL 3 AKILLI MOTORU
# ===============================================================================

def check_smart_sl(zone, open_positions):
    """Mum kapanışını kontrol eder ve gerekirse işlemleri kapatıp bölgeyi yakar."""
    if not zone.get("use_smart_sl", False): return False
    
    tf_str = zone.get("smart_sl_tf", "H4")
    tf_val = TF_MAP.get(tf_str, mt5.TIMEFRAME_H4)
    
    # Son kapanmış mumu çek (index 1)
    rates = mt5.copy_rates_from_pos(SYMBOL, tf_val, 1, 1)
    if rates is None or len(rates) == 0: return False
    
    # Mac/Mock modunda oran listesi veya dict dönebilir, güvenli okuma:
    last_close = rates[0].close if hasattr(rates[0], 'close') else rates[0][4] 
    
    z_min = float(zone["min_price"])
    z_max = float(zone["max_price"])
    
    sl_triggered = False
    
    # Kural: Kapanış Max üstünde ise BUY'lar kardadır, SELL'ler zarardadır (SELL SL olur).
    if last_close > z_max:
        for p in open_positions:
            if p.type == mt5.POSITION_TYPE_SELL and p.profit < 0:
                close_position(p)
                sl_triggered = True
                
    # Kural: Kapanış Min altında ise SELL'ler kardadır, BUY'lar zarardadır (BUY SL olur).
    elif last_close < z_min:
        for p in open_positions:
            if p.type == mt5.POSITION_TYPE_BUY and p.profit < 0:
                close_position(p)
                sl_triggered = True

    return sl_triggered

def check_classic_sl(zone, current_price):
    """Fiyat klasik SL değerlerine çarptı mı kontrolü."""
    z_dir = zone.get("direction", "BOTH")
    if z_dir in ["BOTH", "BUY"] and zone.get("use_buy_sl", False):
        if current_price <= float(zone.get("buy_sl", 0)): return True
        
    if z_dir in ["BOTH", "SELL"] and zone.get("use_sell_sl", False):
        if current_price >= float(zone.get("sell_sl", 999999)): return True
        
    return False

def burn_the_zone(zone_index):
    """Bölgeyi deaktif eder, bekleyen emirlerini temizler ve kaydeder."""
    global ZONES
    if not ZONES[zone_index].get("is_burned", False):
        ZONES[zone_index]["is_burned"] = True
        log_message(f"🔥 BÖLGE {zone_index+1} YANDI! SL tetiklendi, bölge deaktif edildi.", "WARN")
        save_burned_state_to_json()
        
        # Bu bölgedeki (sınırlar içindeki) robot emirlerini temizle
        orders = get_orders()
        z_min = float(ZONES[zone_index]["min_price"])
        z_max = float(ZONES[zone_index]["max_price"])
        for o in orders:
            if z_min <= o.price_open <= z_max:
                cancel_order(o.ticket)

def deploy_grid_for_zone(zone, current_price, existing_orders, existing_positions):
    z_min = float(zone["min_price"])
    z_max = float(zone["max_price"])
    z_dir = zone.get("direction", "BOTH")
    
    # Bölgede miyiz?
    if not (z_min <= current_price <= z_max): return
    
    # Olan fiyatları topla
    occupied_buy = set(normalize_price(p.price_open) for p in existing_positions if p.type == mt5.POSITION_TYPE_BUY)
    occupied_buy.update(normalize_price(o.price_open) for o in existing_orders if o.type in [mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_BUY_STOP])
    
    occupied_sell = set(normalize_price(p.price_open) for p in existing_positions if p.type == mt5.POSITION_TYPE_SELL)
    occupied_sell.update(normalize_price(o.price_open) for o in existing_orders if o.type in [mt5.ORDER_TYPE_SELL_LIMIT, mt5.ORDER_TYPE_SELL_STOP])

    # BUY GRID
    if z_dir in ["BOTH", "BUY"]:
        step = float(zone.get("buy_grid", 0.05))
        ref_price = round(current_price / step) * step
        
        p = ref_price
        while p <= z_max:
            if normalize_price(p) not in occupied_buy:
                tp = normalize_price(p + float(zone.get("buy_tp", 0.05)))
                sl = float(zone.get("buy_sl", 0.0)) if zone.get("use_buy_sl", False) else 0.0
                send_pending_order(normalize_price(p), float(zone.get("buy_lot", 0.01)), tp, sl, True)
            p += step
            
        p = ref_price - step
        while p >= z_min:
            if normalize_price(p) not in occupied_buy:
                tp = normalize_price(p + float(zone.get("buy_tp", 0.05)))
                sl = float(zone.get("buy_sl", 0.0)) if zone.get("use_buy_sl", False) else 0.0
                send_pending_order(normalize_price(p), float(zone.get("buy_lot", 0.01)), tp, sl, True)
            p -= step

    # SELL GRID
    if z_dir in ["BOTH", "SELL"]:
        step = float(zone.get("sell_grid", 0.05))
        ref_price = round(current_price / step) * step
        
        p = ref_price
        while p <= z_max:
            if normalize_price(p) not in occupied_sell:
                tp = normalize_price(p - float(zone.get("sell_tp", 0.05)))
                sl = float(zone.get("sell_sl", 0.0)) if zone.get("use_sell_sl", False) else 0.0
                send_pending_order(normalize_price(p), float(zone.get("sell_lot", 0.01)), tp, sl, False)
            p += step
            
        p = ref_price - step
        while p >= z_min:
            if normalize_price(p) not in occupied_sell:
                tp = normalize_price(p - float(zone.get("sell_tp", 0.05)))
                sl = float(zone.get("sell_sl", 0.0)) if zone.get("use_sell_sl", False) else 0.0
                send_pending_order(normalize_price(p), float(zone.get("sell_lot", 0.01)), tp, sl, False)
            p -= step

def manage_model_3():
    tick = mt5.symbol_info_tick(SYMBOL)
    if not tick: return
    current_price = tick.bid
    
    positions = get_positions()
    orders = get_orders()
    
    for idx, zone in enumerate(ZONES):
        if zone.get("is_burned", False): 
            continue # Yanmış bölgeyi atla
            
        # 1. Klasik SL Kontrolü
        if check_classic_sl(zone, current_price):
            if zone.get("burn_on_sl", True):
                burn_the_zone(idx)
            continue
            
        # 2. Akıllı SL (Mum Kapanışı) Kontrolü
        if check_smart_sl(zone, positions):
            if zone.get("burn_on_sl", True):
                burn_the_zone(idx)
            continue
            
        # 3. SL Olmadıysa, Ağ Örmeye Devam Et
        deploy_grid_for_zone(zone, current_price, orders, positions)

# ===============================================================================
# ANA DÖNGÜ
# ===============================================================================

def main_loop():
    global SYMBOL_INFO, IS_RUNNING
    log_message("USOUSD Model 3 Baslatiliyor...")
    if not mt5.initialize():
        log_message("MT5 baglantisi kurulamadi", "ERROR")
        return

    SYMBOL_INFO = mt5.symbol_info(SYMBOL)
    if not SYMBOL_INFO: return

    while IS_RUNNING:
        load_dynamic_settings()
        manage_model_3()
        time.sleep(LOOP_INTERVAL_SECONDS)

if __name__ == "__main__":
    main_loop()