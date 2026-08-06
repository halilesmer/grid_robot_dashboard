# components/settings_panel.py
import streamlit as st
import uuid
import json
import os
from src.constants.tooltips import SETTINGS_TOOLTIPS

# Modal (Dialog) pencerelerimizi içeri alıyoruz:
from src.components.dialogs import confirm_clear_dialog, confirm_delete_zone_dialog

# 🌟 YENİ: Merkezi yol (path) yöneticisini içeri aktarıyoruz
from src.utils.paths import get_cmd_path, get_ui_state_path


@st.dialog("⚠️ Kaydedilmemiş Ayarlar")
def confirm_start_with_changes_dialog(account_id, zone_id, idx):
    st.write("Bu bölgede değiştirdiğiniz ancak henüz kaydetmediğiniz ayarlar var.")
    st.write("**Değiştirdiğiniz yeni ayarlar ile mi başlasın?**")

    c1, c2 = st.columns(2)
    if c1.button("✅ Evet (Kaydet ve Başlat)", use_container_width=True):
        st.session_state[f"save_req_{account_id}"] = True
        _handle_zone_action(account_id, zone_id, idx, "START")
        st.rerun()
    if c2.button("❌ Hayır (İptal)", use_container_width=True):
        st.rerun()


def render_settings_panel(current_settings, model_name="Model 2", account_id="default"):
    """
    JSON'dan beslenen Dinamik Bölge (Zone) Ayarları (Model 2)
    """
    # Başlık ve yerleşim işlemleri doğrudan Model 2'nin içinde yönetiliyor
    return render_model_2_settings(current_settings, account_id)


def _default_zone():
    return {
        "id": str(uuid.uuid4()),  # Hafıza kaybını önleyen benzersiz kimlik
        "symbol": "USOUSD",
        "order_type": "BUY",
        "min_price": 70.0,
        "max_price": 80.0,
        "grid_step": 0.05,
        "lot_size": 0.01,
        "take_profit": 0.05,
        "stop_loss": 0.0,
        "is_breakout": False,  # 🌟 YENİ: Kırılım/Momentum Modu
        "pullback_distance": 0.50,  # 🌟 YENİ: Geri Çekilme Mesafesi
        "levels_below": 5,
        "levels_above": 5,
        "max_positions": 10,
        "clear_on_exit": True,
        "clear_scope": "Sadece Emirler",
        "exit_condition": "Anlık Fiyat",
        "exit_timeframe": "M15",
    }


def _send_zone_command(account_id: str, zone_idx: int, state: str):
    """Atomik yazma ile commands JSON dosyasına komut gönderir."""
    commands_file = get_cmd_path(account_id)
    current = {}
    if os.path.exists(commands_file):
        try:
            with open(commands_file, "r", encoding="utf-8") as f:
                current = json.load(f)
        except Exception:
            pass
    current[str(zone_idx)] = {"state": state}

    tmp = commands_file + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(current, f)
    os.replace(tmp, commands_file)


def _handle_zone_action(account_id: str, zone_id: str, idx: int, state: str):
    """Buton tıklamalarında UI'ı çökertmeden durumu güncelleyen Callback fonksiyonu."""
    # 1. Bota komut gönder (Bot idx kullanır)
    _send_zone_command(account_id, idx, state)

    # 2. Anlık UI hafızasını GÜVENLİ (ID bazlı) güncelle
    ui_state_key = f"ui_zone_states_{account_id}"
    if ui_state_key in st.session_state:
        st.session_state[ui_state_key][zone_id] = state


def _force_upper_symbol(key: str):
    """Sembol inputuna yazılan değeri anında büyük harfe çevirir."""
    if key in st.session_state:
        st.session_state[key] = str(st.session_state[key]).upper().strip()


def render_model_2_settings(current_settings, account_id):
    zones_session_key = f"model2_zones_{account_id}"
    ui_state_key = f"ui_zone_states_{account_id}"

    # 1. İlk açılış: Kayıtlı bölgelere ID ataması yaparak güvenle yükle
    if zones_session_key not in st.session_state:
        saved_zones = current_settings.get("ZONES", [])
        for z in saved_zones:
            if "id" not in z:
                z["id"] = str(uuid.uuid4())

        if not saved_zones:
            saved_zones = [_default_zone()]
        st.session_state[zones_session_key] = saved_zones

    # 2. Arayüz Kalıcı Hafızasını ve Bot'tan Gelen Bildirimleri Yükle
    if ui_state_key not in st.session_state:
        st.session_state[ui_state_key] = {}

    # 🌟 GÜNCELLENDİ: Diskteki en son durumu oku (İlk açılışta veya yenilemede durumu koru)
    states_file = get_ui_state_path(account_id)
    if os.path.exists(states_file):
        try:
            with open(states_file, "r", encoding="utf-8") as f:
                saved_states = json.load(f)
                for i, z in enumerate(st.session_state[zones_session_key]):
                    zone_id = z["id"]
                    # Eğer bölge durum hafızasında yoksa veya Bot arka planda durum değiştirdiyse diskten yükle
                    if zone_id not in st.session_state[ui_state_key]:
                        st.session_state[ui_state_key][zone_id] = saved_states.get(
                            str(i), "CLEAR"
                        )
                    elif saved_states.get(str(i)) == "AUTO_CLEAR":
                        st.session_state[ui_state_key][zone_id] = "AUTO_CLEAR"
        except Exception:
            pass

    # Ana Başlık ve Input'u yan yana almak için sütunlara ayırıyoruz
    h_col1, h_col2 = st.columns([0.85, 0.15], vertical_alignment="center")
    with h_col1:
        st.markdown("##### ⚙️ Sistem Parametreleri")
    with h_col2:
        loop_interval = st.number_input(
            "Kontrol Sıklığı (Sn)",
            value=float(current_settings.get("LOOP_INTERVAL_SECONDS", 1.0)),
            step=0.1,
            key=f"m2_loop_{account_id}",
        )

    st.markdown("---")
    st.markdown("###### 🎯 Dinamik Bölgeler (Zones)")

    updated_zones = []

    # Bölgeleri Ekrana Çiz
    for idx, zone in enumerate(st.session_state[zones_session_key]):
        zone_id = zone.get("id")
        if not zone_id:
            zone_id = str(uuid.uuid4())
            zone["id"] = zone_id

        current_state = st.session_state[ui_state_key].get(zone_id, "CLEAR")

        start_label = "✅ Başladı" if current_state == "START" else "▶️ Başlat"
        pause_label = "🟡 Beklemede" if current_state == "PAUSE" else "⏸️ Beklet"
        clear_label = (
            "🗑️ Temizlendi"
            if current_state in ["CLEAR", "AUTO_CLEAR"]
            else "🗑️ Temizle"
        )

        # Orijinal dosyadan veriyi çek (Kıyaslama için)
        orig_zones = current_settings.get("ZONES", [])
        orig_zone = next((z for z in orig_zones if z.get("id") == zone_id), None)

        # 🛠️ Streamlit'in kendi çerçevesini kullanıyoruz
        with st.container(border=True):
            hdr_col, bc_upd, bc_div, bc1, bc2, bc3, bc4 = st.columns(
                [2.1, 1, 0.1, 1, 1, 1, 0.5]
            )

            with hdr_col:
                # Başlığı daha sonra (değişkenler okunduktan sonra) güncellemek için boş bir alan ayırıyoruz
                title_placeholder = st.empty()

            with bc_upd:
                upd_btn_placeholder = st.empty()

            with bc_div:
                st.markdown(
                    "<div style='text-align: center; font-size: 24px; color: #888; margin-top: 2px;'>|</div>",
                    unsafe_allow_html=True,
                )

            # 🌟 YENİ: Otomatik Temizlik Uyarı Mesajı
            if current_state == "AUTO_CLEAR":
                st.error(
                    "⚠️ **Bilgi:** Fiyat belirlenen sınırların dışına çıktığı için bu bölge otomatik olarak temizlendi ve durduruldu."
                )

            with bc1:
                start_btn_placeholder = st.empty()
            with bc2:
                st.button(
                    pause_label,
                    key=f"pause_{zone_id}_{account_id}",
                    use_container_width=True,
                    type="primary" if current_state == "PAUSE" else "secondary",
                    help="Yeni emir göndermeyi durdurur ve bekleyen emirleri siler. Açık işlemlere dokunmaz.",
                    on_click=_handle_zone_action,
                    args=(account_id, zone_id, idx, "PAUSE"),
                )
            with bc3:
                if st.button(
                    clear_label,
                    key=f"clear_{zone_id}_{account_id}",
                    use_container_width=True,
                    type="primary" if current_state == "CLEAR" else "secondary",
                    help="Acil Durum: Bekleyen emirleri siler ve AÇIK POZİSYONLARI ayara göre kapatır.",
                ):
                    # Lambda ile anlık değişkenleri (zone_id, idx) dondurarak modal'a gönderiyoruz
                    confirm_clear_dialog(
                        lambda acc=account_id, z_id=zone_id, i=idx: _handle_zone_action(
                            acc, z_id, i, "CLEAR"
                        )
                    )

            with bc4:
                # 🌟 YENİ: 3 Noktalı Açılır Menü (Dropdown)
                with st.popover("⋮", use_container_width=True):
                    if st.button(
                        "➕ Yeni Bölge Ekle",
                        key=f"add_{zone_id}_{account_id}",
                        use_container_width=True,
                    ):
                        st.session_state[zones_session_key].append(_default_zone())
                        st.rerun()
                    if st.button(
                        "🗑️ Bölgeyi Sil",
                        key=f"del_{zone_id}_{account_id}",
                        use_container_width=True,
                    ):

                        def remove_zone(target_id=zone_id):
                            st.session_state[zones_session_key] = [
                                z
                                for z in st.session_state[zones_session_key]
                                if z.get("id") != target_id
                            ]

                        confirm_delete_zone_dialog(f"Bölge {idx + 1}", remove_zone)

            zc1, zc2, zc3, zc4 = st.columns(4)
            with zc1:
                sym_key = f"sym_{zone_id}_{account_id}"
                z_symbol = st.text_input(
                    "Sembol",
                    key=sym_key,
                    value=str(zone.get("symbol", "USOUSD")).upper(),
                    on_change=_force_upper_symbol,
                    args=(sym_key,),
                    help="Bu bölgenin çalışacağı parite.",
                )
            with zc2:
                opts = ["BUY", "SELL", "BOTH"]
                cur_val = zone.get("order_type", "BUY")
                z_order_type = st.selectbox(
                    "İşlem Yönü",
                    options=opts,
                    index=opts.index(cur_val) if cur_val in opts else 0,
                    key=f"ord_{zone_id}_{account_id}",
                    help="Bu bölge ALIM mı, SATIM mı yoksa HER İKİSİNİ BİRDEN mi yapacak?",
                )
            with zc3:
                z_min = st.number_input(
                    "Alt Sınır ($)",
                    key=f"min_{zone_id}_{account_id}",
                    min_value=0.0,
                    value=max(0.0, float(zone.get("min_price", 0.0))),
                    step=0.1,
                    format="%.2f",
                    help="💵 Robotun çalışacağı EN DÜŞÜK fiyat.",
                )
            with zc4:
                z_max = st.number_input(
                    "Üst Sınır ($)",
                    key=f"max_{zone_id}_{account_id}",
                    min_value=0.0,
                    value=max(0.0, float(zone.get("max_price", 0.0))),
                    step=0.1,
                    format="%.2f",
                    help="💵 Robotun çalışacağı EN YÜKSEK fiyat.",
                )

            zc5, zc6, zc7, zc8 = st.columns(4)
            with zc5:
                z_grid = st.number_input(
                    "Grid Adımı ($)",
                    key=f"grid_{zone_id}_{account_id}",
                    min_value=0.01,
                    value=max(0.01, float(zone.get("grid_step", 0.05))),
                    step=0.01,
                    format="%.2f",
                    help="📏 Emirlerin kaç aralıkla dizileceği.",
                )
            with zc6:
                z_lot = st.number_input(
                    "Lot (📦)",
                    key=f"lot_{zone_id}_{account_id}",
                    min_value=0.01,
                    max_value=5.0,
                    value=max(0.01, min(5.0, float(zone.get("lot_size", 0.01)))),
                    step=0.01,
                    format="%.2f",
                    help="📦 İşlem başına lot miktarı.",
                )
            with zc7:
                z_tp = st.number_input(
                    "Kâr Al ($)",
                    key=f"tp_{zone_id}_{account_id}",
                    min_value=0.01,
                    value=max(0.01, float(zone.get("take_profit", 0.05))),
                    step=0.01,
                    format="%.2f",
                    help="🎯 Pozisyon başına hedeflenen kâr.",
                )
            with zc8:
                z_sl = st.number_input(
                    "Stop Loss ($)",
                    key=f"sl_{zone_id}_{account_id}",
                    min_value=0.0,
                    value=max(0.0, float(zone.get("stop_loss", 0.0))),
                    step=0.01,
                    format="%.2f",
                    help="🛡️ Zarar kes mesafesi (0 ise kapalıdır).",
                )

            # 🌟 YENİ EKLENEN BLOK: Kırılım / Momentum Ayarları
            st.markdown(
                "<div style='margin-top: 10px; margin-bottom: 5px;'><small style='color: gray;'>🚀 Kırılım / Momentum (Breakout) Stratejisi</small></div>",
                unsafe_allow_html=True,
            )
            brk_c1, brk_c2 = st.columns(2)
            with brk_c1:
                z_breakout = st.checkbox(
                    "Sadece Trend Yönüne Ağ Ör (Kırılım Modu)",
                    value=bool(zone.get("is_breakout", False)),
                    key=f"brk_{zone_id}_{account_id}",
                    help="Aktif edilirse robot Limit emir (düştükçe al) yerine SADECE Stop emir (kırılım/yükseldikçe al) kullanır. 'BOTH' seçilirse fiyatın üstüne Buy Stop, altına Sell Stop dizer.",
                )
            with brk_c2:
                z_pullback = st.number_input(
                    "Min. Geri Çekilme Mesafesi ($)",
                    key=f"pb_{zone_id}_{account_id}",
                    min_value=0.01,
                    value=float(zone.get("pullback_distance", 0.50)),
                    step=0.05,
                    format="%.2f",
                    disabled=not z_breakout,
                    help="TP olan bir emrin yerine yenisinin kurulması için fiyatın o seviyeden en az ne kadar uzağa çekilmesi gerektiğini belirler. (Geçersiz Fiyat hatalarını önler)",
                )

            # 🌟 Kayan Ağ (Sliding Grid) Emir Sayısı ve Güvenlik
            # Dinamik Disabled Mantığı: Kırılım açıksa ters yöndeki emir kutusunu soluklaştırır.
            disable_below = z_breakout and z_order_type == "BUY"
            disable_above = z_breakout and z_order_type == "SELL"

            zc9, zc10, zc11 = st.columns(3)
            with zc9:
                z_levels_below = st.number_input(
                    "Alt Seviye (LEVELS_BELOW)",
                    key=f"lb_{zone_id}_{account_id}",
                    min_value=1,
                    value=int(zone.get("levels_below", 5)),
                    step=1,
                    disabled=disable_below,
                    help="Fiyatın ALTINDA ağda aktif tutulacak bekleyen emir sayısı. (Kırılım modunda BUY için devre dışı kalır)",
                )
            with zc10:
                z_levels_above = st.number_input(
                    "Üst Seviye (LEVELS_ABOVE)",
                    key=f"la_{zone_id}_{account_id}",
                    min_value=1,
                    value=int(zone.get("levels_above", 5)),
                    step=1,
                    disabled=disable_above,
                    help="Fiyatın ÜSTÜNDE ağda aktif tutulacak bekleyen emir sayısı. (Kırılım modunda SELL için devre dışı kalır)",
                )
            with zc11:
                z_max_pos = st.number_input(
                    "Maks. Pozisyon",
                    key=f"mp_{zone_id}_{account_id}",
                    min_value=0,
                    value=int(zone.get("max_positions", 10)),
                    step=1,
                    help="Bu bölgede aynı anda açık olabilecek maksimum işlem sayısı. Sınırı kaldırmak için 0 girin (Sistem güvenliği için arka planda maks 500 olarak çalışır).",
                )

            # Alt satır 3: Çıkışta Temizle ve Seçenekleri
            z_clear = st.checkbox(
                "🧹 Bölgeden Çıkıldığında Temizlik Yap",
                key=f"clear_on_exit_{zone_id}_{account_id}",
                value=bool(zone.get("clear_on_exit", True)),
                help="İşaretliyken, fiyat bölgeden çıkarsa belirlenen kurala göre robot temizlik yapar.",
            )

            z_clear_scope = "Sadece Emirler"
            z_exit_cond = "Anlık Fiyat"
            z_exit_tf = "M15"

            if z_clear:
                st.markdown(
                    "<small style='color: gray;'>Temizlik Detayları</small>",
                    unsafe_allow_html=True,
                )
                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    z_clear_scope = st.selectbox(
                        "Neler Temizlensin?",
                        options=["Sadece Emirler", "Emirler + Açık Pozisyonlar"],
                        index=(
                            0
                            if zone.get("clear_scope", "Sadece Emirler")
                            == "Sadece Emirler"
                            else 1
                        ),
                        key=f"scope_{zone_id}_{account_id}",
                        help="Bölge dışına çıkıldığında açıkta olan işlemler kapatılsın mı?",
                    )
                with cc2:
                    z_exit_cond = st.selectbox(
                        "Çıkış Tetikleyicisi",
                        options=["Anlık Fiyat", "Mum Kapanışı"],
                        index=(
                            0
                            if zone.get("exit_condition", "Anlık Fiyat")
                            == "Anlık Fiyat"
                            else 1
                        ),
                        key=f"cond_{zone_id}_{account_id}",
                        help="İğne atmalarda işlem yapılmasın diyorsan Mum Kapanışını seçmelisin.",
                    )
                with cc3:
                    if z_exit_cond == "Mum Kapanışı":
                        tf_opts = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
                        cur_tf = zone.get("exit_timeframe", "M15")
                        z_exit_tf = st.selectbox(
                            "Zaman Dilimi",
                            options=tf_opts,
                            index=tf_opts.index(cur_tf) if cur_tf in tf_opts else 2,
                            key=f"tf_{zone_id}_{account_id}",
                        )
                    else:
                        z_exit_tf = zone.get("exit_timeframe", "M15")

        # 🌟 YENİ: Anlık Değişiklik (Modifiye) Dedektörü
        is_modified = False
        if not orig_zone:
            is_modified = True  # Yeni eklenmiş, henüz kaydedilmemiş bölge
        else:
            if (
                str(z_symbol).upper().strip()
                != str(orig_zone.get("symbol", "")).upper().strip()
                or str(z_order_type) != str(orig_zone.get("order_type", ""))
                or round(float(z_min), 4)
                != round(float(orig_zone.get("min_price", 0.0)), 4)
                or round(float(z_max), 4)
                != round(float(orig_zone.get("max_price", 0.0)), 4)
                or round(float(z_grid), 4)
                != round(float(orig_zone.get("grid_step", 0.0)), 4)
                or round(float(z_lot), 4)
                != round(float(orig_zone.get("lot_size", 0.0)), 4)
                or round(float(z_tp), 4)
                != round(float(orig_zone.get("take_profit", 0.0)), 4)
                or round(float(z_sl), 4)
                != round(float(orig_zone.get("stop_loss", 0.0)), 4)
                or bool(z_breakout) != bool(orig_zone.get("is_breakout", False))
                or round(float(z_pullback), 4)
                != round(float(orig_zone.get("pullback_distance", 0.0)), 4)
                or int(z_levels_below) != int(orig_zone.get("levels_below", 5))
                or int(z_levels_above) != int(orig_zone.get("levels_above", 5))
                or int(z_max_pos) != int(orig_zone.get("max_positions", 10))
                or bool(z_clear) != bool(orig_zone.get("clear_on_exit", True))
                or str(z_clear_scope) != str(orig_zone.get("clear_scope", ""))
                or str(z_exit_cond) != str(orig_zone.get("exit_condition", ""))
                or str(z_exit_tf) != str(orig_zone.get("exit_timeframe", ""))
            ):
                is_modified = True

        # Butonu şimdi placeholder içine basıyoruz (Sadece değişiklik varken renkli olur)
        upd_label = "💾 Güncelle ⚠️" if is_modified else "💾 Güncelle"
        if upd_btn_placeholder.button(
            upd_label,
            key=f"upd_{zone_id}_{account_id}",
            use_container_width=True,
            type="primary" if is_modified else "secondary",
        ):
            st.session_state[f"save_req_{account_id}"] = True

        # 🌟 YENİ: Başlat butonunu placeholder içine basıyoruz (Değişiklik kontrolü ile)
        if start_btn_placeholder.button(
            start_label,
            key=f"start_{zone_id}_{account_id}",
            use_container_width=True,
            type="primary" if current_state == "START" else "secondary",
            help="Bu bölgedeki ağ örme işlemini başlatır ve güncel fiyatı takip eder.",
        ):
            if is_modified:
                confirm_start_with_changes_dialog(account_id, zone_id, idx)
            else:
                _handle_zone_action(account_id, zone_id, idx, "START")
                st.rerun()

        # Başlığı şimdi placeholder içine basıyoruz (Uyarı eklentisi kaldırıldı)
        title_placeholder.markdown(
            f"**🗺️ Bölge {idx + 1}** — "
            f"*{str(z_symbol).upper().strip()} ({z_order_type})* | "
            f"${z_min:.2f} → ${z_max:.2f}",
            unsafe_allow_html=True,
        )

        # Bölgeyi güncel listeye ekle (Silme işlemi Modal içinden tetikleniyor)
        updated_zones.append(
            {
                "id": zone_id,
                "symbol": str(z_symbol).upper().strip() if z_symbol else "USOUSD",
                "order_type": z_order_type,
                "min_price": z_min,
                "max_price": z_max,
                "grid_step": z_grid,
                "lot_size": z_lot,
                "take_profit": z_tp,
                "stop_loss": z_sl,
                "is_breakout": z_breakout,  # 🌟 YENİ EKLENDİ
                "pullback_distance": z_pullback,  # 🌟 YENİ EKLENDİ
                "levels_below": z_levels_below,
                "levels_above": z_levels_above,
                "max_positions": z_max_pos,
                "clear_on_exit": z_clear,
                "clear_scope": z_clear_scope,
                "exit_condition": z_exit_cond,
                "exit_timeframe": z_exit_tf,
            }
        )

    # Hafıza kaybını önlemek için her renderda listeyi eşitle!
    st.session_state[zones_session_key] = updated_zones

    # Robot (model_2.py) arka planda hala IDX kullandığı için ona uygun JSON köprüsü oluşturuyoruz
    backend_states = {}
    for i, z in enumerate(updated_zones):
        backend_states[str(i)] = st.session_state[ui_state_key].get(z["id"], "CLEAR")

    ui_file = get_ui_state_path(account_id)
    with open(ui_file, "w", encoding="utf-8") as f:
        json.dump(backend_states, f)

    # ── Güncelleme Tetikleyicisi (Bölge başlığından gelen sinyali yakalar) ───
    if st.session_state.get(f"save_req_{account_id}", False):
        st.session_state[f"save_req_{account_id}"] = False
        global_order_type = updated_zones[0]["order_type"] if updated_zones else "BUY"
        global_symbol = updated_zones[0]["symbol"] if updated_zones else "USOUSD"

        return {
            "ORDER_TYPE": global_order_type,
            "SYMBOL": global_symbol,
            "LOOP_INTERVAL_SECONDS": loop_interval,
            "ZONES": updated_zones,
        }

    return None
