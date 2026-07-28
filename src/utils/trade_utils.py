# src/utils/trade_utils.py


class TradeState:
    """Tüm robot modelleri için ortak durum hafızası"""

    algo_trading_disabled = False


def safe_send_order(mt5_module, request, log_func=None):
    """
    Merkezi Emir Gönderici ve Hata Yakalayıcı.
    """
    # Sadece yeni emir gönderimlerinde (PENDING/DEAL) ön kontrol (order_check) yapılır.
    # Emir silme (REMOVE) işleminde order_check kullanılamaz.
    if request.get("action") in [
        mt5_module.TRADE_ACTION_PENDING,
        mt5_module.TRADE_ACTION_DEAL,
    ]:
        check = mt5_module.order_check(request)
        if check is None or check.retcode != 0:
            if check is not None and check.retcode == 10027:
                TradeState.algo_trading_disabled = True
            if log_func:
                log_func(
                    f"❌ MT5 Check Hatası! Kodu: {check.retcode if check else 'Yok'}",
                    "ERROR",
                )
            return False

    # Asıl Emri Gönder
    result = mt5_module.order_send(request)
    if result is None or result.retcode != 10009:  # 10009 = TRADE_RETCODE_DONE
        if result is not None and result.retcode == 10027:
            TradeState.algo_trading_disabled = True
        if log_func:
            last_err = mt5_module.last_error()
            log_func(
                f"❌ MT5 Emir Hatası! Kodu: {result.retcode if result else 'Yok'}, Hata: {last_err}",
                "ERROR",
            )
        return False

    # İşlem başarılıysa hatayı sıfırla
    TradeState.algo_trading_disabled = False
    return True


def get_algo_status():
    return TradeState.algo_trading_disabled
