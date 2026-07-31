```python
content = """# 🤖 Algoritmik Ticaret Botu (Grid Robot) Sistem Dokümantasyonu

Gönderilen log dökümlerine ve referans alınan `docs/proje_dosya_krokisi.md` dosyasına dayanarak oluşturulan proje mimarisi ve dosya yapısı aşağıda sunulmuştur. Bu sistem, MetaTrader 5 (MT5) entegrasyonuna sahip bir **Algoritmik Ticaret (Algorithmic Trading) Botu** ve bu botun yönetimini sağlayan bir **Streamlit** web arayüzünden oluşmaktadır.

---

## 📂 Proje Klasör Şablonu (Kroki)

```text
📦 PROJE_KOK_DIZINI
┣ 📜 app.py                     # Uygulamanın (Streamlit) ana giriş noktası
┣ 📜 requirements.txt           # Python bağımlılıkları
┃
┣ 📂 src                        # Kaynak kodların bulunduğu ana dizin
┃ ┣ 📂 components               # Arayüz (UI) bileşenleri
┃ ┃ ┣ 📜 account_selector.py    # Hesap seçim ekranı
┃ ┃ ┣ 📜 chart_viewer.py        # Grafik ve veri görselleştirme
┃ ┃ ┣ 📜 controls.py            # Başlat/Durdur gibi kontrol butonları
┃ ┃ ┣ 📜 header.py              # Üst bilgi alanı
┃ ┃ ┣ 📜 log_viewer.py          # Arayüzde logların gösterimi
┃ ┃ ┣ 📜 metrics.py             # Kâr/Zarar gibi metriklerin gösterimi
┃ ┃ ┣ 📜 model3_settings.py     # Model 3'e özel arayüz ayarları
┃ ┃ ┗ 📜 settings_panel.py      # Genel ayar paneli
┃ ┃
┃ ┣ 📂 core                     # Çekirdek algoritma ve ticaret mantığı
┃ ┃ ┣ 📜 bot_runner.py          # Botu çalıştıran ana motor
┃ ┃ ┣ 📜 model_1.py             # Ticaret stratejisi / Modeli 1
┃ ┃ ┣ 📜 model_2.py             # Ticaret stratejisi / Modeli 2
┃ ┃ ┗ 📜 model_3.py             # Ticaret stratejisi / Modeli 3
┃ ┃
┃ ┣ 📂 utils                    # Yardımcı araçlar ve bağlantılar
┃ ┃ ┣ 📜 bot_manager.py         # Botların yaşam döngüsünü yöneten araç
┃ ┃ ┣ 📜 config.py              # Ayar dosyalarını (JSON) okuma/yazma işlemleri
┃ ┃ ┣ 📜 mt5_connection.py      # MetaTrader 5 (MT5) borsa/broker bağlantısı
┃ ┃ ┗ 📜 trade_utils.py         # Alım-satım ve hesaplama yardımcı fonksiyonları
┃ ┃
┃ ┣ 📂 constants                # Sabit değerler
┃ ┃ ┗ 📜 tooltips.py            # Arayüzdeki bilgilendirme/ipucu metinleri
┃ ┃
┃ ┗ 📂 styles                   # Arayüz tasarımları
┃   ┗ 📜 custom_css.py          # Streamlit arayüzünü özelleştiren CSS kodları
┃
┣ 📂 configs                    # Konfigürasyon dosyaları (JSON)
┃ ┣ 📜 accounts.json            # Borsa hesap bilgileri/kimlik bilgileri
┃ ┗ 📜 settings_*.json          # Modeller için parametre ve ayar kayıtları
┃
┣ 📂 logs                       # Sistem kayıtları
┃ ┣ 📜 grid_robot_log.txt       # Genel bot logları
┃ ┗ 📜 grid_robot_m3_log.txt    # Model 3'e özel loglar
┃
┗ 📂 docs                       # Dokümantasyon
  ┣ 📜 proje_dosya_krokisi.md   # Proje genel yapısı (Ana rehber dosya)
  ┣ 📜 my_notes.md              # Geliştirici notları
  ┗ 📂 architecture             # Modellere ait teknik mimari belgeleri

```

---

## ⚙️ Dosyaların İşlevleri ve Etkileşim Yapısı

Sistem, **Önyüz (Frontend - Streamlit)** ve **Arkayüz (Backend - Ticaret Mantığı)** olmak üzere modüler bir mimariyle tasarlanmıştır.

### 1. Arayüz Katmanı (Girdi ve Görüntüleme)

* **`app.py`:** Sistemin giriş noktasıdır. Kullanıcı arayüzü başlattığında bu dosya çalışır ve `src/components/` altındaki UI modüllerini birleştirerek ekranı oluşturur.
* **`src/components/`:** Uygulamanın görsel öğeleridir.
* `header.py` üst bilgi alanını çizer.
* `account_selector.py` borsa/hesap seçimini sağlar.
* `controls.py` işlemleri başlatıp durduran tetikleyicileri barındırır. Bu bileşenler üzerinden alınan girdiler işlenmek üzere **Core** ve **Utils** katmanlarına gönderilir.



### 2. Çekirdek İş Katmanı (Beyin)

* **`src/core/bot_runner.py`:** Arayüzden başlatma komutu geldiğinde devreye giren ana motordur. Seçilen ticaret modelinin yüklenmesinden ve çalıştırılmasından sorumludur.
* **`src/core/model_*.py`:** Algoritmik ticaret stratejilerini barındıran asıl dosyalardır. Fiyat verilerini analiz ederek piyasaya giriş (alım) veya çıkış (satış) kararlarını verirler.

### 3. Bağlantı ve Araçlar Katmanı (Operasyonel)

* **`src/utils/mt5_connection.py`:** Modellerin dış dünyayla, yani MetaTrader 5 terminaliyle iletişimini sağlar. Anlık piyasa verilerini alır ve modelin ürettiği işlem emirlerini (AL/SAT) terminale iletir.
* **`src/utils/trade_utils.py`:** İşlem boyutlandırması, Stop-Loss (Zarar Durdur) ve Take-Profit (Kâr Al) gibi kritik finansal/matematiksel hesaplamaları yapan yardımcı kütüphanedir.
* **`src/utils/config.py`:** Sistemin çalışması için gerekli olan `configs/` altındaki JSON yapılandırma dosyalarını okur, yorumlar ve diğer modüllerin kullanımına sunar.

### 4. Sistem Veri Akışı ve Çalışma Senaryosu

1. Sistem `app.py` üzerinden ayağa kalktığında, `config.py` çalışarak `configs/` içindeki ayarları (ör. `accounts.json`) okur ve arayüze yükler.
2. Kullanıcı `account_selector.py` ile bir ticaret hesabı seçer ve parametreleri belirleyerek `controls.py` üzerinden botu başlatır.
3. Alınan başlatma emri, **`src/utils/bot_manager.py`** vasıtasıyla **`src/core/bot_runner.py`** modülüne iletilir.
4. `bot_runner.py`, kullanıcının seçtiği ticaret stratejisini (`model_1`, `model_2` veya `model_3`) bellek üzerinde aktif hale getirir.
5. Çalışan model, **`mt5_connection.py`** aracılığıyla MT5 platformuna bağlanarak anlık piyasa fiyatlarını çekmeye başlar.
6. Algoritma bir işlem fırsatı tespit ettiğinde, işlem detayları **`trade_utils.py`** üzerinden hesaplanır ve **`mt5_connection.py`** üzerinden emir olarak piyasaya iletilir.
7. İşlemin her aşamasındaki durum, başarı/hata sonuçları ve metrikler **`logs/`** dizinine metin olarak kaydedilir. Bu veriler eş zamanlı olarak **`log_viewer.py`**, **`chart_viewer.py`** ve **`metrics.py`** üzerinden görsel bir şekilde kullanıcıya sunulur.
"""

with open("proje_dokumantasyonu.md", "w", encoding="utf-8") as f:
f.write(content)

```

Dosyayı indirmekte sorun yaşıyorsan, bağlantıyı senin için tazeledim:
[file-tag: code-generated-file-62f74677-fc2a-4632-841a-82dd260dd3de]

**Eğer yine sistem üzerinden indiremezsen,** hiç dert etme! Aşağıdaki kutudaki metnin tamamını kopyalayıp bilgisayarında `proje_dokumantasyonu.md` adında bir dosya oluşturarak doğrudan içine yapıştırabilirsin:

```markdown
# 🤖 Algoritmik Ticaret Botu (Grid Robot) Sistem Dokümantasyonu

Gönderilen log dökümlerine ve referans alınan `docs/proje_dosya_krokisi.md` dosyasına dayanarak oluşturulan proje mimarisi ve dosya yapısı aşağıda sunulmuştur. Bu sistem, MetaTrader 5 (MT5) entegrasyonuna sahip bir **Algoritmik Ticaret (Algorithmic Trading) Botu** ve bu botun yönetimini sağlayan bir **Streamlit** web arayüzünden oluşmaktadır.

---

## 📂 Proje Klasör Şablonu (Kroki)

📦 PROJE_KOK_DIZINI
┣ 📜 app.py                     # Uygulamanın (Streamlit) ana giriş noktası
┣ 📜 requirements.txt           # Python bağımlılıkları
┃
┣ 📂 src                        # Kaynak kodların bulunduğu ana dizin
┃ ┣ 📂 components               # Arayüz (UI) bileşenleri
┃ ┃ ┣ 📜 account_selector.py    # Hesap seçim ekranı
┃ ┃ ┣ 📜 chart_viewer.py        # Grafik ve veri görselleştirme
┃ ┃ ┣ 📜 controls.py            # Başlat/Durdur gibi kontrol butonları
┃ ┃ ┣ 📜 header.py              # Üst bilgi alanı
┃ ┃ ┣ 📜 log_viewer.py          # Arayüzde logların gösterimi
┃ ┃ ┣ 📜 metrics.py             # Kâr/Zarar gibi metriklerin gösterimi
┃ ┃ ┣ 📜 model3_settings.py     # Model 3'e özel arayüz ayarları
┃ ┃ ┗ 📜 settings_panel.py      # Genel ayar paneli
┃ ┃
┃ ┣ 📂 core                     # Çekirdek algoritma ve ticaret mantığı
┃ ┃ ┣ 📜 bot_runner.py          # Botu çalıştıran ana motor
┃ ┃ ┣ 📜 model_1.py             # Ticaret stratejisi / Modeli 1
┃ ┃ ┣ 📜 model_2.py             # Ticaret stratejisi / Modeli 2
┃ ┃ ┗ 📜 model_3.py             # Ticaret stratejisi / Modeli 3
┃ ┃
┃ ┣ 📂 utils                    # Yardımcı araçlar ve bağlantılar
┃ ┃ ┣ 📜 bot_manager.py         # Botların yaşam döngüsünü yöneten araç
┃ ┃ ┣ 📜 config.py              # Ayar dosyalarını (JSON) okuma/yazma işlemleri
┃ ┃ ┣ 📜 mt5_connection.py      # MetaTrader 5 (MT5) borsa/broker bağlantısı
┃ ┃ ┗ 📜 trade_utils.py         # Alım-satım ve hesaplama yardımcı fonksiyonları
┃ ┃
┃ ┣ 📂 constants                # Sabit değerler
┃ ┃ ┗ 📜 tooltips.py            # Arayüzdeki bilgilendirme/ipucu metinleri
┃ ┃
┃ ┗ 📂 styles                   # Arayüz tasarımları
┃   ┗ 📜 custom_css.py          # Streamlit arayüzünü özelleştiren CSS kodları
┃
┣ 📂 configs                    # Konfigürasyon dosyaları (JSON)
┃ ┣ 📜 accounts.json            # Borsa hesap bilgileri/kimlik bilgileri
┃ ┗ 📜 settings_*.json          # Modeller için parametre ve ayar kayıtları
┃
┣ 📂 logs                       # Sistem kayıtları
┃ ┣ 📜 grid_robot_log.txt       # Genel bot logları
┃ ┗ 📜 grid_robot_m3_log.txt    # Model 3'e özel loglar
┃
┗ 📂 docs                       # Dokümantasyon
  ┣ 📜 proje_dosya_krokisi.md   # Proje genel yapısı (Ana rehber dosya)
  ┣ 📜 my_notes.md              # Geliştirici notları
  ┗ 📂 architecture             # Modellere ait teknik mimari belgeleri


---

## ⚙️ Dosyaların İşlevleri ve Etkileşim Yapısı

Sistem, **Önyüz (Frontend - Streamlit)** ve **Arkayüz (Backend - Ticaret Mantığı)** olmak üzere modüler bir mimariyle tasarlanmıştır.

### 1. Arayüz Katmanı (Girdi ve Görüntüleme)
*   **`app.py`:** Sistemin giriş noktasıdır. Kullanıcı arayüzü başlattığında bu dosya çalışır ve `src/components/` altındaki UI modüllerini birleştirerek ekranı oluşturur.
*   **`src/components/`:** Uygulamanın görsel öğeleridir. 
    *   `header.py` üst bilgi alanını çizer.
    *   `account_selector.py` borsa/hesap seçimini sağlar.
    *   `controls.py` işlemleri başlatıp durduran tetikleyicileri barındırır. Bu bileşenler üzerinden alınan girdiler işlenmek üzere **Core** ve **Utils** katmanlarına gönderilir.

### 2. Çekirdek İş Katmanı (Beyin)
*   **`src/core/bot_runner.py`:** Arayüzden başlatma komutu geldiğinde devreye giren ana motordur. Seçilen ticaret modelinin yüklenmesinden ve çalıştırılmasından sorumludur.
*   **`src/core/model_*.py`:** Algoritmik ticaret stratejilerini barındıran asıl dosyalardır. Fiyat verilerini analiz ederek piyasaya giriş (alım) veya çıkış (satış) kararlarını verirler.

### 3. Bağlantı ve Araçlar Katmanı (Operasyonel)
*   **`src/utils/mt5_connection.py`:** Modellerin dış dünyayla, yani MetaTrader 5 terminaliyle iletişimini sağlar. Anlık piyasa verilerini alır ve modelin ürettiği işlem emirlerini (AL/SAT) terminale iletir.
*   **`src/utils/trade_utils.py`:** İşlem boyutlandırması, Stop-Loss (Zarar Durdur) ve Take-Profit (Kâr Al) gibi kritik finansal/matematiksel hesaplamaları yapan yardımcı kütüphanedir.
*   **`src/utils/config.py`:** Sistemin çalışması için gerekli olan `configs/` altındaki JSON yapılandırma dosyalarını okur, yorumlar ve diğer modüllerin kullanımına sunar.

### 4. Sistem Veri Akışı ve Çalışma Senaryosu
1. Sistem `app.py` üzerinden ayağa kalktığında, `config.py` çalışarak `configs/` içindeki ayarları (ör. `accounts.json`) okur ve arayüze yükler.
2. Kullanıcı `account_selector.py` ile bir ticaret hesabı seçer ve parametreleri belirleyerek `controls.py` üzerinden botu başlatır.
3. Alınan başlatma emri, **`src/utils/bot_manager.py`** vasıtasıyla **`src/core/bot_runner.py`** modülüne iletilir.
4. `bot_runner.py`, kullanıcının seçtiği ticaret stratejisini (`model_1`, `model_2` veya `model_3`) bellek üzerinde aktif hale getirir.
5. Çalışan model, **`mt5_connection.py`** aracılığıyla MT5 platformuna bağlanarak anlık piyasa fiyatlarını çekmeye başlar.
6. Algoritma bir işlem fırsatı tespit ettiğinde, işlem detayları **`trade_utils.py`** üzerinden hesaplanır ve **`mt5_connection.py`** üzerinden emir olarak piyasaya iletilir.
7. İşlemin her aşamasındaki durum, başarı/hata sonuçları ve metrikler **`logs/`** dizinine metin olarak kaydedilir. Bu veriler eş zamanlı olarak **`log_viewer.py`**, **`chart_viewer.py`** ve **`metrics.py`** üzerinden görsel bir şekilde kullanıcıya sunulur.

```