# 📂 Proje Dosya Yapısı ve Görevleri

> **SİSTEM TALİMATI (YAPAY ZEKA İÇİN):**
> Bu proje üzerinde çalışırken, eğer projeye **yeni bir dosya eklersen**, **yeni bir klasör oluşturursan** veya **mevcut bir dosyanın adını/işlevini köklü şekilde değiştirirsen**, bu değişiklikleri okumakta olduğun bu krokiye de yansıtmalısın. Her yeni dosya veya klasör oluşturma işleminin ardından, bana mutlaka güncellenmiş `proje_dosya_krokisi.md` dosyasının içeriğini de ver. Yeni dosyayı doğru klasör başlığı altına ekle, dosya adını kalın (`**`) yaz ve hemen yanına ne işe yaradığını kısaca açıkla.

Bu belge, `grid_robot_dashboard` projesinin dosya ve klasör hiyerarşisini, ayrıca her bir bileşenin ne işe yaradığını açıklamaktadır. Sisteme veya yapay zekaya bağlam sunmak için bir referans rehberidir.

## Ana Dizin (Root)
*   **`app.py`**: Projenin ana çalıştırma ve giriş (entry point) dosyasıdır.
*   **`requirements.txt`**: Projenin çalışması için kurulması gereken Python bağımlılıklarını ve kütüphanelerini listeler.
*   **`grid_robot_log.txt`**: Sistemin veya bir grid robotunun çalışma zamanı günlüklerini (log) kaydettiği metin dosyasıdır.
*   **`settings_model1.json`, `settings_model2.json`, `settings_model3.json`**: Projedeki farklı çekirdek modellerin (1, 2 ve 3) ayarlarını, parametrelerini ve yapılandırmalarını tutan veri dosyalarıdır.
*   **`proje_dosya_krokisi.md`**: Projenin yapısını ve dosyaların görevlerini açıklayan, yapay zekaya bağlam sağlayan güncel doküman (bu dosya).
*   **`.gitignore` / `.gitattributes`**: Git versiyon kontrol sistemi için hariç tutulacak dosyaları ve depolama kurallarını belirler.

## 📁 Gizli ve Yapılandırma Klasörleri
*   **`.agents/`**: Yapay zeka destekli kodlama araçlarının (asistanların) kurallarını ve yeteneklerini tanımlayan dosyaları (örneğin Streamlit becerileri veya token tasarruf kuralları) barındırır.
*   **`.git/`**: Projenin versiyon kontrol geçmişini ve Git yapılandırmalarını tutar.
*   **`.streamlit/`**: Streamlit arayüz kütüphanesine ait özel yapılandırmaları (`config.toml` gibi) içerir.
*   **`.vscode/`**: Visual Studio Code veya benzeri editörler için çalışma alanı (workspace) ayarlarını (`settings.json`) saklar.

## 📁 `components/` Klasörü
Kullanıcı arayüzünü (UI) oluşturan modüler parçaları barındırır.
*   **`chart_viewer.py`**: Verileri görselleştirmek ve grafikleri göstermek için kullanılan bileşendir.
*   **`controls.py`**: Kullanıcının etkileşime girdiği kontrol elemanlarını (butonlar, kaydırıcılar vb.) içerir.
*   **`header.py`**: Uygulamanın üst bilgi, başlık veya menü kısmını yönetir.
*   **`log_viewer.py`**: Arka planda veya robot tarafından üretilen logları arayüzde göstermeye yarar.
*   **`metrics.py`**: Sistemden gelen verilerin temel metriklerini ve istatistiklerini arayüzde sunar.
*   **`model3_settings.py`**: Özellikle 3. modelin arayüzdeki ayar paneline özgü kontrolleri yönetir.
*   **`settings_panel.py`**: Kullanıcının uygulamanın genel ayarlarını değiştirebildiği paneli oluşturur.
*   **`__init__.py`**: Bu klasörün bir Python modülü olarak tanınmasını sağlar.

## 📁 `core/` Klasörü
Projenin beynidir; ana mantığı, yapay zeka veya işlem modellerini içerir.
*   **`model_1.py`, `model_2.py`, `model_3.py`**: Sistemin temelini oluşturan üç farklı simülasyon, veri işleme veya yapay zeka modelinin tanımlandığı çekirdek dosyalardır.
*   **`__init__.py`**: Klasörü Python modülü yapar.

## 📁 `constants/` Klasörü
Proje genelinde kullanılan sabitleri (değişmeyen verileri) tutar.
*   **`tooltips.py`**: Arayüzdeki bilgilendirme kutucuklarının (ipucu/tooltip) metinlerini içerir.

## 📁 `styles/` Klasörü
Uygulamanın görsel tasarımıyla ilgili dosyaları tutar.
*   **`custom_css.py`**: Projenin arayüzünü özelleştirmek için kullanılan CSS kodlarını Python üzerinden sisteme entegre eder.

## 📁 `utils/` Klasörü
Projede birden çok yerde ihtiyaç duyulan yardımcı araçları barındırır.
*   **`config.py`**: Uygulama yapılandırmalarının okunması, işlenmesi veya yönetilmesi için kullanılan yardımcı fonksiyonları içerir.
