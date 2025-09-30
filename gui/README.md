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

### 📁 Merkezi Veri Yönetimi

Tüm log ve test verileri merkezi klasörlerde saklanır:

```
lab_instruments/
└── data/
    ├── logs/              # Tüm log dosyaları
    │   └── keithley_log_YYYYMMDD_HHMMSS.csv
    └── test_results/      # Tüm test sonuçları
        ├── pulse_bt_YYYYMMDD_HHMMSS.csv
        ├── rest_evoc_YYYYMMDD_HHMMSS.csv
        ├── battery_model_*.csv
        └── monitoring_*.csv
```

**Avantajları:**
- ✅ Tüm veriler tek merkezde
- ✅ Kolay yedekleme ve arşivleme
- ✅ .gitignore ile otomatik ignore
- ✅ Proje root'u temiz kalır

### Data Logger (data_logger.py)
```python
from utils.data_logger import DataLogger

logger = DataLogger()
# Veriler otomatik olarak ../data/logs/ klasörüne kaydedilir
logger.log_data({
    "timestamp": "2024-01-01 12:00:00",
    "voltage": 3.7,
    "current": 1.0,
    "temperature": 25.0
})
```

### Keithley Logger (keithley_logger.py)
```python
from utils.keithley_logger import KeithleyLogger

logger = KeithleyLogger()
logger.start_timer()

# Log measurements
logger.log_measurement(
    timestamp="2024-01-01 12:00:00",
    voltage=3.7,
    current=1.0,
    mode="battery_test"
)

# Otomatik olarak ../data/logs/ klasörüne kaydedilir
log_path = logger.save_log_csv()
print(f"Log saved to: {log_path}")

# Analysis export otomatik olarak ../data/test_results/ klasörüne kaydedilir
analysis_path = logger.export_for_analysis()
```

### Log Formatları
- **CSV**: Tablo formatında veri
- **JSON**: Structured data
- **LOG**: Text tabanlı loglar

### Dosya Konumları
- **Loglar**: `data/logs/keithley_log_YYYYMMDD_HHMMSS.csv`
- **Test Sonuçları**: `data/test_results/pulse_bt_YYYYMMDD_HHMMSS.csv`
- **Battery Models**: `data/test_results/battery_model_slot*.csv`
- **Monitoring Data**: `data/test_results/monitoring_*.csv`

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

### Veri Klasör Yapısı
```
lab_instruments/
└── data/
    ├── logs/              # Sistem ve cihaz logları
    │   ├── keithley_log_20250930_120000.csv
    │   └── monitoring_20250930_120000.csv
    └── test_results/      # Tüm test sonuçları
        ├── pulse_bt_20250930_152324.csv
        ├── rest_evoc_20250930_152324.csv
        ├── battery_model_slot1_20250930.csv
        └── keithley_analysis_20250930.csv
```

### Örnek Veri Dosyaları
- `data/test_results/pulse_bt_*.csv` - Pulse test verileri
- `data/test_results/rest_evoc_*.csv` - EVOC test verileri
- `data/test_results/battery_model_*.csv` - Battery model exports
- `data/logs/keithley_log_*.csv` - Keithley operation logs

### Veri Formatı
```csv
timestamp,voltage,current,power,temperature
2024-01-01 12:00:00,3.7,1.0,3.7,25.0
2024-01-01 12:00:01,3.65,1.0,3.65,25.1
```

### Veri Erişimi
```python
from pathlib import Path

# Log dosyalarına erişim
log_dir = Path('data/logs')
logs = list(log_dir.glob('*.csv'))

# Test sonuçlarına erişim
results_dir = Path('data/test_results')
results = list(results_dir.glob('*.csv'))
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