# 🚨 Risk Analizi: Tespit Edilen Sorunların Gerçek Senaryolardaki Etkileri

**Tarih:** 2025-12-19  
**Amaç:** Her sorunun ne zaman, nasıl ve hangi durumlarda sıkıntı çıkarabileceğini detaylı açıklamak

---

## 🔴 KRİTİK SORUNLAR - GERÇEK SENARYOLAR

### 1. Thread Safety: `busy` Flag Race Condition

#### ❌ Ne Zaman Sorun Çıkarır?

**Senaryo 1: Test Başlatma Sırasında Monitoring Devam Ediyor**
```
Timeline:
T0: Kullanıcı "Run Pulse Test" butonuna basar
T1: GUI thread: controller.set_busy(True) çağrılır
T2: [RACE CONDITION] Monitoring thread: controller.is_busy() okur → False döner (henüz yazılmamış!)
T3: Monitoring thread: controller.get_measurements() çağrılır
T4: Test thread: controller.send_command(':BATT:OUTP ON') çağrılır
T5: [ÇAKIŞMA] İki thread aynı anda cihaza komut gönderir!
```

**Sonuç:**
- ❌ Cihaz komutları karışır
- ❌ Veri bozulması (önceki CSV sorunu gibi)
- ❌ Test başarısız olur
- ❌ Cihaz beklenmeyen duruma girebilir

**Ne Zaman Görülür?**
- Hızlı tıklamalarda (kullanıcı test butonuna basar, monitoring hala çalışıyor)
- Yüksek CPU yükünde (thread scheduling gecikmeleri)
- Çoklu cihaz monitoring'inde (birden fazla cihaz aynı anda test edilirken)

---

**Senaryo 2: Test Biterken Monitoring Başlıyor**
```
Timeline:
T0: Test thread: controller.set_busy(False) çağrılır
T1: [RACE CONDITION] Monitoring thread: controller.is_busy() okur → True döner (henüz False yazılmamış!)
T2: Monitoring thread: "Device busy, skipping" der
T3: Test thread: Cleanup yapar (output OFF)
T4: Monitoring thread: Tekrar is_busy() okur → False döner
T5: Monitoring thread: get_measurements() çağrılır
T6: [ÇAKIŞMA] Test cleanup devam ederken monitoring başlar!
```

**Sonuç:**
- ❌ Cleanup sırasında ölçüm yapılır (yanlış veri)
- ❌ Cihaz durumu belirsiz kalır
- ❌ Monitoring verileri güvenilmez olur

---

**Senaryo 3: İki Test Aynı Anda Başlatılmaya Çalışılıyor**
```
Timeline:
T0: Kullanıcı "Run Pulse Test" butonuna basar
T1: Thread 1: if controller.busy: → False (henüz set edilmemiş)
T2: Kullanıcı hızlıca "Run Current Profile" butonuna basar
T3: Thread 2: if controller.busy: → False (henüz set edilmemiş)
T4: Thread 1: controller.set_busy(True)
T5: Thread 2: controller.set_busy(True)
T6: [ÇAKIŞMA] İki test aynı anda çalışır!
```

**Sonuç:**
- ❌ İki test aynı anda çalışır
- ❌ Cihaz komutları karışır
- ❌ Veri bozulması
- ❌ Test sonuçları geçersiz olur
- ❌ Cihaz beklenmeyen duruma girebilir (güvenlik riski!)

---

### 2. Exception Handling: Bare `except:` Kullanımları

#### ❌ Ne Zaman Sorun Çıkarır?

**Senaryo 1: Ctrl+C ile Uygulama Kapatılamıyor**
```python
# gui/controllers/base_controller.py:84
def identify(self):
    try:
        identify_cmd = self.device_spec.default_commands.get('identify', '*IDN?')
        self.model = self.interface.query(identify_cmd)
    except:  # ❌ KeyboardInterrupt'ı da yakalar!
        self.model = "Unknown"
```

**Gerçek Durum:**
- Kullanıcı Ctrl+C ile uygulamayı kapatmaya çalışır
- `KeyboardInterrupt` exception'ı yakalanır
- Uygulama kapanmaz, donar
- Cihaz bağlantıları açık kalır (güvenlik riski!)

---

**Senaryo 2: Test Sırasında Recovery Başarısız Oluyor**
```python
# gui/controllers/keithley/tests/profile_runner.py:237
def _recovery(self):
    try:
        self.controller.send_command('*RST')
        # ...
    except:  # ❌ Tüm exception'ları yakalar
        print("Device recovery failed")
```

**Gerçek Durum:**
- Test sırasında cihaz hata verir
- Recovery fonksiyonu çağrılır
- Recovery sırasında `SystemExit` veya `KeyboardInterrupt` oluşursa yakalanır
- Recovery sessizce başarısız olur
- Cihaz hatalı durumda kalır
- Kullanıcı hatayı fark etmez (güvenlik riski!)

---

**Senaryo 3: Sorensen Ölçüm Hataları Gizleniyor**
```python
# gui/controllers/sorensen_controller.py:97
def measure_voltage(self) -> Optional[float]:
    try:
        cmd = self.device_spec.default_commands['measure_voltage']
        response = self.query_command(cmd)
        return float(response)
    except:  # ❌ Tüm exception'ları yakalar
        return None
```

**Gerçek Durum:**
- Cihaz bağlantısı kopar
- `ConnectionError` oluşur
- Exception yakalanır, `None` döner
- Kullanıcı cihazın bağlantısının koptuğunu fark etmez
- GUI'da "Voltage: -- V" görünür (normal gibi)
- Kullanıcı yanlış veriyle çalışmaya devam eder

---

### 3. Memory Leak: `measurement_data` Sınırsız Büyüme

#### ❌ Ne Zaman Sorun Çıkarır?

**Senaryo 1: Uzun Süreli Monitoring (1 Saat)**
```
Örnek: 1 saniye örnekleme ile 1 saat monitoring
- 3600 ölçüm × 3 cihaz = 10,800 data point
- Her data point ~200 bytes = 2.16 MB
- 10 saat = 21.6 MB
- 100 saat = 216 MB
- 1000 saat = 2.16 GB (sistem çöker!)
```

**Gerçek Durum:**
- Kullanıcı gece boyunca monitoring yapar (8 saat)
- Sabah uygulama çok yavaşlar
- Memory kullanımı 500MB+ olur
- Sistem swap kullanmaya başlar
- Uygulama donar veya çöker
- Veri kaybı olur

---

**Senaryo 2: Çoklu Cihaz Monitoring**
```
3 cihaz × 1 saniye örnekleme × 24 saat = 259,200 data point
Her data point: timestamp + 3 cihaz × (voltage, current, power, mode) = ~500 bytes
Toplam: 259,200 × 500 bytes = 129.6 MB (sadece measurement_data!)
```

**Gerçek Durum:**
- 3 cihaz aynı anda monitoring'de
- 24 saat sonra memory kullanımı 200MB+
- Sistem yavaşlar
- CSV/Excel kaydetme çok uzun sürer (dosya işleme)
- Kullanıcı veri kaydedemez (timeout)

---

**Senaryo 3: Monitoring + Test Aynı Anda**
```
Monitoring thread: Her saniye measurement_data.append()
Test thread: Profil çalıştırıyor, log dosyası yazıyor
GUI thread: CSV/Excel kaydetme işlemi başlatıyor
```

**Gerçek Durum:**
- Memory kullanımı hızla artar
- Garbage collection sık çalışır (performans düşer)
- Disk I/O yavaşlar (swap kullanımı)
- Uygulama donar
- Kullanıcı veri kaybeder

---

## 🟡 ORTA SEVİYE SORUNLAR - GERÇEK SENARYOLAR

### 4. Thread Cleanup: Daemon Thread'ler Join Edilmiyor

#### ❌ Ne Zaman Sorun Çıkarır?

**Senaryo 1: Uygulama Kapanırken Test Devam Ediyor**
```
Timeline:
T0: Kullanıcı uygulamayı kapatır (X butonuna basar)
T1: on_closing() çağrılır
T2: Test thread hala çalışıyor (daemon=True, join() yok)
T3: Uygulama kapanır
T4: Test thread yarıda kesilir
T5: finally bloğu çalışmaz
T6: Cihaz output açık kalır! (GÜVENLİK RİSKİ!)
```

**Sonuç:**
- ❌ Cihaz output açık kalır
- ❌ Test verileri kaybolur
- ❌ Log dosyası yarıda kesilir
- ❌ Cihaz beklenmeyen durumda kalır

---

**Senaryo 2: Test Biterken Uygulama Kapanıyor**
```
Timeline:
T0: Test tamamlanmak üzere (son segment)
T1: Kullanıcı uygulamayı kapatır
T2: Test thread: log dosyasını yazıyor
T3: Uygulama kapanır
T4: Dosya yazma yarıda kesilir
T5: Log dosyası bozuk olur
```

**Sonuç:**
- ❌ Log dosyası bozuk/eksik olur
- ❌ Veri kaybı
- ❌ Test sonuçları geçersiz

---

### 5. Prodigit Buffer Clearing: Standalone Query'lerde Eksik

#### ❌ Ne Zaman Sorun Çıkarır?

**Senaryo 1: GUI Tab'de Status Güncelleme**
```
Timeline:
T0: Monitoring: get_measurements() → buffer temizlenir
T1: Monitoring: MEAS:VOLT? → "29.84" döner
T2: Monitoring: MEAS:CURR? → "2.001" döner
T3: Monitoring: MEAS:POW? → "59.71" döner
T4: GUI Tab: _update_status() çağrılır
T5: GUI Tab: query_mode() → buffer temizlenmez!
T6: GUI Tab: query_mode() → "CC" yerine "59.71" döner! (önceki yanıt)
```

**Sonuç:**
- ❌ GUI'da yanlış mode gösterilir
- ❌ Kullanıcı yanlış bilgi görür
- ❌ Karar verme hataları

---

**Senaryo 2: Monitoring + GUI Tab Aynı Anda**
```
Timeline:
T0: Monitoring thread: get_measurements() → buffer temizlenir
T1: Monitoring thread: MEAS:VOLT? gönderir
T2: GUI Tab thread: query_load_status() → buffer temizlenmez!
T3: GUI Tab thread: query_load_status() → "29.84" döner! (voltage yanıtı)
T4: Monitoring thread: MEAS:VOLT? yanıtını okur → "ON" döner! (load status yanıtı)
```

**Sonuç:**
- ❌ Veri karışması (önceki CSV sorunu gibi)
- ❌ GUI'da yanlış bilgi
- ❌ Monitoring verileri yanlış

---

### 6. Direct `busy` Attribute Access

#### ❌ Ne Zaman Sorun Çıkarır?

**Senaryo: Test Başlatma Kontrolü**
```python
# gui/controllers/keithley/tests/profile_runner.py:77
if self.controller.busy:  # ❌ Thread-safe değil
    raise Exception("Device is busy")
```

**Gerçek Durum:**
- Test başlatılırken `busy` kontrolü yapılır
- Aynı anda monitoring thread `busy` flag'ini değiştiriyor
- Race condition: Test başlar ama cihaz aslında busy
- İki işlem aynı anda çalışır
- Veri bozulması

---

### 7. Queue Overflow Risk

#### ❌ Ne Zaman Sorun Çıkarır?

**Senaryo: Yavaş GUI Update + Hızlı Monitoring**
```
Timeline:
T0: Monitoring thread: Her 0.2 saniyede data_queue.put()
T1: GUI thread: Her 1 saniyede get_new_data() çağrılır
T2: Queue hızla dolar (5× daha hızlı ekleme)
T3: Memory kullanımı artar
T4: Queue 10,000+ item olur
T5: Memory 50MB+ olur
T6: Sistem yavaşlar
```

**Sonuç:**
- ❌ Memory kullanımı artar
- ❌ Uygulama yavaşlar
- ❌ GUI donar
- ❌ Veri kaybı (queue overflow)

---

## 🟢 DÜŞÜK SEVİYE SORUNLAR - GERÇEK SENARYOLAR

### 8. Callback Listesi Temizlenmiyor

#### ❌ Ne Zaman Sorun Çıkarır?

**Senaryo: Uzun Süreli Kullanım**
```
- Her monitoring başlatıldığında callback eklenir
- Monitoring durdurulduğunda callback silinmez
- 100 kez monitoring başlat/durdur = 100 callback
- Her callback memory kullanır
- Memory leak (küçük ama birikir)
```

**Sonuç:**
- ❌ Küçük memory leak
- ❌ Uzun süreli kullanımda birikir
- ❌ Performans düşer

---

### 9. VISA Connection Cleanup

#### ❌ Ne Zaman Sorun Çıkarır?

**Senaryo: Çoklu Bağlantı/Kopma**
```
- Cihaz bağlanır → connection objesi oluşur
- Cihaz kopar → connection.close() çağrılır
- connection = None yapılmaz
- Eski connection objesi memory'de kalır
- 100 kez bağlan/kopar = 100 connection objesi
```

**Sonuç:**
- ❌ Küçük memory leak
- ❌ Uzun süreli kullanımda birikir
- ❌ Sistem kaynakları tükenir

---

## 📊 ÖZET: SORUN ÇIKMA İHTİMALLERİ

| Sorun | Ne Zaman | Sıklık | Etki | Güvenlik Riski |
|-------|----------|--------|------|----------------|
| `busy` flag race condition | Test başlatma/kapanma | **Yüksek** | Veri bozulması, test başarısızlığı | ⚠️ **Yüksek** (cihaz açık kalabilir) |
| Bare `except:` | Ctrl+C, recovery | Orta | Uygulama donması, hata gizleme | ⚠️ **Yüksek** (cihaz kontrolü kaybı) |
| Memory leak | Uzun monitoring | **Yüksek** | Sistem çökmesi, veri kaybı | ⚠️ Orta |
| Thread cleanup | Uygulama kapanma | Orta | Cihaz açık kalma | ⚠️ **Yüksek** |
| Buffer clearing | GUI + monitoring | Orta | Veri bozulması | ⚠️ Düşük |
| Direct `busy` access | Test başlatma | Düşük | Race condition | ⚠️ Orta |
| Queue overflow | Yavaş GUI | Düşük | Memory artışı | ⚠️ Düşük |

---

## 🎯 EN KRİTİK SENARYOLAR (Öncelik Sırasıyla)

### 1. 🔴 Test Başlatma Sırasında Monitoring Devam Ediyor
**Risk:** Yüksek  
**Etki:** Veri bozulması, test başarısızlığı, cihaz güvenliği  
**Çözüm:** `busy` flag için thread lock

### 2. 🔴 Uygulama Kapanırken Cihaz Açık Kalıyor
**Risk:** Yüksek  
**Etki:** Güvenlik riski, cihaz hasarı  
**Çözüm:** Thread cleanup, join() mekanizması

### 3. 🔴 Uzun Monitoring'de Memory Tükeniyor
**Risk:** Yüksek  
**Etki:** Sistem çökmesi, veri kaybı  
**Çözüm:** `measurement_data` limiti

### 4. 🟡 Ctrl+C ile Uygulama Kapatılamıyor
**Risk:** Orta  
**Etki:** Kullanıcı deneyimi, güvenlik  
**Çözüm:** Bare `except:` → `except Exception:`

### 5. 🟡 GUI Tab'de Yanlış Status Gösteriliyor
**Risk:** Orta  
**Etki:** Yanlış bilgi, karar verme hataları  
**Çözüm:** Standalone query'lerde buffer clearing

---

## 💡 SONUÇ

**En Tehlikeli Senaryo:** Test başlatılırken monitoring devam ediyor → Cihaz komutları karışıyor → Veri bozulması → Test başarısız → Cihaz beklenmeyen durumda kalıyor (GÜVENLİK RİSKİ!)

**En Sık Görülen:** Memory leak → Uzun monitoring → Sistem yavaşlar → Uygulama çöker

**En Kritik:** Thread safety sorunları → Race condition → Veri bozulması → Test güvenilirliği kaybı

**Öneri:** Öncelikle thread safety sorunlarını (1, 4, 12) düzelt, sonra memory leak'i (3, 13) çöz.

