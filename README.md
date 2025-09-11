# Lab Instruments Control System

Bu proje, laboratuvar cihazlarının kontrolü ve test işlemleri için geliştirilmiş bir Python tabanlı sistem koleksiyonudur.

## 📁 Proje Yapısı

```
lab_instruments/
├── docs/                    # Cihaz manuelleri ve dökümanlar
├── instruments/             # Cihazlara özel kodlar ve veriler
│   ├── keithley/           # Keithley cihazları
│   │   ├── src/            # Kaynak kodlar (kategorilere ayrılmış)
│   │   │   ├── battery_models/      # Batarya modeli oluşturma
│   │   │   ├── battery_tests/       # Batarya test betikleri
│   │   │   ├── current_profiles/    # Akım profili betikleri
│   │   │   ├── pulse_tests/         # Pulse test betikleri
│   │   │   ├── utilities/           # Yardımcı araçlar
│   │   │   └── demos/               # Demo betikleri
│   │   ├── data/           # Ham veri dosyaları
│   │   ├── results/        # Test sonuçları
│   │   └── logs/           # Log kayıtları
│   └── sgx400/             # SGX400 cihazları
├── gui/                    # Ana GUI uygulaması
├── archive/                # Eski kodlar ve arşiv
└── myenv/                  # Python sanal ortamı
```

## 🚀 Kurulum

### Linux Kurulumu

#### Gereksinimler
- Python 3.8+
- Virtual environment (önerilen)

#### Adımlar
1. Repository'yi klonlayın
2. Sanal ortamı aktifleştirin:
   ```bash
   source myenv/bin/activate
   ```
3. Gerekli paketleri yükleyin (GUI klasöründe requirements.txt mevcut)

---

## 🪟 Windows Kurulumu (Step-by-Step)

### 1️⃣ Sistem Gereksinimleri
- **Windows 10/11** (64-bit önerilen)
- **Python 3.8 veya üzeri**
- **Administrator yetkisi** (sürücü kurulumu için)
- **USB portu** (USB cihaz bağlantısı için)
- **Ethernet bağlantısı** (network cihazları için)

### 2️⃣ Python Kurulumu

1. **Python'u indirin:**
   - [python.org](https://www.python.org/downloads/) adresinden Python 3.8+ indirin
   - ⚠️ **ÖNEMLİ:** Kurulum sırasında "Add Python to PATH" seçeneğini işaretleyin

2. **Kurulumu doğrulayın:**
   ```cmd
   python --version
   pip --version
   ```

### 3️⃣ VISA Sürücü Kurulumu

**Keithley ve diğer test cihazları için gerekli:**

#### Seçenek A: NI-VISA (Önerilen)
1. [NI-VISA Runtime](https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html) indirin
2. İndirilen dosyayı **Administrator olarak çalıştırın**
3. Kurulum tamamlandıktan sonra bilgisayarı yeniden başlatın

#### Seçenek B: Keysight IO Libraries
1. [Keysight IO Libraries](https://www.keysight.com/us/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html) indirin
2. **Administrator olarak kurulum yapın**
3. Sistem yeniden başlatın

### 4️⃣ Proje Kurulumu

1. **Repository'yi klonlayın:**
   ```cmd
   git clone <repository-url>
   cd lab_instruments
   ```

2. **Python sanal ortamı oluşturun:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Gerekli paketleri yükleyin:**
   ```cmd
   cd gui
   pip install -r requirements.txt
   pip install PyQt5
   ```

### 5️⃣ Cihaz Bağlantısı Test

1. **USB Bağlantısı:**
   - Keithley cihazını USB ile bilgisayara bağlayın
   - Windows Device Manager'da cihazın tanındığını kontrol edin

2. **Ethernet Bağlantısı:**
   - Cihazı aynı ağa bağlayın
   - Cihazın IP adresini not edin

3. **Bağlantıyı test edin:**
   ```cmd
   cd gui\utils
   python test_communication.py
   ```

---

## 🖥️ GUI Uygulaması Kullanımı

### 📋 GUI Başlatma

1. **Uygulamayı başlatın:**
   ```cmd
   cd gui
   python main.py
   ```

2. **Ana pencere açılacak** - Farklı cihaz sekmeleri görüntülenecek

### 🔌 Cihaz Bağlantısı

#### Adım 1: Connection Widget
1. **Sol üst köşedeki "Connection" panelini kullanın**
2. **Bağlantı türünü seçin:**
   - `USB`: Cihaz otomatik algılanacak
   - `Ethernet`: IP adresini girin (örn: `192.168.1.100`)
   - `Serial`: COM port seçin (örn: `COM3`)

#### Adım 2: Cihaz Keşfi
1. **"Scan Devices" butonuna tıklayın**
2. **Bulunan cihazlar listede görünecek**
3. **İstediğiniz cihazı seçin**
4. **"Connect" butonuna tıklayın**

✅ **Bağlantı başarılı olursa:** Durum ışığı yeşil olacak
❌ **Bağlantı başarısız olursa:** Kırmızı uyarı mesajı görünecek

### 🔋 Keithley Sekmesi Kullanımı

#### Battery Test Modu
1. **"Keithley" sekmesine tıklayın**
2. **"Battery Test" modunu seçin**
3. **Test parametrelerini ayarlayın:**
   - Voltage: `3.0V - 4.2V` arası
   - Current: `0.1A - 3.0A` arası
   - Duration: Test süresi (saniye)
4. **"Start Test" butonuna tıklayın**

#### Current Profile Modu
1. **"Current Profile" modunu seçin**
2. **Profil dosyasını yükleyin** (.csv formatında)
3. **"Load Profile" → "Apply Profile" → "Start"**

#### Pulse Test Modu
1. **"Pulse Test" modunu seçin**
2. **Pulse parametrelerini ayarlayın:**
   - Pulse Width: `1ms - 1000ms`
   - Pulse Current: `0.1A - 3.0A`
   - Rest Time: `10ms - 10s`
3. **"Generate Pulse" butonuna tıklayın**

### 📊 Monitoring Sekmesi

#### Real-time Veri İzleme
1. **"Monitoring" sekmesine tıklayın**
2. **İzlenecek parametreleri seçin:**
   - ☑️ Voltage
   - ☑️ Current
   - ☑️ Power
   - ☑️ Temperature
3. **"Start Monitoring" butonuna tıklayın**

#### Grafik Görüntüleme
- **Canlı grafikler otomatik güncellenir**
- **Zoom:** Mouse tekerleği ile yakınlaştırma
- **Pan:** Sağ tık + sürükle ile grafik kaydırma
- **Export:** "Save Graph" butonu ile PNG/SVG kaydetme

### 💾 Veri Loglama

#### Otomatik Loglama
- **Tüm testler otomatik olarak loglanır**
- **Dosya konumu:** `data/` klasörü
- **Dosya formatı:** `test_YYYYMMDD_HHMMSS.csv`

#### Manuel Kaydetme
1. **Test sonrası "Save Results" butonuna tıklayın**
2. **Dosya adını ve konumunu seçin**
3. **Format seçin:** CSV, JSON veya Excel

### 🔧 Ayarlar ve Konfigürasyon

#### Cihaz Ayarları
1. **"Settings" menüsüne tıklayın**
2. **"Device Configuration" seçin**
3. **Güvenlik limitlerini ayarlayın:**
   - Max Voltage: `5.0V`
   - Max Current: `3.0A`
   - Max Power: `15.0W`

#### GUI Ayarları
- **Theme:** Açık/Koyu tema seçimi
- **Language:** Türkçe/İngilizce dil seçimi
- **Auto-save:** Otomatik kaydetme aralığı

## 🔧 Cihazlar

### Keithley Cihazları
Keithley 2281S ve benzeri güç kaynakları için geliştirilmiş betikler.

#### Kategoriler:
- **Battery Models**: Batarya davranışını simüle eden modeller
- **Battery Tests**: Batarya performans testleri
- **Current Profiles**: Özel akım profilleri
- **Pulse Tests**: Pulse karakterizasyon testleri
- **Utilities**: Teşhis ve yardımcı araçlar

### SGX400 Cihazları
SGX400 serisi cihazlar için test betikleri.

## 📊 GUI Uygulaması

`gui/` klasöründe modüler bir GUI uygulaması bulunmaktadır:
- Cihaz bağlantı yönetimi
- Real-time monitoring
- Veri loglama
- Test sonuçları görüntüleme

### GUI Başlatma
```bash
cd gui
python main.py
```

## 📈 Kullanım Örnekleri

### Batarya Testi
```bash
cd instruments/keithley/src/battery_tests
python battery_aging_assessment.py
```

### Pulse Testi
```bash
cd instruments/keithley/src/pulse_tests
python demo_pulse_test_60s.py
```

### Akım Profili Uygulama
```bash
cd instruments/keithley/src/current_profiles
python apply_current_profile.py
```

## 📋 Veri Yapısı

### Veri Dosyaları
- **CSV**: Test sonuçları ve ölçüm verileri
- **JSON**: Konfigürasyon ve metadata
- **LOG**: Sistem logları ve hata kayıtları

### Dosya Adlandırma
- `battery_test_YYYYMMDD_HHMMSS.csv`
- `current_profile_YYYYMMDD_HHMMSS.log`
- `pulse_test_YYYYMMDD_HHMMSS.json`

## 🛠️ Geliştirme

### Yeni Betik Ekleme
1. Uygun kategori klasörüne yerleştirin
2. Standart logging formatını kullanın
3. Veri dosyalarını `data/` veya `results/` klasörüne kaydedin

### Kod Standartları
- Python PEP 8 standartlarını takip edin
- Docstring'leri ekleyin
- Error handling implement edin

## 📚 Dökümanlar

`docs/` klasöründe cihaz manuelleri ve teknik dökümanlar bulunmaktadır:
- Keithley 2281S Reference Manual
- SGX400 Operation Manual

## 🔍 Troubleshooting

### Linux Sorunları
1. **Cihaz Bağlantısı**: VISA sürücülerini kontrol edin
2. **Port Erişimi**: Kullanıcı izinlerini kontrol edin
3. **Paket Eksikliği**: `requirements.txt` dosyasını kontrol edin

---

## 🛠️ Windows Troubleshooting

### 🔴 Yaygın Kurulum Sorunları

#### Problem: "python komut bulunamadı"
**Çözüm:**
1. Python'u PATH'e ekleyin:
   ```cmd
   # Sistem değişkenlerini açın
   # PATH'e şunu ekleyin: C:\Python38\;C:\Python38\Scripts\
   ```
2. Veya Python'u yeniden kurun ("Add to PATH" seçeneği ile)

#### Problem: "No module named 'pyvisa'"
**Çözüm:**
```cmd
pip install --upgrade pyvisa pyvisa-py
pip install PyQt5
```

#### Problem: VISA sürücü hatası
**Çözüm:**
1. NI-VISA'yı yeniden kurun (Administrator olarak)
2. Windows Firewall'da Python'u allow edin
3. Antivirus yazılımının Python'u engellememesini sağlayın

### 🔌 Cihaz Bağlantı Sorunları

#### Problem: USB cihaz tanınmıyor
**Kontrol Listesi:**
- ✅ USB kablo çalışıyor mu? (farklı kablo deneyin)
- ✅ Device Manager'da cihaz görünüyor mu?
- ✅ VISA sürücüler kurulu mu?
- ✅ Cihaz açık ve hazır mı?

**Çözüm:**
1. **Device Manager'ı açın** (`devmgmt.msc`)
2. **"Universal Serial Bus controllers" sekmesine bakın**
3. **Sarı ünlem işareti varsa sağ tık → "Update driver"**

#### Problem: Ethernet bağlantısı başarısız
**Kontrol Listesi:**
- ✅ Cihaz ve PC aynı ağda mı?
- ✅ IP adresi doğru mu?
- ✅ Port numarası doğru mu? (genelde 5025)
- ✅ Windows Firewall engellemiyor mu?

**Test komutu:**
```cmd
# Ping testi
ping 192.168.1.100

# Telnet testi
telnet 192.168.1.100 5025
```

#### Problem: Serial port erişim hatası
**Çözüm:**
1. **Doğru COM port'u bulun:**
   ```cmd
   # Device Manager → Ports (COM & LPT)
   ```
2. **Port'u kullanan başka program kapatın**
3. **Baud rate'i kontrol edin** (genelde 9600)

### 🖥️ GUI Sorunları

#### Problem: GUI açılmıyor
**Çözüm:**
```cmd
# PyQt5 yükleyin
pip install PyQt5

# Alternatif: PySide2
pip install PySide2
```

#### Problem: GUI donuyor
**Kontrol:**
- Task Manager'da Python process'leri kontrol edin
- Çoklu GUI instance açık mı?
- Antivirus real-time scan kapatın (test için)

#### Problem: Grafik görünmüyor
**Çözüm:**
```cmd
pip install matplotlib
pip install pyqtgraph
```

### 📊 Veri Loglama Sorunları

#### Problem: Dosya kaydetme hatası
**Kontrol:**
- ✅ Yazma yetkisi var mı?
- ✅ Disk alanı yeterli mi?
- ✅ Dosya yolu geçerli mi?

**Çözüm:**
- Farklı klasör seçin (Desktop, Documents)
- Administrator olarak çalıştırın

#### Problem: CSV dosyası bozuk
**Kontrol:**
- Excel ile açmaya çalışın
- NotePad ile raw text kontrol edin
- UTF-8 encoding sorunu olabilir

### 🔧 Test ve Doğrulama

#### Temel Bağlantı Testi
```cmd
cd gui
python -c "
import pyvisa
rm = pyvisa.ResourceManager()
print(rm.list_resources())
"
```

#### VISA Kurulum Testi
```cmd
python -c "
import visa
print('VISA version:', visa.__version__)
"
```

#### Cihaz Kimlik Testi
```cmd
python -c "
import pyvisa
rm = pyvisa.ResourceManager()
inst = rm.open_resource('USB0::0x05E6::0x2281::04420926::INSTR')
print(inst.query('*IDN?'))
inst.close()
"
```

### 🆘 Acil Durum Kurtarma

#### Cihaz Yanıt Vermiyor
1. **Soft Reset:**
   ```python
   device.write("*RST")
   ```
2. **Hard Reset:** Cihazı kapatıp açın
3. **USB Reconnect:** USB kablosunu çıkarıp takın

#### Sistem Kilitleme
1. **Ctrl+C** ile Python script'i durdurun
2. **Task Manager** ile Python process'leri kapatın
3. **GUI donmuşsa Alt+F4**

### 📞 Destek Kaynakları

#### Log Dosyaları Konumu
- **Windows:** `%APPDATA%\lab_instruments\logs\`
- **Geçici:** `C:\temp\lab_instruments\`

#### Yararlı Komutlar
```cmd
# Python modül listesi
pip list

# VISA cihaz listesi
python -c "import pyvisa; print(pyvisa.ResourceManager().list_resources())"

# Sistem bilgisi
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
```

### Log Dosyaları
Hata ayıklama için `logs/` klasöründeki log dosyalarını inceleyin.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun
3. Değişikliklerinizi commit edin
4. Pull request gönderin

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 📞 İletişim

Sorularınız için proje maintainer'ı ile iletişime geçin.

---

**Son Güncelleme**: $(date +%Y-%m-%d) 