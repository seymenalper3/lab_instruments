# Lab Instruments - Windows Kurulum Rehberi

## 📦 Paket İçeriği

Bu arşiv, Lab Instruments GUI uygulamasının kaynak kodunu ve Windows için build scriptlerini içerir.

### Dahil Edilen Dosyalar
- ✅ Tüm Python kaynak kodları
- ✅ PyInstaller spec dosyası (`lab_instruments.spec`)
- ✅ Windows build scripti (`build_windows.bat`)
- ✅ Logo ve icon dosyaları (ITU logosu dahil)
- ✅ Gereksinimler dosyası (`gui/requirements.txt`)
- ✅ Dokümantasyon

### Hariç Tutulan Klasörler
- ❌ Virtual environment (`myenv/`)
- ❌ Build çıktıları (`build/`, `dist/`)
- ❌ Log dosyaları (`logs/`)
- ❌ Test verileri (`data/`)
- ❌ Git geçmişi (`.git/`)

---

## 🚀 Kurulum Adımları

### 1. Önkoşullar

Windows sisteminde aşağıdakilerin kurulu olması gerekir:

#### Python 3.8 veya üzeri
```bash
# Kurulu olup olmadığını kontrol edin:
python --version
```

**İndirme:** https://www.python.org/downloads/

**Önemli:** Kurulum sırasında "Add Python to PATH" seçeneğini işaretleyin!

#### NI-VISA veya Keysight IO Libraries (VISA Sürücüleri)

USB/GPIB cihaz iletişimi için gereklidir:

- **NI-VISA:** https://www.ni.com/visa/
- **Keysight IO Libraries:** https://www.keysight.com/find/iolib

**Not:** Sadece Serial/Ethernet kullanacaksanız VISA gerekli değildir.

---

### 2. Arşivi Açma

Windows'ta arşivi açmak için:

**Seçenek 1: 7-Zip (Önerilen)**
1. 7-Zip'i indirin: https://www.7-zip.org/
2. Arşive sağ tıklayın → "7-Zip" → "Extract Here"

**Seçenek 2: WinRAR**
1. WinRAR'ı indirin: https://www.win-rar.com/
2. Arşive sağ tıklayın → "Extract Here"

**Seçenek 3: Windows Tar (Windows 10+)**
```cmd
tar -xzf lab_instruments_windows.tar.gz
```

---

### 3. Executable Oluşturma

Klasöre girin ve build scriptini çalıştırın:

```cmd
cd lab_instruments
build_windows.bat
```

Script otomatik olarak:
1. ✅ Python sürümünü kontrol eder
2. ✅ PyInstaller'ı yükler (gerekirse)
3. ✅ Tüm bağımlılıkları yükler
4. ✅ Önceki build'leri temizler
5. ✅ Executable'ı oluşturur

**Tahmini Süre:** 5-10 dakika (internet hızına bağlı)

---

### 4. Çıktı

Build başarılı olduğunda:

```
dist/
└── LabInstruments.exe  (~50-100 MB)
```

**İlk Çalıştırma:**
- İlk açılış 5-10 saniye sürebilir (dosyalar açılıyor)
- Sonraki açılışlar daha hızlıdır
- Antivirus false positive uyarısı gösterebilir (normal)

---

## 🎨 Dahil Edilen Asset'ler

Uygulama aşağıdaki görsel öğeleri içerir:

- **Ana Logo:** `gui/assets/logo.png`
- **Uygulama İkonu:** `gui/assets/app_icon.ico` (exe ikonunda kullanılır)
- **İTÜ Logosu:** `gui/assets/images/itu_logo.png`

Tüm logo ve ikonlar executable'a gömülüdür.

---

## 🛠️ Manuel Kurulum (Build Etmeden)

Eğer executable oluşturmak istemiyorsanız, doğrudan Python ile çalıştırabilirsiniz:

### 1. Bağımlılıkları Yükleyin
```cmd
cd lab_instruments
python -m pip install -r gui\requirements.txt
```

### 2. Uygulamayı Çalıştırın
```cmd
python gui\main.py
```

---

## 📋 Gerekli Python Paketleri

- `pyvisa` - VISA cihaz iletişimi
- `pyvisa-py` - Pure Python VISA backend
- `pyserial` - Serial port iletişimi
- `pandas` - Veri işleme
- `openpyxl` - Excel dosya desteği
- `Pillow` - Görüntü işleme (logolar için)
- `tkinter` - GUI framework (Python ile birlikte gelir)

---

## ⚠️ Bilinen Sorunlar ve Çözümler

### Antivirus Uyarısı
PyInstaller executables bazı antivirusler tarafından şüpheli görülebilir.

**Çözüm:**
- Windows Defender'da istisna ekleyin
- Dosya güvenlidir (kaynak kodundan oluşturulmuştur)

### "Python was not found" Hatası
**Çözüm:**
1. Python'un PATH'e ekli olduğundan emin olun
2. Sistemi yeniden başlatın
3. `python` yerine `py` komutunu deneyin

### PyInstaller Build Hatası
**Çözüm:**
```cmd
python -m pip install --upgrade pip
python -m pip install --upgrade pyinstaller
```

### VISA Cihazları Bulunamıyor
**Çözüm:**
1. NI-VISA veya Keysight IO Libraries kurulu mu kontrol edin
2. Cihazın düzgün bağlandığını doğrulayın
3. NI MAX (Measurement & Automation Explorer) ile test edin

---

## 📖 Ek Kaynaklar

- **Ana README:** `README.md`
- **Dokümantasyon:** `docs/` klasörü
- **Test Scriptleri:** `gui/tests/`
- **Örnek Profiller:** `gui/examples/`

---

## 🆘 Destek

Sorun yaşarsanız:

1. **Build Loglarını Kontrol Edin:** Console çıktısında hata mesajları
2. **Log Dosyalarına Bakın:** `logs/` klasörü (çalıştırma sonrası)
3. **Sistem Gereksinimlerini Kontrol Edin:** Python 3.8+, Windows 10+

---

## 📦 Dağıtım Paketi Oluşturma

Executable'ı başkalarıyla paylaşmak için:

1. `dist/` klasörünün tamamını kopyalayın
2. Aşağıdaki dosyaları ekleyin:
   - `README.md`
   - `WINDOWS_SETUP.md` (bu dosya)
   - `docs/` klasörü (opsiyonel)
3. Bir ZIP dosyası oluşturun

**Minimum Dağıtım Paketi:**
```
LabInstruments_v1.0/
├── LabInstruments.exe
├── README.md
└── WINDOWS_SETUP.md
```

---

## 📊 Versiyon Bilgisi

- **Uygulama:** Lab Instruments GUI v1.0.0
- **Python Minimum:** 3.8
- **Windows:** 10 ve üzeri
- **Build Tarihi:** 2024-12-19

---

## ✅ Başarı Kontrol Listesi

Build ve kurulum tamamlandıktan sonra:

- [ ] `LabInstruments.exe` oluşturuldu
- [ ] Executable çalıştı (hata vermeden açıldı)
- [ ] Ana pencere göründü
- [ ] Logolar düzgün yüklendi (ITU logosu dahil)
- [ ] Cihaz bağlantısı test edildi (varsa)
- [ ] Log dosyaları oluşturuldu

**Her şey çalışıyorsa, kurulum başarılıdır! 🎉**

---

## 🔄 Güncelleme

Yeni bir versiyon için:

1. Güncel arşivi indirin
2. Yeni klasöre açın
3. `build_windows.bat`'i tekrar çalıştırın
4. Eski `dist/` klasörünü silin veya yedekleyin

---

**Son Güncelleme:** 2024-12-19
**Hazırlayan:** Seymen Alper
