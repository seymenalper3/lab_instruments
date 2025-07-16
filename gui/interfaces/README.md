# Interfaces

Bu klasör, farklı iletişim protokolleri ile cihazlara bağlanmak için geliştirilmiş arayüz sınıflarını içerir.

## 📁 Dosyalar

### Temel Sınıf
- `base_interface.py` - Tüm iletişim arayüzleri için temel sınıf

### İletişim Arayüzleri
- `visa_interface.py` - VISA protokolü (USB, GPIB, Ethernet)
- `ethernet_interface.py` - TCP/IP Ethernet iletişimi
- `serial_interface.py` - RS232/RS485 seri port iletişimi

## 🚀 Kullanım

### VISA Interface
```python
from interfaces.visa_interface import VISAInterface

# VISA bağlantısı
interface = VISAInterface("TCPIP::192.168.1.100::INSTR")
interface.connect()

# Komut gönder
interface.write("*IDN?")
response = interface.read()

# Query (write + read)
response = interface.query("MEAS:VOLT?")

interface.disconnect()
```

### Ethernet Interface
```python
from interfaces.ethernet_interface import EthernetInterface

# TCP/IP bağlantısı
interface = EthernetInterface("192.168.1.100", 5025)
interface.connect()

# Veri gönder/al
interface.send_data("MEAS:VOLT?")
response = interface.receive_data()

interface.disconnect()
```

### Serial Interface
```python
from interfaces.serial_interface import SerialInterface

# Seri port bağlantısı
interface = SerialInterface("/dev/ttyUSB0", 9600)
interface.connect()

# Veri gönder/al
interface.write_data("*IDN?")
response = interface.read_data()

interface.disconnect()
```

## 🔧 Sınıf Yapısı

### BaseInterface
Tüm iletişim arayüzleri için ortak interface:
```python
class BaseInterface:
    def connect(self):
        """Bağlantı kur"""
        pass
    
    def disconnect(self):
        """Bağlantıyı kapat"""
        pass
    
    def write(self, data):
        """Veri gönder"""
        pass
    
    def read(self):
        """Veri oku"""
        pass
    
    def query(self, command):
        """Komut gönder ve yanıt al"""
        pass
```

## 📊 İletişim Protokolleri

### VISA (Virtual Instrument Software Architecture)
- **Desteklenen Protokoller**: USB, GPIB, Ethernet, Serial
- **Avantajlar**: Standart, yaygın destek
- **Kullanım Alanı**: Çoğu test cihazı

### Ethernet/TCP-IP
- **Port Numaraları**: 
  - Keithley: 5025
  - Sorensen: 9221
  - Prodigit: 4001
- **Avantajlar**: Hızlı, uzun mesafe
- **Kullanım Alanı**: Ağ üzerinden kontrol

### Serial (RS232/RS485)
- **Baud Rates**: 9600, 19200, 38400, 115200
- **Avantajlar**: Basit, güvenilir
- **Kullanım Alanı**: Eski cihazlar, endüstriyel ortam

## 🛠️ Konfigürasyon

### VISA Konfigürasyonu
```python
visa_config = {
    "resource_name": "TCPIP::192.168.1.100::INSTR",
    "timeout": 5000,  # ms
    "read_termination": "\n",
    "write_termination": "\n"
}
```

### Ethernet Konfigürasyonu
```python
ethernet_config = {
    "host": "192.168.1.100",
    "port": 5025,
    "timeout": 5.0,  # seconds
    "buffer_size": 1024
}
```

### Serial Konfigürasyonu
```python
serial_config = {
    "port": "/dev/ttyUSB0",
    "baudrate": 9600,
    "bytesize": 8,
    "parity": "N",
    "stopbits": 1,
    "timeout": 1.0
}
```

## 🔍 Hata Yönetimi

### Yaygın Hatalar
- `ConnectionError`: Bağlantı kurulamadı
- `TimeoutError`: Zaman aşımı
- `CommunicationError`: İletişim hatası
- `ProtocolError`: Protokol hatası

### Hata Yakalama
```python
try:
    interface.connect()
    response = interface.query("*IDN?")
except ConnectionError:
    print("Cihaza bağlanılamadı")
except TimeoutError:
    print("Komut zaman aşımına uğradı")
except Exception as e:
    print(f"Beklenmeyen hata: {e}")
```

## 📈 Performans Optimizasyonu

### Bağlantı Havuzu
```python
class ConnectionPool:
    def __init__(self, max_connections=5):
        self.pool = []
        self.max_connections = max_connections
    
    def get_connection(self, address):
        # Mevcut bağlantıyı kullan veya yeni oluştur
        pass
```

### Asenkron İletişim
```python
import asyncio

async def async_query(interface, command):
    return await interface.async_query(command)
```

## 🛡️ Güvenlik

### Güvenlik Önlemleri
- **Bağlantı Şifreleme**: TLS/SSL desteği
- **Kimlik Doğrulama**: Kullanıcı/parola kontrolü
- **Erişim Kontrolü**: IP whitelist
- **Veri Bütünlüğü**: Checksum kontrolü

### Güvenli Bağlantı
```python
secure_config = {
    "use_tls": True,
    "verify_cert": True,
    "username": "admin",
    "password": "password"
}
```

## 🧪 Test Araçları

### Bağlantı Testi
```python
def test_connection(interface):
    try:
        interface.connect()
        response = interface.query("*IDN?")
        print(f"Cihaz: {response}")
        return True
    except Exception as e:
        print(f"Test başarısız: {e}")
        return False
```

### Performans Testi
```python
def performance_test(interface, iterations=100):
    start_time = time.time()
    for i in range(iterations):
        interface.query("*IDN?")
    end_time = time.time()
    
    avg_time = (end_time - start_time) / iterations
    print(f"Ortalama yanıt süresi: {avg_time:.3f}s")
```

## 📝 Notlar

- Tüm interface'ler thread-safe'dir
- Otomatik yeniden bağlanma desteği
- Bağlantı durumu sürekli izlenir
- Timeout değerleri cihaza göre ayarlanmalı
- Hata logları otomatik olarak kaydedilir 