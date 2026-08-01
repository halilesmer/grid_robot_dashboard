# src/utils/trade_utils.py


class TradeState:
    """Tüm robot modelleri için ortak durum hafızası"""

    algo_trading_disabled = False
    last_error_message = ""


def normalize_volume(mt5_module, symbol, volume):
    """Lot miktarını MT5'in kabul edeceği tam formata zorlar (Örn: 0.020000001 -> 0.02)"""
    symbol_info = mt5_module.symbol_info(symbol)
    if symbol_info is None:
        return float(volume)
    step = symbol_info.volume_step
    # Adıma göre tam yuvarlama yap ve string üzerinden float'a çevirerek bozulmayı önle
    rounded_vol = round(volume / step) * step
    return float(f"{rounded_vol:.6f}")


def cancel_all_pending_orders(mt5_module, magic=None):
    """Sadece bekleyen emirleri (PENDING) siler, açık işlemlere (AKTİF) dokunmaz."""
    orders = mt5_module.orders_get()
    if orders is None or len(orders) == 0:
        return
    for order in orders:
        # Eğer belirli bir magic number verilmişse, sadece o robota ait olanları sil
        if magic is not None and order.magic != magic:
            continue
        request = {
            "action": mt5_module.TRADE_ACTION_REMOVE,
            "order": order.ticket,
        }
        mt5_module.order_send(request)


def safe_send_order(mt5_module, request, log_func=None):
    """
    Merkezi Emir Gönderici ve Hata Yakalayıcı.
    """
    try:
        # KESİN KURAL: Gönderilmeden önce LOT değerini MT5'in beklediği hassasiyete göre kusursuzlaştır
        if "volume" in request and "symbol" in request:
            request["volume"] = normalize_volume(
                mt5_module, request["symbol"], request["volume"]
            )

        # Sadece yeni emir gönderimlerinde (PENDING/DEAL) ön kontrol yapılır.
        if request.get("action") in [
            mt5_module.TRADE_ACTION_PENDING,
            mt5_module.TRADE_ACTION_DEAL,
        ]:
            check = mt5_module.order_check(request)
            if check is None or check.retcode != 0:
                retcode = check.retcode if check else -1
                if retcode == 10027:
                    TradeState.algo_trading_disabled = True
                    TradeState.last_error_message = "Algo Trading im MT5 deaktiviert!"
                if log_func:
                    log_func(f"❌ MT5 Check Hatası! Kodu: {retcode}", "ERROR")
                return False

        # Asıl Emri Gönder
        result = mt5_module.order_send(request)

        if result is None:
            last_err = mt5_module.last_error()
            TradeState.last_error_message = (
                f"Keine Antwort vom MT5 Terminal: {last_err}"
            )
            if log_func:
                log_func(f"❌ MT5 Request başarısız (None): {last_err}", "ERROR")
            return False

        # 10009 = TRADE_RETCODE_DONE
        if result.retcode != 10009:
            if result.retcode == 10027:
                TradeState.algo_trading_disabled = True
                TradeState.last_error_message = "Algo Trading im MT5 deaktiviert!"
            if log_func:
                last_err = mt5_module.last_error()
                log_func(
                    f"❌ MT5 Emir Hatası! Kodu: {result.retcode}, Hata: {last_err}",
                    "ERROR",
                )
            return False

        # İşlem başarılıysa hatayı sıfırla
        TradeState.algo_trading_disabled = False
        TradeState.last_error_message = ""
        return True

    except Exception as e:
        TradeState.last_error_message = f"Kritik Hata: {str(e)}"
        if log_func:
            log_func(f"💥 MT5 Request Exception: {str(e)}", "ERROR")
        return False


def get_algo_status():
    return TradeState.algo_trading_disabled


def get_last_error_msg():
    return TradeState.last_error_message


def close_position(mt5_module, position, symbol, log_func=None):
    """
    Kapatılacak açık pozisyonu (market price üzerinden) kapatır.
    """
    tick = mt5_module.symbol_info_tick(symbol)
    if tick is None:
        if log_func:
            log_func(f"Fiyat alınamadı, {position.ticket} kapatılamıyor.", "ERROR")
        return False

    # Buy ise Sell ile, Sell ise Buy ile kapat
    if position.type == mt5_module.POSITION_TYPE_BUY:
        trade_type = mt5_module.ORDER_TYPE_SELL
        price = tick.bid
    else:
        trade_type = mt5_module.ORDER_TYPE_BUY
        price = tick.ask

    request = {
        "action": mt5_module.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": position.volume,
        "type": trade_type,
        "position": position.ticket,
        "price": price,
        "deviation": 20,
        "type_time": mt5_module.ORDER_TIME_GTC,
        "type_filling": mt5_module.ORDER_FILLING_IOC, # Genelde IOC kapatmak için yeterlidir
    }

    return safe_send_order(mt5_module, request, log_func)

