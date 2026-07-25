# components/model3_settings.py
import streamlit as st

def render_model_3_settings(current_settings):
    # Session state içinde Model 3 bölgelerini tutalım
    if "model3_zones" not in st.session_state:
        st.session_state.model3_zones = current_settings.get("ZONES", [])

    with st.form("settings_form_m3"):
        st.markdown("###### ⚖️ Temel İşlem Ayarları (Model 3)")
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            symbol = st.text_input("Sembol", value=current_settings.get("SYMBOL", "USOUSD"))
        with t_col2:
            loop_interval = st.number_input("Kontrol Sıklığı (Sn)", value=float(current_settings.get("LOOP_INTERVAL_SECONDS", 1.0)), step=0.1)

        st.markdown("---")
        st.markdown("###### 🎯 Dinamik Bölgeler (Zones)")
        
        updated_zones = []
        for idx, zone in enumerate(st.session_state.model3_zones):
            # Yanmış (Burned) bölge ise başlıkta belirt
            burn_status = " 🔥 (YANDI - PASİF)" if zone.get("is_burned", False) else ""
            
            with st.expander(f"Bölge {idx + 1} Ayarları {burn_status}", expanded=not zone.get("is_burned", False)):
                
                # 1. Sınırlar ve Yön
                c1, c2, c3, c4 = st.columns([1, 1, 1.5, 0.5])
                with c1:
                    z_min = st.number_input(f"Alt Sınır##m3_{idx}", value=float(zone.get("min_price", 0.0)), step=0.1)
                with c2:
                    z_max = st.number_input(f"Üst Sınır##m3_{idx}", value=float(zone.get("max_price", 0.0)), step=0.1)
                with c3:
                    z_dir = st.selectbox(f"İşlem Yönü##m3_{idx}", options=["BOTH", "BUY", "SELL"], index=["BOTH", "BUY", "SELL"].index(zone.get("direction", "BOTH")))
                with c4:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    delete_btn = st.checkbox(f"🗑️ Sil##del_m3_{idx}")

                st.divider()

                # 2. BUY Ayarları
                if z_dir in ["BOTH", "BUY"]:
                    st.markdown("**🟢 BUY (Alış) Stratejisi**")
                    bc1, bc2, bc3, bc4, bc5 = st.columns(5)
                    with bc1:
                        b_grid = st.number_input(f"Grid##buy_{idx}", value=float(zone.get("buy_grid", 0.05)), step=0.01)
                    with bc2:
                        b_lot = st.number_input(f"Lot##buy_{idx}", value=float(zone.get("buy_lot", 0.01)), step=0.01)
                    with bc3:
                        b_tp = st.number_input(f"TP##buy_{idx}", value=float(zone.get("buy_tp", 0.05)), step=0.01)
                    with bc4:
                        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                        b_sl_use = st.checkbox(f"SL Kullan##buy_chk_{idx}", value=bool(zone.get("use_buy_sl", False)))
                    with bc5:
                        b_sl = st.number_input(f"SL Fiyatı##buy_sl_{idx}", value=float(zone.get("buy_sl", 0.0)), step=0.01, disabled=not b_sl_use)
                else:
                    b_grid, b_lot, b_tp, b_sl_use, b_sl = 0.05, 0.01, 0.05, False, 0.0

                # 3. SELL Ayarları
                if z_dir in ["BOTH", "SELL"]:
                    st.markdown("**🔴 SELL (Satış) Stratejisi**")
                    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                    with sc1:
                        s_grid = st.number_input(f"Grid##sell_{idx}", value=float(zone.get("sell_grid", 0.05)), step=0.01)
                    with sc2:
                        s_lot = st.number_input(f"Lot##sell_{idx}", value=float(zone.get("sell_lot", 0.01)), step=0.01)
                    with sc3:
                        s_tp = st.number_input(f"TP##sell_{idx}", value=float(zone.get("sell_tp", 0.05)), step=0.01)
                    with sc4:
                        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                        s_sl_use = st.checkbox(f"SL Kullan##sell_chk_{idx}", value=bool(zone.get("use_sell_sl", False)))
                    with sc5:
                        s_sl = st.number_input(f"SL Fiyatı##sell_sl_{idx}", value=float(zone.get("sell_sl", 0.0)), step=0.01, disabled=not s_sl_use)
                else:
                    s_grid, s_lot, s_tp, s_sl_use, s_sl = 0.05, 0.01, 0.05, False, 0.0

                st.divider()

                # 4. Akıllı Güvenlik Ayarları
                st.markdown("**🛡️ Akıllı Güvenlik (Mum Kapanışı & Bölge İptali)**")
                ac1, ac2, ac3 = st.columns(3)
                with ac1:
                    smart_sl = st.checkbox(f"Mum Kapanışı SL##smart_{idx}", value=bool(zone.get("use_smart_sl", False)))
                with ac2:
                    tf_options = ["M15", "H1", "H4", "D1"]
                    current_tf = zone.get("smart_sl_tf", "H4")
                    tf_idx = tf_options.index(current_tf) if current_tf in tf_options else 2
                    smart_tf = st.selectbox(f"Zaman Dilimi##tf_{idx}", options=tf_options, index=tf_idx, disabled=not smart_sl)
                with ac3:
                    burn_zone = st.checkbox(f"SL Olunca Bölgeyi Yak (İptal Et)##burn_{idx}", value=bool(zone.get("burn_on_sl", True)))

                if not delete_btn:
                    updated_zones.append({
                        "min_price": z_min,
                        "max_price": z_max,
                        "direction": z_dir,
                        "buy_grid": b_grid, "buy_lot": b_lot, "buy_tp": b_tp, "use_buy_sl": b_sl_use, "buy_sl": b_sl,
                        "sell_grid": s_grid, "sell_lot": s_lot, "sell_tp": s_tp, "use_sell_sl": s_sl_use, "sell_sl": s_sl,
                        "use_smart_sl": smart_sl, "smart_sl_tf": smart_tf,
                        "burn_on_sl": burn_zone,
                        "is_burned": zone.get("is_burned", False) 
                    })
        
        st.session_state.model3_zones = updated_zones

        col_b1, col_b2 = st.columns([1, 1])
        
        # KESİN ÇÖZÜM: Streamlit sol kolonu HTML'de ilk gördüğü için 
        # Enter tuşunu daima buraya atar. Bu yüzden Güncelleme butonunu sola alıyoruz.
        with col_b1:
            submitted = st.form_submit_button("💾 Ayarları Güncelle", type="primary")
            
        with col_b2:
            add_zone = st.form_submit_button("➕ Yeni Bölge Ekle")

        if add_zone:
            st.session_state.model3_zones.append({
                "min_price": 90.0,
                "max_price": 100.0,
                "direction": "BOTH",
                "buy_grid": 0.05, "buy_lot": 0.01, "buy_tp": 0.05, "use_buy_sl": False, "buy_sl": 0.0,
                "sell_grid": 0.05, "sell_lot": 0.01, "sell_tp": 0.05, "use_sell_sl": False, "sell_sl": 0.0,
                "use_smart_sl": True, "smart_sl_tf": "H4", "burn_on_sl": True, "is_burned": False
            })
            st.rerun()

        if submitted:
            return {
                "SYMBOL": symbol,
                "LOOP_INTERVAL_SECONDS": loop_interval,
                "ZONES": updated_zones
            }
            
    return None