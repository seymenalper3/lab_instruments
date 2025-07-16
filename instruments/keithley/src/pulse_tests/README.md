# Pulse Tests

Bu klasör, pulse karakterizasyon testleri ve dinamik pulse analizleri için geliştirilmiş betikleri içerir.

## 📁 Dosyalar

### Demo Pulse Testleri
- `demo_pulse_test_60s.py` - 60 saniye demo pulse testi
- `demo_pulse_softrest_60s.py` - Soft reset ile 60s pulse testi
- `demo_pulse_trace_60s.py` - Trace özellikli 60s pulse testi

### Dinamik Pulse Testleri
- `dynamic_pulse_test.py` - Dinamik pulse testi
- `dynamic_pulse_test_V2.py` - V2 dinamik pulse testi

### Gelişmiş Pulse Testleri
- `pulse_test_v2.py` - V2 pulse testi
- `pulse_evoc_60s(last).py` - 60s pulse EVOC testi

## 🚀 Kullanım

### Basit Demo Test
```bash
python demo_pulse_test_60s.py
```

### Dinamik Test
```bash
python dynamic_pulse_test_V2.py
```

### Gelişmiş Test
```bash
python pulse_evoc_60s(last).py
```

## 📊 Test Türleri

### 1. Pulse Karakterizasyon
- **Pulse Genliği**: Farklı akım seviyelerinde pulse
- **Pulse Süresi**: Değişken pulse süreleri
- **Pulse Frekansı**: Farklı tekrarlama oranları
- **Duty Cycle**: Pulse açık/kapalı oranları

### 2. Dinamik Analiz
- **Transient Response**: Geçici hal tepkisi
- **Settling Time**: Yerleşme süresi
- **Overshoot/Undershoot**: Aşım/eksik kalma
- **Rise/Fall Time**: Yükselme/düşme süreleri

### 3. EVOC Testleri
- **Electronic Variable Output Control**: Elektronik değişken çıkış kontrolü
- **Feedback Control**: Geri besleme kontrolü
- **Stability Analysis**: Kararlılık analizi

## 📈 Ölçüm Parametreleri

### Elektriksel Parametreler
```python
PULSE_CURRENT = [0.1, 0.5, 1.0, 2.0]  # Amper
PULSE_DURATION = [1, 5, 10, 30]  # saniye
PULSE_FREQUENCY = [0.1, 1, 10]  # Hz
VOLTAGE_RANGE = [0, 5]  # Volt
```

### Timing Parametreleri
```python
SAMPLE_RATE = 1000  # Hz
MEASUREMENT_TIME = 60  # saniye
SETTLING_TIME = 0.1  # saniye
DELAY_TIME = 0.01  # saniye
```

## 📋 Çıktılar

### Veri Dosyaları
- `pulse_bt_YYYYMMDD_HHMMSS.csv` - Pulse test verileri
- `rest_evoc_YYYYMMDD_HHMMSS.csv` - EVOC rest verileri
- `merged_pulse_evoc_YYYYMMDD_HHMMSS.csv` - Birleştirilmiş veriler

### Grafikler
- Pulse vs Zaman
- Voltaj Tepkisi
- Frekans Analizi
- Transient Analiz

## 🔧 Test Konfigürasyonu

### Güvenlik Ayarları
```python
MAX_CURRENT = 3.0  # Amper
MAX_VOLTAGE = 5.0  # Volt
MAX_POWER = 15.0  # Watt
TEMPERATURE_LIMIT = 60  # Celsius
```

### Ölçüm Ayarları
```python
NPLC = 1  # Number of Power Line Cycles
APERTURE_TIME = 0.02  # saniye
FILTER_ENABLE = True
AUTO_RANGE = True
```

## 📝 Notlar

- Pulse testleri yüksek hassasiyet gerektirir
- Sonuçlar `../../results/` klasörüne kaydedilir
- Demo versiyonları eğitim amaçlıdır
- V2 versiyonları geliştirilmiş algoritmalara sahiptir
- EVOC testleri gelişmiş kontrol sistemi gerektirir 