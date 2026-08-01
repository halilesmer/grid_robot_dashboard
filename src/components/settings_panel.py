# components/settings_panel.py
import streamlit as st
import uuid
import json
import os
from src.constants.tooltips import SETTINGS_TOOLTIPS

# Yeni model 3 bileşenimizi içeri alıyoruz:
from src.components.model3_settings import render_model_3_settings


def render_settings_panel(current_settings, model_name="Model 1", account_id="default"):
    """
    JSON'dan beslenen Grid ve Risk Ayarları Kompakt Form Bileşeni
    """
    st.markdown(f"##### ⚙️ {model_name} Parametreleri")

    if model_name == "Model 1":
        return render_model_1_settings(current_settings, account_id)
    elif model_name == "Model 2":
        return render_model_2_settings(current_settings, account_id)
    elif model_name == "Model 3":
        return render_model_3_settings(current_settings)

    return None


def render_model_1_settings(current_settings, account_id):
    with st.form(f"settings_form_m1_{account_id}"):
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        with col1:
            grid_step = st.number_input(
                "Grid Adımı (GRID_STEP)",
                value=float(current_settings.get("GRID_STEP", 0.05)),
                step=0.01,
                format="%.2f",
                help=SETTINGS_TOOLTIPS["GRID_STEP"],
            )
            take_profit = st.number_input(
                "Kâr Al (TAKE_PROFIT)",
                value=float(current_settings.get("TAKE_PROFIT", 0.05)),
                step=0.01,
                format="%.2f",
                help=SETTINGS_TOOLTIPS["TAKE_PROFIT"],
            )

        with col2:
            levels_below = st.number_input(
                "Alt Seviye (LEVELS_BELOW)",
                value=int(current_settings.get("LEVELS_BELOW", 10)),
                step=1,
                help=SETTINGS_TOOLTIPS["LEVELS_BELOW"],
            )
            levels_above = st.number_input(
                "Üst Seviye (LEVELS_ABOVE)",
                value=int(current_settings.get("LEVELS_ABOVE", 10)),
                step=1,
                help=SETTINGS_TOOLTIPS["LEVELS_ABOVE"],
            )

        with col3:
            default_lot = st.number_input(
                "Varsayılan Lot (DEFAULT_LOT)",
                value=float(current_settings.get("DEFAULT_LOT", 0.01)),
                step=0.01,
                format="%.2f",
                help=SETTINGS_TOOLTIPS["DEFAULT_LOT"],
            )
            max_positions = st.number_input(
                "Maks. Pozisyon (MAX_POSITIONS)",
                value=int(current_settings.get("MAX_OPEN_POSITIONS", 20)),
                step=1,
                help=SETTINGS_TOOLTIPS["MAX_OPEN_POSITIONS"],
            )

        with col4:
            min_price = st.number_input(
                "Taban Fiyat (MIN_PRICE)",
                value=float(current_settings.get("MIN_PRICE_LIMIT", 60.0)),
                step=1.0,
                help=SETTINGS_TOOLTIPS["MIN_PRICE_LIMIT"],
            )
            max_price = st.number_input(
                "Tavan Fiyat (MAX_PRICE)",
                value=float(current_settings.get("MAX_PRICE_LIMIT", 100.0)),
                step=1.0,
                help=SETTINGS_TOOLTIPS["MAX_PRICE_LIMIT"],
            )

        col_b1, col_b2 = st.columns([2, 1])
        with col_b1:
            loop_interval = st.number_input(
                "Kontrol Sıklığı Saniye (LOOP_INTERVAL)",
                value=float(current_settings.get("LOOP_INTERVAL_SECONDS", 1.0)),
                step=0.1,
                format="%.1f",
                help=SETTINGS_TOOLTIPS["LOOP_INTERVAL_SECONDS"],
            )

        with col_b2:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "💾 Ayarları Güncelle", help="Ayarları anında sisteme kaydeder."
            )

        if submitted:
            return {
                "GRID_STEP": grid_step,
                "TAKE_PROFIT": take_profit,
                "LEVELS_BELOW": levels_below,
                "LEVELS_ABOVE": levels_above,
                "DEFAULT_LOT": default_lot,
                "MAX_OPEN_POSITIONS": max_positions,
                "MAX_PRICE_LIMIT": max_price,
                "MIN_PRICE_LIMIT": min_price,
                "LOOP_INTERVAL_SECONDS": loop_interval,
            }

    return None


def _default_zone():
    return {
        "min_price": 70.0,
        "max_price": 80.0,
        "grid_step": 0.05,
        "lot_size": 0.01,
        "take_profit": 0.05,
        "stop_loss": 0.0,
        "clear_on_exit": True,
    }


def _send_zone_command(account_id: str, zone_idx: int, state: str):
    """Atomik yazma ile commands JSON dosyasına komut gönderir."""
    commands_file = f"logs/commands_{account_id}.json"
    current = {}
    if os.path.exists(commands_file):
        try:
            with open(commands_file, "r", encoding="utf-8") as f:
                current = json.load(f)
        except Exception:
            pass
    current[str(zone_idx)] = {"state": state}
    os.makedirs("logs", exist_ok=True)
    tmp = commands_file + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(current, f)
    os.replace(tmp, commands_file)


def render_model_2_settings(current_settings, account_id):
    zones_session_key = f"model2_zones_{account_id}"

    # İlk açılışta: config boşsa 1 default bölge ile başlat
    if zones_session_key not in st.session_state:
        saved_zones = current_settings.get("ZONES", [])
        if not saved_zones:
            saved_zones = [_default_zone()]
        st.session_state[zones_session_key] = saved_zones

    # Komut geçmişini JSON'dan oku ki buton durumlarını bilelim
    commands_file = f"logs/commands_{account_id}.json"
    zone_states = {}
    if os.path.exists(commands_file):
        try:
            with open(commands_file, "r", encoding="utf-8") as f:
                zone_states = json.load(f)
        except Exception:
            pass

    # ── Temel Ayarlar ──────────
    st.markdown("###### ⚖️ Temel İşlem Ayarları")
    t_col1, t_col2, t_col3 = st.columns([1, 1, 1])
    with t_col1:
        order_type_val = current_settings.get("ORDER_TYPE", "BUY")
        order_type = st.selectbox(
            "İşlem Yönü",
            options=["BUY", "SELL"],
            index=0 if order_type_val == "BUY" else 1,
            key=f"m2_order_type_{account_id}",
        )
    with t_col2:
        symbol = st.text_input(
            "Sembol",
            value=current_settings.get("SYMBOL", "USOUSD"),
            key=f"m2_symbol_{account_id}",
        )
    with t_col3:
        loop_interval = st.number_input(
            "Kontrol Sıklığı (Sn)",
            value=float(current_settings.get("LOOP_INTERVAL_SECONDS", 1.0)),
            step=0.1,
            key=f"m2_loop_{account_id}",
        )

    st.markdown("---")
    st.markdown("###### 🎯 Dinamik Bölgeler (Zones)")

    updated_zones = []
    delete_any = False

    for idx, zone in enumerate(st.session_state[zones_session_key]):
        # Bu bölgenin güncel durumunu tespit et (Varsayılan olarak temizlenmiş kabul et)
        current_state = zone_states.get(str(idx), {}).get("state", "CLEAR")

        # Dinamik Buton Metinleri
        start_label = "✅ Başladı" if current_state == "START" else "▶️ Başlat"
        pause_label = "🟡 Beklemede" if current_state == "PAUSE" else "⏸️ Beklet"
        clear_label = "🗑️ Temizlendi" if current_state == "CLEAR" else "🗑️ Temizle"

        with st.container(border=True):
            hdr_col, bc1, bc2, bc3 = st.columns([2.5, 1, 1, 1])
            with hdr_col:
                st.markdown(
                    f"**🗺️ Bölge {idx + 1}** — "
                    f"${zone.get('min_price', '?')} → ${zone.get('max_price', '?')}"
                )

            with bc1:
                if st.button(
                    start_label,
                    key=f"start_{account_id}_{idx}",
                    use_container_width=True,
                    type="primary" if current_state == "START" else "secondary",
                    help="Bölgeyi aktif hale getirir, robot belirlenen ayarlarla emir göndermeye başlar.",
                ):
                    _send_zone_command(account_id, idx, "START")
                    st.rerun()  # UI'yi anında güncellemek için

            with bc2:
                if st.button(
                    pause_label,
                    key=f"pause_{account_id}_{idx}",
                    use_container_width=True,
                    type="primary" if current_state == "PAUSE" else "secondary",
                    help="Sadece bekleyen emirleri iptal eder, açık pozisyonlara dokunmaz.",
                ):
                    _send_zone_command(account_id, idx, "PAUSE")
                    st.rerun()

            with bc3:
                if st.button(
                    clear_label,
                    key=f"clear_{account_id}_{idx}",
                    use_container_width=True,
                    type="primary" if current_state == "CLEAR" else "secondary",
                    help="Bu bölgedeki bekleyen tüm emirleri siler ve açık pozisyonları anında kapatır.",
                ):
                    _send_zone_command(account_id, idx, "CLEAR")
                    st.rerun()

            # Alt satır: Parametre girişleri (TEMİZ LABELLAR)
            zc1, zc2, zc3, zc4, zc5, zc6 = st.columns([1, 1, 1, 1, 1, 1])
            with zc1:
                z_min = st.number_input(
                    "Alt Sınır ($)",
                    key=f"min_price_{idx}_{account_id}",
                    min_value=0.0,
                    value=max(0.0, float(zone.get("min_price", 0.0))),
                    step=0.1,
                    format="%.2f",
                    help="💵 Robotun çalışacağı EN DÜŞÜK varil fiyatı ($).",
                )
            with zc2:
                z_max = st.number_input(
                    "Üst Sınır ($)",
                    key=f"max_price_{idx}_{account_id}",
                    min_value=0.0,
                    value=max(0.0, float(zone.get("max_price", 0.0))),
                    step=0.1,
                    format="%.2f",
                    help="💵 Robotun çalışacağı EN YÜKSEK varil fiyatı ($).",
                )
            with zc3:
                z_grid = st.number_input(
                    "Grid Adımı ($)",
                    key=f"grid_step_{idx}_{account_id}",
                    min_value=0.05,
                    value=max(0.05, float(zone.get("grid_step", 0.05))),
                    step=0.05,
                    format="%.2f",
                    help="📏 Emirlerin kaç $ aralıkla dizileceği (Ağ adımı).",
                )
            with zc4:
                z_lot = st.number_input(
                    "Lot (📦)",
                    key=f"lot_size_{idx}_{account_id}",
                    min_value=0.01,
                    max_value=5.0,
                    value=max(0.01, min(5.0, float(zone.get("lot_size", 0.01)))),
                    step=0.01,
                    format="%.2f",
                    help="📦 İşlem başına pozisyon büyüklüğü (Lot).",
                )
            with zc5:
                z_tp = st.number_input(
                    "Kâr Al ($)",
                    key=f"take_profit_{idx}_{account_id}",
                    min_value=0.01,
                    value=max(0.01, float(zone.get("take_profit", 0.05))),
                    step=0.01,
                    format="%.2f",
                    help="🎯 Pozisyon başına hedeflenen kâr ($).",
                )
            with zc6:
                z_sl = st.number_input(
                    "Stop Loss ($)",
                    key=f"stop_loss_{idx}_{account_id}",
                    min_value=0.0,
                    value=max(0.0, float(zone.get("stop_loss", 0.0))),
                    step=0.01,
                    format="%.2f",
                    help="🛡️ Zarar kes mesafesi ($). 0.00 ise kapalıdır.",
                )

            opt_c1, opt_c2 = st.columns([3, 1])
            with opt_c1:
                z_clear = st.checkbox(
                    "🧹 Çıkışta Temizle",
                    key=f"clear_on_exit_{idx}_{account_id}",
                    value=bool(zone.get("clear_on_exit", True)),
                    help="🧹 İşaretliyken, fiyat bölgeden çıkarsa bekleyen emirler silinir.",
                )
            with opt_c2:
                delete_btn = st.checkbox(
                    "🗑️ Bu bölgeyi sil",
                    key=f"del_{idx}_{account_id}",
                    help="Bu bölgeyi kaldır.",
                )

        if not delete_btn:
            updated_zones.append(
                {
                    "min_price": z_min,
                    "max_price": z_max,
                    "grid_step": z_grid,
                    "lot_size": z_lot,
                    "take_profit": z_tp,
                    "stop_loss": z_sl,
                    "clear_on_exit": z_clear,
                }
            )
        else:
            delete_any = True

    if delete_any:
        st.session_state[zones_session_key] = updated_zones
        st.rerun()

    # ── Alt Aksiyon Butonları ─────────────────────────────────────────────────
    col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
    with col_b1:
        if st.button("➕ Yeni Bölge Ekle", use_container_width=True):
            st.session_state[zones_session_key].append(_default_zone())
            st.rerun()
    with col_b2:
        if st.button("💾 Ayarları Güncelle", use_container_width=True, type="primary"):
            return {
                "ORDER_TYPE": order_type,
                "SYMBOL": symbol,
                "LOOP_INTERVAL_SECONDS": loop_interval,
                "ZONES": updated_zones,
            }

    return None
