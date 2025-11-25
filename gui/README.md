# Lab Instruments GUI

Bu klasör, laboratuvar cihazlarını kontrol etmek için geliştirilmiş modüler GUI uygulamasını içerir.

## 📁 Proje Yapısı

```
gui/
├── main.py                    # Ana uygulama giriş noktası
├── requirements.txt           # Python bağımlılıkları
├── controllers/              # Cihaz kontrol sınıfları
│   ├── base_controller.py    # Temel kontrol sınıfı
│   ├── keithley_controller.py # Keithley cihaz kontrolü
│   ├── prodigit_controller.py # Prodigit cihaz kontrolü
│   └── sorensen_controller.py # Sorensen cihaz kontrolü
├── gui/                      # GUI bileşenleri
│   ├── main_window.py        # Ana pencere
│   ├── connection_widget.py  # Bağlantı widget'ı
│   ├── device_tab.py         # Genel cihaz sekmesi
│   ├── keithley_tab.py       # Keithley sekmesi
│   ├── prodigit_tab.py       # Prodigit sekmesi
│   ├── sorensen_tab.py       # Sorensen sekmesi
│   └── monitoring_tab.py     # Monitoring sekmesi
├── interfaces/               # İletişim arayüzleri
│   ├── base_interface.py     # Temel arayüz
│   ├── ethernet_interface.py # Ethernet iletişimi
│   ├── serial_interface.py   # Seri port iletişimi
│   └── visa_interface.py     # VISA iletişimi
├── models/                   # Veri modelleri
│   └── device_config.py      # Cihaz konfigürasyonu
├── utils/                    # Yardımcı araçlar
│   ├── data_logger.py        # Veri loglama
│   └── keithley_logger.py    # Keithley özel loglama
├── tests/                    # Test betikleri
│   ├── test_structure.py     # Yapı testi
│   ├── test_monitoring_fix.py # Monitoring testi
│   └── test_pulse_simple.py  # Pulse test
├── docs/                     # Dokümantasyon
│   ├── MONITORING_FIX_SUMMARY.md
│   ├── PULSE_TEST_FIXES.md
│   └── STRUCTURE_SUMMARY.md
└── battery_models/           # Batarya modelleri
```

## 🚀 Kurulum ve Başlatma

### Gereksinimler
```bash
pip install -r requirements.txt
```

### Uygulamayı Başlatma
```bash
python main.py
```

## 🔧 Desteklenen Cihazlar

### Keithley Cihazları
- **Model**: 2281S, 2260B serisi
- **Özellikler**: Güç kaynağı, akım/voltaj ölçümü, batarya simülasyonu
- **İletişim**: VISA (USB, Ethernet, Serial)

### Prodigit Cihazları
- **Model**: 3311F, 3312F serisi
- **Özellikler**: Elektronik yük, güç analizi
- **İletişim**: VISA, Modbus

## Prodigit CC CSV Profilleri

- CSV formatı `time_s,current_a` sütunlarını kullanır. `time_s` segment başlangıç zamanı, `current_a` ise CC set noktasıdır.
- Prodigit kontrolleri `STAT:MODE CC`, `CURR:HIGH`, `STAT:LOAD ON/OFF` komut setiyle yürütülür (bkz. `docs/90034000A5_34000A series Operation Manual-rD.pdf`).
- Guardrail'ler:
  - Minimum segment süresi: **1 saniye**
  - Maksimum toplam süre: **3600 saniye** (~1 saat)
  - Sürekli akım limiti: **120 A** (cihazın 160 A nominal limitinin altında güvenli aralık)
- GUI üzerinden çalışma:
  1. Prodigit tab'ında bağlanın.
  2. "CSV CC Profile" bölümünden dosya seçin ve **Load Profile** ile özet bilgileri kontrol edin.
  3. Örnekleme periyodunu (varsayılan 1 s) belirleyip **Start** ile başlatın, **Stop** ile iptal edin.
  4. Her saniye ölçümler `logs/prodigit_cc_*.csv` dosyalarına kaydedilir.
- Donanım olmadan doğrulama için CLI/helper:

```bash
python gui/tests/test_prod_digit_profile.py your_profile.csv --sample-period 0.5
```

Bu komut mock bir kontrolcüyle profili simüle eder ve aynı log dosyasını üretir.

### Sorensen Cihazları
- **Model**: XG serisi
- **Özellikler**: Programlanabilir güç kaynağı
- **İletişim**: VISA, Serial

## 🖥️ GUI Bileşenleri

### Ana Pencere (main_window.py)
- Tabbed interface
- Menü çubuğu
- Durum çubuğu
- Toolbar

### Bağlantı Widget'ı (connection_widget.py)
- Cihaz keşfi
- Bağlantı yönetimi
- Durum gösterimi
- Otomatik yeniden bağlantı

### Cihaz Sekmeleri
- **Keithley Tab**: Güç kaynağı kontrolü, batarya testleri
- **Prodigit Tab**: Elektronik yük kontrolü
- **Sorensen Tab**: Programlanabilir güç kaynağı
- **Monitoring Tab**: Real-time veri izleme

## 📊 Özellikler

### Real-time Monitoring
- Canlı veri görüntüleme
- Grafik çizimi
- Alarm sistemi
- Veri loglama

### Batarya Testleri
- Şarj/deşarj döngüleri
- Kapasite testleri
- İç direnç ölçümü
- Yaşlanma analizi

### Pulse Testleri
- Dinamik pulse oluşturma
- Transient analiz
- Frekans analizi
- EVOC testleri

### Veri Yönetimi
- Otomatik veri kaydetme
- CSV/JSON export
- Grafik export
- Test raporları

## 🔌 İletişim Arayüzleri

### VISA Interface (visa_interface.py)
```python
from interfaces.visa_interface import VISAInterface

# VISA bağlantısı
interface = VISAInterface("TCPIP::192.168.1.100::INSTR")
interface.connect()
response = interface.query("*IDN?")
```

### Ethernet Interface (ethernet_interface.py)
```python
from interfaces.ethernet_interface import EthernetInterface

# Ethernet bağlantısı
interface = EthernetInterface("192.168.1.100", 5025)
interface.connect()
data = interface.send_command("MEAS:VOLT?")
```

### Serial Interface (serial_interface.py)
```python
from interfaces.serial_interface import SerialInterface

# Serial bağlantısı
interface = SerialInterface("/dev/ttyUSB0", 9600)
interface.connect()
response = interface.read_data()
```

## 🎛️ Kontrol Sınıfları

### Base Controller (base_controller.py)
Tüm cihaz kontrolcüleri için temel sınıf:
```python
class BaseController:
    def connect(self):
        pass
    
    def disconnect(self):
        pass
    
    def get_status(self):
        pass
```

### Keithley Controller (keithley_controller.py)
```python
from controllers.keithley_controller import KeithleyController

controller = KeithleyController()
controller.connect("TCPIP::192.168.1.100::INSTR")
controller.set_voltage(3.7)
controller.set_current(1.0)
voltage = controller.measure_voltage()
```

## 📈 Veri Loglama

### Data Logger (data_logger.py)
```python
from utils.data_logger import DataLogger

logger = DataLogger("test_data.csv")
logger.log_data({
    "timestamp": "2024-01-01 12:00:00",
    "voltage": 3.7,
    "current": 1.0,
    "temperature": 25.0
})
```

### Log Formatları
- **CSV**: Tablo formatında veri
- **JSON**: Structured data
- **LOG**: Text tabanlı loglar

## 🔧 Konfigürasyon

### Device Config (device_config.py)
```python
{
    "keithley": {
        "address": "TCPIP::192.168.1.100::INSTR",
        "timeout": 5000,
        "voltage_limit": 5.0,
        "current_limit": 3.0
    },
    "prodigit": {
        "address": "TCPIP::192.168.1.101::INSTR",
        "mode": "CC",
        "power_limit": 150.0
    }
}
```

## 🛠️ Geliştirme

### Yeni Cihaz Ekleme
1. `controllers/` klasörüne yeni controller ekleyin
2. `gui/` klasörüne yeni tab ekleyin
3. `interfaces/` klasörüne gerekli interface'i ekleyin
4. `main_window.py`'da yeni tab'ı kaydedin

### Yeni Test Ekleme
1. Test sınıfını oluşturun
2. GUI bileşenlerini ekleyin
3. Veri loglama ekleyin
4. Dokümantasyon güncelleyin

## 🐛 Hata Ayıklama

### Log Dosyaları
- `pulse_debug.log` - Pulse test hataları
- `monitoring.log` - Monitoring sistem logları
- `connection.log` - Bağlantı hataları

### Test Betikleri
- `tests/test_structure.py` - Yapı testi
- `tests/test_monitoring_fix.py` - Monitoring testi
- `tests/test_pulse_simple.py` - Pulse test

### Yaygın Sorunlar
1. **Cihaz Bağlantısı**: VISA sürücülerini kontrol edin
2. **GUI Donması**: Thread kullanımını kontrol edin
3. **Veri Kaybı**: Buffer boyutunu artırın

## 📋 Test Verileri

### Örnek Veri Dosyaları
- `pulse_bt_20250627_152324.csv` - Pulse test verileri
- `rest_evoc_20250627_152324.csv` - EVOC test verileri

### Veri Formatı
```csv
timestamp,voltage,current,power,temperature
2024-01-01 12:00:00,3.7,1.0,3.7,25.0
2024-01-01 12:00:01,3.65,1.0,3.65,25.1
```

## 📚 Dokümantasyon

### Mevcut Dokümantasyon
- `docs/MONITORING_FIX_SUMMARY.md` - Monitoring düzeltmeleri
- `docs/PULSE_TEST_FIXES.md` - Pulse test düzeltmeleri
- `docs/STRUCTURE_SUMMARY.md` - Yapı özeti

## 🔐 Güvenlik

### Güvenlik Önlemleri
- Cihaz limitleri kontrolü
- Kullanıcı yetkilendirmesi
- Veri şifreleme
- Güvenli bağlantı

### Güvenlik Limitleri
```python
SAFETY_LIMITS = {
    "max_voltage": 5.0,
    "max_current": 3.0,
    "max_power": 15.0,
    "max_temperature": 60.0
}
```

## 🚀 Performans

### Optimizasyon
- Asenkron işlemler
- Veri buffering
- GUI thread separation
- Memory management

### Performans Metrikleri
- Response time: <100ms
- Data rate: 1000 samples/sec
- Memory usage: <500MB
- CPU usage: <30%

## 📝 Notlar

- GUI PyQt5/PySide2 tabanlıdır
- Thread-safe veri işleme
- Modüler tasarım
- Kolay genişletilebilir
- Cross-platform uyumlu

---

**Geliştirici**: Lab Instruments Team
**Son Güncelleme**: 2025-07-16