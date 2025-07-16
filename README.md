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

### Gereksinimler
- Python 3.8+
- Virtual environment (önerilen)

### Adımlar
1. Repository'yi klonlayın
2. Sanal ortamı aktifleştirin:
   ```bash
   source myenv/bin/activate
   ```
3. Gerekli paketleri yükleyin (GUI klasöründe requirements.txt mevcut)

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

### Yaygın Sorunlar
1. **Cihaz Bağlantısı**: VISA sürücülerini kontrol edin
2. **Port Erişimi**: Kullanıcı izinlerini kontrol edin
3. **Paket Eksikliği**: `requirements.txt` dosyasını kontrol edin

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