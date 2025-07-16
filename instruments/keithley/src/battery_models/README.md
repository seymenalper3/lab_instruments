# Battery Models

Bu klasör, batarya davranışını simüle eden modeller ve model oluşturma betiklerini içerir.

## 📁 Dosyalar

### Model Oluşturucular
- `battery_model_generator_opus.py` - Opus tabanlı batarya modeli oluşturucu
- `battery_model_generator_v11.py` - V11 batarya modeli oluşturucu
- `battery_model_generator_v12_quick.py` - Hızlı V12 batarya modeli oluşturucu
- `generate_battery_model.py` - Temel batarya modeli oluşturucu
- `generate_battery_model_V2.py` - V2 batarya modeli oluşturucu
- `generate_battery_model_V3.py` - V3 batarya modeli oluşturucu
- `generate_battery_model_V4.py` - V4 batarya modeli oluşturucu
- `generate_battery_model_demo.py` - Demo batarya modeli oluşturucu

### Özel Modeller
- `bellek_ile_model.py` - Bellek tabanlı batarya modeli

## 🚀 Kullanım

Model oluşturmak için:
```bash
python battery_model_generator_opus.py
```

Demo çalıştırmak için:
```bash
python generate_battery_model_demo.py
```

## 📊 Çıktılar

Modeller genellikle şu formatlarda çıktı üretir:
- CSV dosyaları (voltaj-akım karakteristikleri)
- JSON dosyaları (model parametreleri)
- Log dosyaları (işlem kayıtları)

## 📝 Notlar

- Modeller `../../results/` klasörüne kaydedilir
- Her model farklı batarya türleri için optimize edilmiştir
- V12 versiyonu en hızlı çalışan versiyondur 