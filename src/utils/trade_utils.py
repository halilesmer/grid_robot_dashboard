# src/utils/trade_utils.py


class TradeState:
    """Tüm robot modelleri için ortak durum hafızası"""

    algo_trading_disabled = False
    last_error_message = ""


def safe_send_order(mt5_module, request, log_func=None):
    """
    Merkezi Emir Gönderici ve Hata Yakalayıcı.
    """
    try:
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
