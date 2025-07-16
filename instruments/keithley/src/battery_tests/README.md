# Battery Tests

Bu klasör, batarya performansını test etmek ve yaşlanma analizleri yapmak için geliştirilmiş betikleri içerir.

## 📁 Dosyalar

### Yaşlanma Testleri
- `battery_aging_assessment.py` - Batarya yaşlanma değerlendirmesi
- `keithley_battery_aging_test.py` - Kapsamlı batarya yaşlanma testi

### Performans Testleri
- `long_battery_test.py` - Uzun süreli batarya testi
- `quick_long_battery_test.py` - Hızlı uzun süreli test
- `quick_long_battery_test_V2.py` - V2 hızlı uzun süreli test

### Yardımcı Araçlar
- `battery_test_utility.py` - Batarya test yardımcı fonksiyonları

## 🚀 Kullanım

### Yaşlanma Testi
```bash
python battery_aging_assessment.py
```

### Uzun Süreli Test
```bash
python long_battery_test.py
```

### Hızlı Test
```bash
python quick_long_battery_test_V2.py
```

## 📊 Test Türleri

### 1. Yaşlanma Testleri
- **Kapasite Degradasyonu**: Zaman içinde kapasite kaybı
- **İç Direnç Artışı**: Batarya iç direncinin değişimi
- **Voltaj Profili**: Şarj/deşarj voltaj karakteristikleri

### 2. Performans Testleri
- **Döngü Testi**: Tekrarlı şarj/deşarj döngüleri
- **Sıcaklık Testi**: Farklı sıcaklıklarda performans
- **Akım Kapasitesi**: Farklı akım seviyelerinde kapasite

### 3. Güvenlik Testleri
- **Aşırı Şarj Koruması**: Güvenlik limitlerinin testi
- **Aşırı Deşarj Koruması**: Düşük voltaj koruması
- **Sıcaklık Koruması**: Termal güvenlik testleri

## 📈 Çıktılar

### Veri Dosyaları
- `battery_health_YYYYMMDD_HHMMSS_baseline.csv` - Temel sağlık verileri
- `battery_health_YYYYMMDD_HHMMSS_baseline.json` - Metadata
- `aging_assessment_YYYYMMDD_HHMMSS.log` - Test logları

### Grafikler
- Kapasite vs Zaman
- Voltaj vs Akım
- Sıcaklık vs Performans

## 🔧 Konfigürasyon

### Test Parametreleri
```python
TEST_DURATION = 3600  # saniye
CURRENT_LEVELS = [0.1, 0.5, 1.0, 2.0]  # Amper
VOLTAGE_LIMITS = [3.0, 4.2]  # Volt
TEMPERATURE_RANGE = [25, 45]  # Celsius
```

## 📝 Notlar

- Testler `../../results/` klasörüne kaydedilir
- Log dosyaları `../../logs/` klasöründe tutulur
- V2 versiyonları daha hızlı ve optimize edilmiştir
- Güvenlik limitleri her zaman aktiftir 