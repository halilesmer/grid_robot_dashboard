# src/components/dialogs.py
import streamlit as st


@st.dialog("⚠️ Bölgeyi Temizle")
def confirm_clear_dialog(on_confirm_func):
    """
    Bölge temizleme işlemi için onay penceresi (Modal).
    SADECE bekleyen emirler (pending orders) silinir, AÇIK POZİSYONLARA DOKUNULMAZ.
    on_confirm_func: 'Evet' butonuna basıldığında çalıştırılacak fonksiyon.
    """
    st.write(
        "Bu bölgedeki bekleyen emirleri silmek istediğinize emin misiniz? "
        "AÇIK POZİSYONLAR KORUNUR. Bu işlem geri alınamaz."
    )

    col_yes, col_no = st.columns([1, 1])
    if col_yes.button("Evet, Temizle", type="primary", width="stretch"):
        on_confirm_func()  # Asıl temizleme işlemini yapan fonksiyonu tetikle
        st.rerun()

    if col_no.button("Hayır, İptal", width="stretch"):
        st.rerun()


@st.dialog("🗑️ Bölgeyi Sil")
def confirm_delete_zone_dialog(zone_name, on_confirm_func):
    """
    Belirli bir bölgeyi silmek için onay penceresi (Modal).
    zone_name: Silinecek bölgenin adı (Ekranda göstermek için).
    on_confirm_func: 'Evet' butonuna basıldığında çalıştırılacak fonksiyon.
    """
    st.write(f"**{zone_name}** adlı bölgeyi silmek istediğinize emin misiniz?")

    col_yes, col_no = st.columns([1, 1])
    if col_yes.button("Evet, Sil", type="primary", width="stretch"):
        on_confirm_func()  # Asıl silme işlemini yapan fonksiyonu tetikle
        st.rerun()

    if col_no.button("Hayır, İptal", width="stretch"):
        st.rerun()


@st.dialog("🗑️ Hesabı Sil")
def confirm_delete_account_dialog(account_name, on_confirm_func):
    """
    Hesap silme işlemi için onay penceresi (Modal).
    """
    st.warning(
        f"⚠️ **{account_name}** adlı hesabı tamamen silmek istediğinize emin misiniz?",
        icon="🗑️",
    )

    col_yes, col_no = st.columns([1, 1])
    if col_yes.button("Evet, Sil", type="primary", width="stretch"):
        on_confirm_func()
        st.rerun()

    if col_no.button("Hayır, İptal", width="stretch"):
        st.rerun()


@st.dialog("🛑 MT5 Bağlantısını Kes")
def confirm_stop_motor_dialog(account_id, on_stop_func):
    """
    MT5 bağlantısını kesmek için onay penceresi (Modal).

    Bot kapanır; AÇIK POZİSYONLARA ASLA DOKUNULMAZ.
    Bekleyen emirler (pending orders) de olduğu gibi korunur.
    """
    st.write("MT5 bağlantısını kesmek istediğinize emin misiniz?")
    st.info(
        "Açık pozisyonlar ve bekleyen emirler broker'da olduğu gibi korunur.",
        icon="ℹ️",
    )

    col1, col2 = st.columns([1, 1])
    if col1.button("🟡 Evet, Bağlantıyı Kes", width="stretch"):
        on_stop_func(account_id)
        cleanup_key = f"bot_started_at_{account_id}"
        if cleanup_key in st.session_state:
            del st.session_state[cleanup_key]
        st.rerun()
    if col2.button("❌ İptal", width="stretch"):
        st.rerun()
