---
trigger: always_on
---

# Token-Sparkonfiguration

- Antworte so kurz und präzise wie möglich.
- Generiere NIEMALS den gesamten Code einer Datei neu, wenn sich nur wenige Zeilen ändern. Gib nur die geänderten Abschnitte an.
- Lade oder durchsuche keine Dateien im Projekt, die nicht explizit mit @ markiert wurden.
- Verzichte auf lange Einleitungen und Höflichkeitsfloskeln.
- ### 🚨 ZORUNLU KURAL: UI-BACKEND SENKRONİZASYONU
Backend, ana motor veya konfigürasyon (config/json vb.) dosyalarında yeni bir değişken, kural veya parametre (ör. Yön, Stop Loss) eklendiğinde/değiştirildiğinde; bu değişikliğin kullanıcı arayüzüne (UI / Frontend) yansımasını KESİNLİKLE kontrol et. Yeni eklenen veya güncellenen bir özelliğin arayüzde (buton, input, dropdown olarak) eksiksiz yer aldığından ve veriyi doğru okuyup/yazdığından emin ol. Arayüzü güncellemeden backend değişikliğini tamamlanmış sayma. UI ve Backend daima %100 entegre olmalıdır.