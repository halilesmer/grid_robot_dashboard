# src/components/dialogs.py
import streamlit as st


@st.dialog("⚠️ Tümünü Temizle")
def confirm_clear_dialog(on_confirm_func):
    """
    Tümünü temizleme işlemi için onay penceresi (Modal).
    on_confirm_func: 'Evet' butonuna basıldığında çalıştırılacak fonksiyon.
    """
    st.write(
        "Tüm kayıtları/verileri temizlemek istediğinize emin misiniz? Bu işlem geri alınamaz."
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
