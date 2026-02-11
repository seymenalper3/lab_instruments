# Laboratuvar Cihazlari GUI - Kullanim Kilavuzu

Bu kilavuz, EV batarya test sistemi icin gelistirilen cok cihazli kontrol arayuzunun kullanimi hakkinda bilgi vermektedir. GUI, uc farkli laboratuvar cihazini tek bir arayuzden kontrol etmeye olanak saglar.

---

## Desteklenen Cihazlar

| Cihaz | Tur | Maks Gerilim | Maks Akim | Maks Guc | Baglanti Arayuzleri |
|-------|-----|-------------|-----------|----------|---------------------|
| **Keithley 2281S** | Batarya Simulator/Emulator | 20V | 6A | 120W | USB, Ethernet, GPIB |
| **Sorensen SGX400-12D** | DC Guc Kaynagi | 400V | 12A | 4800W | RS232, Ethernet, GPIB |
| **Prodigit 34205A** | Elektronik Yuk | 600V | 160A | 5000W | RS232, USB |

---

## 1. GUI'yi Baslatma

### Gereksinimler

- Python 3.6 veya ustu
- Gerekli Python paketleri:

```
pip install -r requirements.txt
```

`requirements.txt` dosyasindaki paketler:

| Paket | Aciklama |
|-------|----------|
| `pyserial` | Seri port (RS232) iletisimi |
| `pyvisa` | VISA protokolu (USB/GPIB) |
| `pyvisa-py` | PyVISA backend |
| `pandas` | Veri isleme ve CSV/Excel okuma |
| `openpyxl` | Excel (.xlsx) dosya destegi |
| `Pillow` | Logo ve gorsel islemleri |

### Uygulamayi Calistirma

```bash
cd gui
python main.py
```

Uygulama basladiginda terminal ciktisinda Python surumu ve platform bilgisi gorunur. Eger sadece seri port (RS232) veya Ethernet baglantisi kullaniyorsaniz, "PyVISA not available" uyarisi normaldir ve calismayi etkilemez. PyVISA yalnizca USB ve GPIB baglantilari icin gereklidir.

Uygulama penceresi 1200x800 piksel boyutunda, ekranin ortasinda acilir. Baslik cubugunda "Multi-Device Test Controller" yazar ve sol ust kosede kurum logosu gorunur.

---

## 2. Baglanti Kurulumu

Her cihaz sekmesinin ust kisminda "Connection Settings" basligi altinda baglanti ayarlari bulunur.

### Arayuz Tipleri

**RS232 (Seri Port):**
- Acilir menuден COM port secin (ornegin `COM3`, `/dev/ttyUSB0`)
- Baud rate secin:
  - Sorensen: varsayilan 9600
  - Prodigit: varsayilan 115200
- Kablo fiziksel olarak baglanmis olmalidir

**Ethernet:**
- IP adresi girin (ornegin `192.168.1.100`)
- Port numarasi girin:
  - Keithley varsayilan: `5025` (SCPI standart)
  - Sorensen varsayilan: `9221`
- Keithley icin cihazin IP adresini bulmak icin: Cihaz on panelinde MENU > Settings > Communication > LAN yolunu takip edin
- Bilgisayar ve cihaz ayni agda olmalidir

**USB / GPIB (VISA):**
- VISA kaynak stringi girin (ornegin `USB0::0x05E6::0x2281S::4587429::0::INSTR`)
- "Detect" butonuna tiklayarak mevcut VISA kaynaklarini otomatik tarayabilirsiniz
- Listeden cihazinizi secip "Confirm" ile onaylayin
- PyVISA kurulu olmalidir

### Baglanma Adimi

1. Ilgili cihaz sekmesine gecin (Sorensen, Keithley veya Prodigit)
2. Arayuz tipini secin
3. Gerekli parametreleri girin
4. "Connect" butonuna tiklayin
5. Basarili baglantida durum "Connected" (yesil) olarak degisir ve cihazin IDN yaniti durum cubugunda gorunur
6. Baglanti ayarlari otomatik olarak `~/.lab_instruments/connection_settings.json` dosyasina kaydedilir ve sonraki baglantilar icin hatirlanir

### Baglanti Kesme

"Disconnect" butonuna tiklayin. Cihaz ciktisi kapatilir ve baglanti guvenli sekilde sonlandirilir.

### Acil Durdurma (Emergency Stop)

Baslik cubugunun sag tarafinda kirmizi "EMERGENCY STOP" butonu bulunur. Bu butona tiklandiginda **tum bagli cihazlarin ciktisi aninda kapatilir**. Guc kaynaklarinin output'u ve elektronik yukun load'u sifirlanir. Acil durumlarda bu butonu kullanin.

---

## 3. Keithley 2281S - Batarya Simulator

Keithley 2281S sekmesi, batarya test ve simulasyonu icin gelismis kontroller sunar.

### 3.1 Modlar

| Mod | Aciklama | Kullanim Alani |
|-----|----------|----------------|
| Power Supply | Standart DC guc kaynagi | Gerilim/akim ayarlama, sarj islemleri |
| Battery Test | Batarya test modu | Desarj, puls testi, batarya model olusturma |
| Battery Simulator | Batarya simulasyonu | Batarya davranisini taklit etme |

### 3.2 Temel Islemler

**Set Parameters & Mode:**
- "Function/Mode" menuден modu secin
- Gerilim (V) ve akim (A) degerlerini girin
- "Set Parameters & Mode" butonuna tiklayin
- Cihaz otomatik olarak secilen moda gecer, parametreleri uygular ve gerilim korumasi ayarlar
- Aktif mod, etiket uzerinde renkli olarak gosterilir (Power Supply: yesil, Battery Test: mavi, Battery Simulator: turuncu)

**Output ON:**
- Cikisi aktif etmeden once guvenlik kontrolleri yapilir:
  - Gerilim aralik kontrolu (0 - 20V)
  - Akim aralik kontrolu (0 - 6A)
  - Guc limiti kontrolu (V x I <= 120W)
- Cihaz limitlerinin %80'ine yaklasan degerlerde uyari penceresi cikar
- LED gostergesi yesile doner

**Output OFF:**
- Cikisi guvenli sekilde kapatir
- LED gostergesi griye doner

### 3.3 Cikti Formati

Test fonksiyonlarinin log dosyalari icin format secimi yapilabilir:
- **CSV (Fast):** En hizli kayit formati, evrensel uyumluluk
- **Excel:** .xlsx formati (openpyxl gerektirir)
- **Both:** Her iki formatta da kayit yapar

### 3.4 Pulse Test (Puls Testi)

Batarya empedans olcumu icin desarj/dinlenme donguleri gerceklestirir.

**Parametreler:**

| Parametre | Varsayilan | Aciklama |
|-----------|-----------|----------|
| Pulses | 2 | Puls dongusu sayisi |
| Pulse Time (s) | 30 | Desarj suresi (saniye) |
| Rest Time (s) | 30 | Dinlenme suresi (saniye) |
| Pulse Current (A) | 1.0 | Desarj akimi |

**Kullanim:**
1. Parametreleri ayarlayin
2. "Run Pulse Test" butonuna tiklayin
3. Onay penceresinde toplam test suresi gosterilir
4. Test arkaplanda calisir, buton deaktif olur
5. Tamamlandiginda sonuc penceresi goruntulenir

**Onemli Notlar:**
- Test otomatik olarak Battery Test moduna gecer
- Keithley 2281S, Battery Test modunda yaklasik 1A desarj akimi uygular (cihaz sinirlamasi)
- USB baglantisi gereklidir (Ethernet uzerinden calismaz)

**Cikti Dosyalari:**
- `logs/pulse_bt_YYYYMMDD_HHMMSS.csv` (puls verileri)
- `logs/rest_evoc_YYYYMMDD_HHMMSS.csv` (dinlenme verileri)

### 3.5 Battery Model Generation (Batarya Model Olusturma)

Tam desarj ve sarj dongusuyle batarya modeli olusturur. Bu model daha sonra Battery Simulator modunda kullanilabilir.

**Parametreler:**

| Parametre | Varsayilan | Aciklama |
|-----------|-----------|----------|
| Discharge End Voltage (V) | 3.0 | Desarjin durdurulacagi gerilim |
| Discharge End Current (A) | 0.4 | Desarjin durdurulacagi akim |
| Charge Full Voltage (V) | 4.20 | Hedef sarj gerilimi |
| Charge Current Limit (A) | 1.0 | Maksimum sarj akimi |
| Charge End Current (A) | 0.05 | Sarjin tamamlanma akimi (C/20) |
| ESR Interval (s) | 30 | ESR olcum araligi |
| Model Slot (1-9) | 4 | Cihaz hafiza yuvasi |
| Model V-min (V) | 2.5 | Model gerilim alt siniri |
| Model V-max (V) | 4.2 | Model gerilim ust siniri |

**UYARI:** Bu test saatler surer! Batarya tamamen desarj edilip tekrar sarj edilir. Test suresinin tahmini, onay penceresinde gosterilir.

**Cikti Dosyalari:**
- `logs/battery_model_data_YYYYMMDD_HHMMSS.csv` (test verileri)
- `battery_model_slot_X.csv` (model dosyasi, "Export model to CSV" secenegi aciksa)

### 3.6 Current Profile (Akim Profili)

CSV veya Excel dosyasindan okunan akim profiline gore otomatik mod gecisi yaparak sarj/desarj islemleri gerceklestirir.

**Parametreler:**

| Parametre | Varsayilan | Aciklama |
|-----------|-----------|----------|
| Profile File | - | CSV veya Excel profil dosyasi |
| Discharge Current (A) | 1.0 | Negatif segmentler icin desarj akimi |
| Charge Voltage (V) | 4.2 | Pozitif segmentler icin sarj gerilimi |
| Sample Period (s) | 1.0 | Olcum araligi |

**Kullanim:**
1. "Browse" ile profil dosyasini secin (secmeden once format bilgisi gosterilir)
2. Parametreleri ayarlayin
3. "Run Current Profile" butonuna tiklayin
4. Tahmini sure onay penceresinde gorunur
5. Test arkaplanda calisir

**Otomatik Mod Gecisi:**
- Pozitif akim degerleri: Power Supply moduna gecis (sarj)
- Negatif akim degerleri: Battery Test moduna gecis (desarj)

**Onemli:** USB baglantisi gereklidir. Ethernet baglantisi uzerinden profil calistirma desteklenmez.

**Cikti Dosyasi:** `logs/keithley_log_YYYYMMDD_HHMMSS.csv`

---

## 4. Sorensen SGX400-12D - DC Guc Kaynagi

Sorensen sekmesi, yuksek guclu DC guc kaynagi kontrolu saglar.

### 4.1 Parametreler

| Parametre | Aralik | Aciklama |
|-----------|--------|----------|
| Voltage (V) | 0 - 400 | Cikis gerilimi |
| Current (A) | 0 - 12 | Akim limiti |
| OVP (V) | 0 - 400 | Asiri Gerilim Korumasi (Over-Voltage Protection) |
| OCP (A) | 0 - 12 | Asiri Akim Korumasi (Over-Current Protection) |

### 4.2 Temel Islemler

**Set Parameters:**
- Gerilim, akim, OVP ve OCP degerlerini girin
- "Set Parameters" ile tum ayarlari cihaza gonderin

**Output ON:**
- Guvenlik kontrolleri:
  - OVP degeri, ayarlanan gerilimden buyuk olmalidir
  - OCP degeri, ayarlanan akimdan buyuk veya esit olmalidir
  - Guc limiti: V x I <= 4800W
  - Gerilim ve akim aralik kontrolu
- Cihaz limitlerinin %80'ine yaklasan degerlerde uyari cikar

**Output OFF:**
- Cikisi guvenli sekilde kapatir
- Parametreler cihazda korunur

### 4.3 Koruma Ayarlari

- **OVP:** Yukun asiri gerilimden korunmasi icin ayarlayin. Hedef gerilimin %10-20 ustune ayarlanmasi onerilir.
- **OCP:** Guc kaynaginin asiri akim cekiminden korunmasi icin ayarlayin. Beklenen maksimum akimin biraz ustune ayarlayin.

### 4.4 Veri Kaydi

Sorensen'de otomatik test fonksiyonu yoktur. Olcum verileri icin "Monitoring & Logging" sekmesini kullanin:
1. Cihazi baglayin ve parametreleri ayarlayin
2. Output ON yapin
3. "Monitoring & Logging" sekmesine gecin
4. "Start Monitoring" ile veri toplamaya baslayin
5. Testinizi tamamlayin
6. "Save Data" ile verileri kaydedin

---

## 5. Prodigit 34205A - Elektronik Yuk

Prodigit sekmesi, elektronik yuk kontrolu ve CC profil testi saglar.

### 5.1 Calisma Modlari

| Mod | Aciklama | Parametre | Kullanim |
|-----|----------|-----------|----------|
| CC | Sabit Akim | Akim (A, maks 160) | Batarya desarj, guc kaynagi yuk testi |
| CV | Sabit Gerilim | Gerilim (V, maks 600) | Gerilim regulasyon testi |
| CP | Sabit Guc | Guc (W, maks 5000) | Sabit guc altinda guc kaynagi testi |
| CR | Sabit Direnc | Direnc (Ohm, maks 1 MOhm) | Rezistif yuk simulasyonu |

### 5.2 Temel Islemler

**Set Parameters:**
- Mod secin (CC, CV, CP veya CR)
- Secilen moda gore degeri girin
- "Set Parameters" ile cihaza gonderin
- Profil calisirken parametre degistirilemez

**Load ON:**
- Secilen mod ve degerle yuku aktif eder
- Guvenlik kontrolleri:
  - Sifir deger ile yuk aktif edilemez
  - Her mod icin cihaz limitleri kontrol edilir
  - Cihaz limitlerinin %80'inde uyari gosterilir
- LED gostergesi yesile doner
- Gercek zamanli olcumler (gerilim, akim, guc) sekmede gosterilir

**Load OFF:**
- Yuku guvenli sekilde kapatir
- Profil calisirken bile calisir (acil durdurma icin)

### 5.3 CC Profile (Sabit Akim Profili)

CSV dosyasindan okunan akim profilini otomatik olarak calistirir.

**Kullanim:**
1. "Browse" ile profil dosyasini secin (CSV veya Excel)
2. Ornekleme periyodunu ayarlayin (varsayilan: 1.0 saniye, aralik: 0 - 60 saniye)
3. "Load Profile" ile dosyayi yukleyin ve dogrulayin
4. Ozet bilgileri kontrol edin: segment sayisi, toplam sure, akim araligi
5. "Start" ile profili baslatim
6. Gerekirse "Stop" ile durdurun

**Cikti Formati:** Profile baslatilamdan once CSV, Excel veya Both seceneklerinden birini secin.

**Cikti Dosyasi:** `logs/prodigit_cc_profile_YYYYMMDD_HHMMSS.csv` (ve/veya `.xlsx`)

**Not:** Prodigit profilleri yalnizca negatif olmayan (0 veya pozitif) akim degerleri destekler. Negatif akim degerleri Prodigit'te kullanilamaz.

---

## 6. Profil Dosyasi Formatlari

Hem Keithley hem de Prodigit icin profil dosyalari ayni formati kullanir. CSV (.csv) ve Excel (.xlsx) desteklenir.

### CSV Formati

```csv
time_s,current_a
0,2.0
20,2.5
40,-1.0
60,-0.8
90,0.7
```

### Sutun Aciklamalari

| Sutun | Aciklama |
|-------|----------|
| `time_s` | Segmentin baslangic zamani (saniye cinsinden) |
| `current_a` | Akim degeri (Amper cinsinden) |

### Akim Degerleri

**Keithley icin:**
- Pozitif degerler: Sarj islemi (Power Supply moduna gecis)
- Negatif degerler: Desarj islemi (Battery Test moduna gecis)
- Sifir: Bekleme

**Prodigit icin:**
- Yalnizca sifir veya pozitif degerler desteklenir
- Negatif degerler kullanilamaz

### Sure Hesaplamasi

- Her segmentin suresi, bir sonraki segmentin `time_s` degerinden cikarilarak hesaplanir
- Son segmentin suresi, onceki segmentlerin ortalama suresi olarak belirlenir
- Ornek: `time_s` degerleri 0, 20, 40, 60 olan bir profilde segmentler 20'ser saniyedir

### Ornek Profil: Sarj/Desarj Dongusu

```csv
time_s,current_a
0,-2.0
60,-1.5
120,-1.0
180,0.0
240,1.0
300,1.5
360,2.0
420,0.0
480,-1.5
540,-2.0
600,0.0
```

Bu profil 600 saniye surer ve desarj/bekleme/sarj/bekleme/desarj dongusu uygulanir.

### Performans Notu

- CSV dosyalari Excel dosyalarina gore yaklasik 4 kat daha hizli yuklenir
- 10.000 satirdan buyuk profiller icin CSV formati onerilir

---

## 7. Monitoring & Logging Sekmesi

Bu sekme, tum bagli cihazlardan gercek zamanli olcum toplama ve kaydetme imkani saglar.

### 7.1 Ornekleme Hizlari

Sistem iki bagimsiz hiz ayari kullanir:

| Ayar | Aciklama | Minimum | Varsayilan |
|------|----------|---------|------------|
| Data Sampling Rate | Cihazdan olcum alma sikligi | 0.2 saniye (5 Hz) | 1.0 saniye |
| GUI Update Rate | Ekran yenileme sikligi | 0.1 saniye | 1.0 saniye |

### 7.2 Hazir Ayarlar (Presets)

| Preset | Data Sampling | GUI Update | Kullanim |
|--------|--------------|------------|----------|
| Slow (5s) | 5.0 saniye | 2.0 saniye | Uzun sureli testler, dusuk veri hacmi |
| Standard (1s) | 1.0 saniye | 1.0 saniye | Genel kullanim |
| Fast (0.5s) | 0.5 saniye | 0.5 saniye | Hizli degisim izleme |
| Maximum (0.2s) | 0.2 saniye | 1.0 saniye | En yuksek cozunurluk (cihaz limiti) |

### 7.3 Kontrol Butonlari

| Buton | Islem |
|-------|-------|
| Start Monitoring | Veri toplamaya baslar. Hizlar kilitlenir. |
| Stop Monitoring | Veri toplamayai durdurur. Hizlar tekrar duzenlenebilir. |
| Save Data | Toplanan verileri dosyaya kaydeder. Format secimi penceresi cikar (Excel / CSV / Both). |
| Clear Data | Tum toplanan verileri ve ekran gosterimini siler. |
| Refresh Devices | Bagli cihazlari yeniden tarar ve listeye ekler. |
| Plot Data | Toplanan verilerin grafiklerini yeni bir pencerede acar (matplotlib gerektirir). |

### 7.4 Gercek Zamanli Olcumler

Her bagli cihaz icin ayri bir panel gorunur:
- **Voltage:** Anlik gerilim (V)
- **Current:** Anlik akim (A)
- **Power:** Anlik guc (W)
- **Mode:** Cihazin aktif modu

### 7.5 [BUSY] Gostergesi

Bir cihaz test fonksiyonu calistirirken (Pulse Test, Battery Model, Current Profile, CC Profile), Monitoring sekmesinde o cihaz icin **[BUSY]** veya bos (NULL/--) degerler gorunur. Bu **normal bir davranistir**.

Nedeni: Test fonksiyonlari cihazla surekli iletisim halindedir ve monitoring ayni anda cihaza erisemez.

Bu durumda yapilmasi gereken:
- Test fonksiyonlari kendi log dosyalarini `logs/` klasorune otomatik olarak olusturur
- Test tamamlandiktan sonra `logs/` klasorunu kontrol edin
- Monitoring sekmesi yalnizca manuel islemler (Set Parameters, Output ON/OFF) icin veri kaydi amacli kullanin

---

## 8. Veri Kaydetme

### 8.1 Otomatik Log Dosyalari (Test Fonksiyonlari)

Test fonksiyonlari calistirildiginda `logs/` klasorune otomatik olarak log dosyasi olusturulur:

| Test | Cikti Dosyalari |
|------|----------------|
| Keithley Pulse Test | `logs/pulse_bt_YYYYMMDD_HHMMSS.csv`, `logs/rest_evoc_YYYYMMDD_HHMMSS.csv` |
| Keithley Battery Model | `logs/battery_model_data_YYYYMMDD_HHMMSS.csv` |
| Keithley Current Profile | `logs/keithley_log_YYYYMMDD_HHMMSS.csv` |
| Prodigit CC Profile | `logs/prodigit_cc_profile_YYYYMMDD_HHMMSS.csv` |

Dosya isimlendirmesi: `{cihaz}_{test}_{YYYYMMDD_HHMMSS}.csv`

Zaman damgasi, testin basladigi ani gosterir.

### 8.2 Manuel Veri Kaydi (Monitoring)

Monitoring sekmesindeki "Save Data" butonu ile toplanan veriler kaydedilir:
1. "Save Data" butonuna tiklayin
2. Format secim penceresi cikar:
   - **Yes** = Excel (.xlsx)
   - **No** = CSV (.csv)
   - **Cancel** = Her iki format
3. Dosya adini ve konumunu secin

### 8.3 Dosya Formatlari

| Format | Avantaj | Dezavantaj |
|--------|---------|-----------|
| CSV (.csv) | Hizli, evrensel uyumluluk, kucuk dosya boyutu | Bicimlendirme yok |
| Excel (.xlsx) | Bicimlendirme, grafik, filtreleme | openpyxl gerektirir, daha yavas |

---

## 9. Debug Console Sekmesi

Uygulamanin son sekmesi olan "Debug Console", uygulama loglarini gercek zamanli olarak gosterir. Baglanti sorunlari, komut hatalari ve genel uygulama durumunu izlemek icin faydalidir. Sorun giderme sirasinda bu sekmeyi kontrol edin.

---

## 10. Uygulama Kapatma

Pencere kapatildiginda asagidaki islemler otomatik olarak gerceklestirilir:

1. Debug console durdurulur
2. Monitoring durdurulur
3. Calisanlar test thread'lerinin tamamlanmasi beklenir (3 saniye zaman asimi)
4. Tum bagli cihazlarin ciktilari kapatilir
5. Tum baglantiliar guvenli sekilde sonlandirilir

Bu nedenle uygulamayi kapatmadan once devam eden testlerin tamamlanmasini beklemeniz onerilir.

---

## 11. Sik Karsilasilan Sorunlar

| Sorun | Olasi Neden | Cozum |
|-------|-------------|-------|
| "PyVISA not available" | PyVISA kurulu degil | Sadece RS232/Ethernet kullanilacaksa sorun degildir. USB/GPIB icin `pip install pyvisa pyvisa-py` |
| Baglanti basarisiz | Yanlis port/IP/baud rate | Baglanti ayarlarini kontrol edin, kablo baglantilarini dogrulayin |
| Output ON basarisiz | Guc limiti asimi | V x I degerinin cihaz guc limitini asmamasi gerekir |
| Monitoring [BUSY] | Test fonksiyonu calisiyor | Normaldir. Test log dosyalarini `logs/` klasorunde kontrol edin |
| Profil yuklenemiyor | Hatali CSV formati | Sutun basliklarinin `time_s,current_a` oldugunu dogrulayin |
| Pulse Test calismiyeor | Ethernet baglantisi | Pulse Test ve Current Profile icin USB baglantisi gereklidir |
| Excel kayit hatasi | openpyxl eksik | `pip install openpyxl` |
| OVP/OCP hatasi (Sorensen) | Koruma degerleri cok dusuk | OVP > ayarlanan gerilim, OCP >= ayarlanan akim olmalidir |

---

## 12. Hizli Baslangic Rehberi

### Senaryo 1: Keithley ile Batarya Desarj Testi

1. Keithley sekmesine gecin
2. USB ile baglanin
3. Mod: "Battery Test" secin
4. Gerilim ve akim degerlerini girin
5. "Set Parameters & Mode" tiklayin
6. Pulse Test parametrelerini ayarlayin
7. "Run Pulse Test" tiklayin
8. Test tamamlandiginda `logs/` klasorunu kontrol edin

### Senaryo 2: Sorensen ile Sabit Gerilim Testi

1. Sorensen sekmesine gecin
2. RS232 veya Ethernet ile baglanin
3. Gerilim, akim, OVP, OCP degerlerini girin
4. "Set Parameters" tiklayin
5. "Output ON" tiklayin
6. "Monitoring & Logging" sekmesine gecin
7. "Start Monitoring" tiklayin
8. Test bitince "Save Data" ile kaydedin

### Senaryo 3: Prodigit ile CC Profil Testi

1. Prodigit sekmesine gecin
2. RS232 veya USB ile baglanin
3. "CSV CC Profile" bolumunde "Browse" ile profil dosyasi secin
4. "Load Profile" ile dogrulayin
5. Ozet bilgilerini kontrol edin
6. Cikti formatini secin (CSV/Excel/Both)
7. "Start" ile profili baslatim
8. Test tamamlandiginda `logs/` klasorunu kontrol edin

### Senaryo 4: Keithley ile Akim Profili (Sarj/Desarj Dongusu)

1. Keithley sekmesine gecin
2. USB ile baglanin
3. Profil dosyasini secin (pozitif=sarj, negatif=desarj)
4. Charge Voltage ve Discharge Current degerlerini ayarlayin
5. Cikti formatini secin
6. "Run Current Profile" tiklayin
7. Cihaz otomatik olarak modlar arasinda gecer
8. Test tamamlandiginda `logs/` klasorunu kontrol edin
