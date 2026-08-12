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


@st.dialog("🛑 Motor Durdurma Seçimi")
def confirm_stop_motor_dialog(account_id, on_stop_func, on_stop_close_func):
    """
    Ana Motoru Durdurca açılan güvenlik seçim penceresi (Modal).

    🚀 PHASE 4 Kuralı: İşlemler SADECE kullanıcının açık seçimiyle kapatılır.
    1) "Sadece Durdur": Bot kapanır, pozisyonlar ve emirler broker'da KALIR.
    2) "Durdur ve Tümünü Kapat": Bot kapanır, tüm robot pozisyonları kapatılır.
    """
    st.write("Robot motoru kapatılacak. Açık pozisyonlara ne yapılsın?")

    st.info(
        "🟡 **Sadece Durdur**: Pozisyonlar ve bekleyen emirler olduğu gibi korunur.\n\n"
        "🔴 **Durdur ve Tümünü Kapat**: Tüm robot pozisyonları piyasa fiyatından kapatılır.",
        icon="ℹ️",
    )

    col1, col2 = st.columns([1, 1])
    if col1.button("🟡 Sadece Durdur", width="stretch"):
        on_stop_func(account_id)
        st.rerun()
    if col2.button("🔴 Durdur ve Tümünü Kapat", type="primary", width="stretch"):
        on_stop_close_func(account_id)
        st.rerun()
    if st.button("❌ İptal", width="stretch"):
        st.rerun()
