# Current Profiles

Bu klasör, Keithley cihazlarında özel akım profilleri uygulamak için geliştirilmiş betikleri içerir.

## 📁 Dosyalar

### Profil Uygulayıcılar
- `apply_current_profile.py` - Temel akım profili uygulayıcı
- `apply_profile_list_mode.py` - Liste modunda profil uygulayıcı

### Batarya Profilleri
- `keithley_battery_profile.py` - Kapsamlı batarya profili
- `keithley_simple_profile.py` - Basit batarya profili
- `keithley_working_profile.py` - Çalışan batarya profili
- `keithley_working_profile_V3.py` - V3 çalışan batarya profili
- `keithley_working_profile_V4.py` - V4 çalışan batarya profili (en güncel)

## 🚀 Kullanım

### Basit Profil
```bash
python keithley_simple_profile.py
```

### Gelişmiş Profil
```bash
python keithley_working_profile_V4.py
```

### Liste Modu
```bash
python apply_profile_list_mode.py
```

## 📊 Özellikler

- **Dinamik Akım Kontrolü**: Zamana bağlı akım profilleri
- **Güvenlik Limitleri**: Voltaj ve akım koruma
- **Real-time Monitoring**: Anlık ölçüm takibi
- **Veri Loglama**: Otomatik veri kaydetme

## 📈 Profil Türleri

1. **Sabit Akım**: Belirli akım seviyesinde çalışma
2. **Rampa Profili**: Kademeli akım artışı/azalışı
3. **Pulse Profili**: Pulse şeklinde akım uygulaması
4. **Özel Profil**: Kullanıcı tanımlı akım profilleri

## 📝 Notlar

- Profiller CSV dosyalarından yüklenebilir
- Sonuçlar `../../data/` ve `../../results/` klasörlerine kaydedilir
- V4 versiyonu en stabil ve özellik zengin versiyondur 