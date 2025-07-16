# Controllers

Bu klasör, farklı laboratuvar cihazlarını kontrol etmek için geliştirilmiş kontrol sınıflarını içerir.

## 📁 Dosyalar

### Temel Sınıf
- `base_controller.py` - Tüm cihaz kontrolcüleri için temel sınıf

### Cihaz Kontrolcüleri
- `keithley_controller.py` - Keithley 2281S ve benzeri cihazlar
- `prodigit_controller.py` - Prodigit 3311F/3312F elektronik yük
- `sorensen_controller.py` - Sorensen XG serisi güç kaynağı

## 🚀 Kullanım

### Temel Kullanım
```python
from controllers.keithley_controller import KeithleyController

# Controller oluştur
controller = KeithleyController()

# Cihaza bağlan
controller.connect("TCPIP::192.168.1.100::INSTR")

# Temel işlemler
controller.set_voltage(3.7)
controller.set_current(1.0)
voltage = controller.measure_voltage()
current = controller.measure_current()

# Bağlantıyı kapat
controller.disconnect()
```

## 🔧 Sınıf Yapısı

### BaseController
Tüm cihaz kontrolcüleri için ortak interface:
```python
class BaseController:
    def connect(self, address):
        """Cihaza bağlan"""
        pass
    
    def disconnect(self):
        """Bağlantıyı kapat"""
        pass
    
    def get_status(self):
        """Cihaz durumunu al"""
        pass
    
    def reset(self):
        """Cihazı sıfırla"""
        pass
```

### KeithleyController
Keithley cihazları için özel fonksiyonlar:
```python
# Güç kaynağı kontrolü
controller.set_voltage(3.7)
controller.set_current(1.0)
controller.enable_output(True)

# Ölçüm fonksiyonları
voltage = controller.measure_voltage()
current = controller.measure_current()
power = controller.measure_power()

# Batarya simülasyonu
controller.load_battery_model("battery_model.csv")
controller.start_battery_simulation()
```

### ProdigitController
Prodigit elektronik yük kontrolü:
```python
# Yük modu ayarları
controller.set_mode("CC")  # Constant Current
controller.set_current_level(2.0)
controller.set_voltage_limit(5.0)

# Ölçümler
voltage = controller.measure_voltage()
current = controller.measure_current()
power = controller.measure_power()
```

### SorensenController
Sorensen güç kaynağı kontrolü:
```python
# Çıkış ayarları
controller.set_voltage(12.0)
controller.set_current_limit(5.0)
controller.enable_output(True)

# Koruma ayarları
controller.set_ovp(13.0)  # Over Voltage Protection
controller.set_ocp(6.0)   # Over Current Protection
```

## 📊 Özellikler

### Ortak Özellikler
- **Otomatik Bağlantı**: Cihaz keşfi ve bağlantı
- **Hata Yönetimi**: Kapsamlı hata yakalama
- **Thread Safety**: Çoklu thread desteği
- **Logging**: Detaylı işlem logları

### Güvenlik Özellikleri
- **Limit Kontrolü**: Güvenlik limitlerinin kontrolü
- **Acil Durdurma**: Hızlı güvenlik durdurma
- **Durum Takibi**: Sürekli durum monitoring
- **Hata Kurtarma**: Otomatik hata kurtarma

## 🛠️ Geliştirme

### Yeni Controller Ekleme
1. `BaseController`'dan türetin
2. Cihaza özel fonksiyonları implement edin
3. Hata yönetimi ekleyin
4. Test kodları yazın

### Örnek Yeni Controller
```python
from controllers.base_controller import BaseController

class NewDeviceController(BaseController):
    def __init__(self):
        super().__init__()
        self.device_type = "NewDevice"
    
    def connect(self, address):
        # Cihaza özel bağlantı kodu
        pass
    
    def custom_function(self):
        # Cihaza özel fonksiyon
        pass
```

## 📋 Hata Kodları

### Yaygın Hatalar
- `CONNECTION_ERROR`: Bağlantı hatası
- `TIMEOUT_ERROR`: Zaman aşımı
- `COMMAND_ERROR`: Komut hatası
- `LIMIT_ERROR`: Güvenlik limiti aşımı

### Hata Yönetimi
```python
try:
    controller.set_voltage(3.7)
except ConnectionError:
    print("Cihaz bağlantısı kesildi")
except TimeoutError:
    print("Komut zaman aşımına uğradı")
except Exception as e:
    print(f"Beklenmeyen hata: {e}")
```

## 📝 Notlar

- Tüm controller'lar thread-safe'dir
- Bağlantı kesildiğinde otomatik yeniden bağlanma
- Güvenlik limitleri her zaman kontrol edilir
- Logging otomatik olarak aktiftir
- Cihaz durumu sürekli izlenir 