# Utilities

Bu klasör, sistem yönetimi, teşhis ve yardımcı işlevler için geliştirilmiş betikleri içerir.

## 📁 Dosyalar

### Sistem Yönetimi
- `battery_cleanup.py` - Batarya sistem temizleme
- `make_local.py` - Yerel konfigürasyon oluşturucu

### Teşhis Araçları
- `diagnose_device.py` - Cihaz teşhis aracı
- `test_communication.py` - İletişim testi

### Düzeltme Araçları
- `keithley_fixed_script.py` - Keithley düzeltme betiği

## 🚀 Kullanım

### Cihaz Teşhisi
```bash
python diagnose_device.py
```

### İletişim Testi
```bash
python test_communication.py
```

### Sistem Temizleme
```bash
python battery_cleanup.py
```

## 🔧 Araç Kategorileri

### 1. Teşhis Araçları
- **Cihaz Durumu**: Bağlantı ve durum kontrolü
- **İletişim Testi**: VISA/SCPI iletişim doğrulama
- **Performans Analizi**: Sistem performans ölçümü
- **Hata Tespiti**: Sistem hatalarının belirlenmesi

### 2. Temizleme Araçları
- **Veri Temizleme**: Geçici dosyaların silinmesi
- **Log Temizleme**: Eski log dosyalarının temizlenmesi
- **Önbellek Temizleme**: Sistem önbelleğinin temizlenmesi
- **Konfigürasyon Sıfırlama**: Ayarların varsayılana döndürülmesi

### 3. Konfigürasyon Araçları
- **Yerel Ayarlar**: Kullanıcı özel ayarları
- **Cihaz Konfigürasyonu**: Cihaz özel parametreleri
- **Ağ Ayarları**: İletişim parametreleri
- **Güvenlik Ayarları**: Güvenlik limitlerinin ayarlanması

## 📊 Teşhis Çıktıları

### Sistem Durumu
```
Device Status: Connected
Communication: OK
Firmware Version: 1.2.3
Hardware Revision: A01
Temperature: 25.3°C
```

### İletişim Testi
```
VISA Resource: TCPIP::192.168.1.100::INSTR
Connection Status: SUCCESS
Response Time: 15ms
Command Success Rate: 100%
```

### Performans Metrikleri
```
CPU Usage: 45%
Memory Usage: 2.1GB / 4.0GB
Disk Usage: 15.2GB / 32.0GB
Network Latency: 2ms
```

## 🛠️ Bakım İşlemleri

### Düzenli Bakım
```bash
# Haftalık temizlik
python battery_cleanup.py --weekly

# Aylık bakım
python battery_cleanup.py --monthly

# Sistem teşhisi
python diagnose_device.py --full
```

### Sorun Giderme
```bash
# İletişim sorunları
python test_communication.py --verbose

# Cihaz sorunları
python diagnose_device.py --debug

# Sistem düzeltme
python keithley_fixed_script.py --repair
```

## 📋 Log Dosyaları

### Teşhis Logları
- `diagnosis_YYYYMMDD_HHMMSS.log` - Teşhis sonuçları
- `communication_test_YYYYMMDD_HHMMSS.log` - İletişim test logları
- `system_status_YYYYMMDD_HHMMSS.log` - Sistem durum logları

### Temizleme Logları
- `cleanup_YYYYMMDD_HHMMSS.log` - Temizleme işlem logları
- `maintenance_YYYYMMDD_HHMMSS.log` - Bakım işlem logları

## 🔐 Güvenlik

### Güvenlik Kontrolleri
- **Yetkilendirme**: Kullanıcı yetki kontrolü
- **Veri Koruması**: Hassas veri şifreleme
- **Erişim Logları**: Sistem erişim kayıtları
- **Güvenlik Güncellemeleri**: Otomatik güvenlik yamaları

## 📝 Notlar

- Utilities betikleri yönetici yetkisi gerektirebilir
- Temizleme işlemleri geri alınamaz
- Teşhis sonuçları `../../logs/` klasörüne kaydedilir
- Düzenli bakım önerilir
- Sistem değişiklikleri öncesi yedekleme yapın 