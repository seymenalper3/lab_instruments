# GUI Güvenlik Denetimi Raporu

**Tarih**: 2025-01-20  
**Kapsam**: Lab Instruments GUI - Güvenlik Açıkları Analizi  
**Manueller**: Prodigit 34000A Series, Sorensen SGX400, Keithley 2281S

---

## Özet

Bu rapor, lab cihazları manuellerindeki güvenlik uyarılarına göre GUI kodunda tespit edilen güvenlik açıklarını ve eksiklikleri içermektedir. Toplam **12 kritik/yüksek öncelikli** ve **8 orta/düşük öncelikli** güvenlik sorunu tespit edilmiştir.

---

## Manuel Güvenlik Uyarıları (Referans)

Manuellerden çıkarılan temel güvenlik uyarıları:

1. **DO NOT EXCEED INPUT RATINGS** - Limit aşımı kesinlikle yasak
2. **GROUND THE INSTRUMENT** - Topraklama zorunlu
3. **FUSES** - Doğru tip sigorta kullanılmalı
4. **DO NOT OPERATE IN EXPLOSIVE ATMOSPHERE** - Patlayıcı ortamda kullanılmamalı
5. **KEEP AWAY FROM LIVE CIRCUITS** - Canlı devrelere dokunulmamalı
6. **Output açılmadan önce koruma ayarları yapılmalı**

---

## Kritik Öncelikli Güvenlik Sorunları

### 1. ⚠️ **KRİTİK**: Sorensen - OVP Kontrolü Eksik

**Dosya**: `gui/gui/sorensen_tab.py:66-74`

**Sorun**: Output açılmadan önce OVP (Overvoltage Protection) değerinin set voltajından yüksek olduğu kontrol edilmiyor.

**Kod**:
```python
def output_on(self):
    """Turn output on"""
    def _output_on():
        self.controller.output_on()  # OVP kontrolü yok!
        return "Output turned ON"
```

**Risk**: OVP < Voltage durumunda output açılırsa, koruma hemen devreye girer ve cihaz güvenli olmayan duruma geçebilir.

**Öneri**: `output_on()` metodunda OVP > Voltage kontrolü eklenmeli:
```python
def output_on(self):
    def _output_on():
        voltage = float(self.voltage_entry.get())
        ovp = float(self.ovp_entry.get())
        if ovp <= voltage:
            raise ValueError(f"OVP ({ovp}V) must be greater than set voltage ({voltage}V)")
        self.controller.output_on()
        return "Output turned ON"
```

---

### 2. ⚠️ **KRİTİK**: Keithley - Voltage Protection Eksik

**Dosya**: `gui/gui/keithley_tab.py:217-225`

**Sorun**: Keithley'de Power Supply mode'da voltage protection ayarlanmıyor. Sadece `run_charge_segments()` içinde protection_voltage parametresi var.

**Kod**:
```python
def output_on(self):
    def _output_on():
        self.controller.output_on()  # Protection ayarlanmıyor!
        return "Output turned ON"
```

**Risk**: Yüksek voltajlarda koruma olmadan output açılması cihaz ve bağlı sistemler için tehlikeli.

**Öneri**: `set_parameters()` veya `output_on()` metodunda voltage protection ayarlanmalı:
```python
def set_parameters(self):
    # ... mevcut kod ...
    # Voltage protection ekle
    if hasattr(self.controller, 'set_voltage_protection'):
        protection_voltage = voltage * 1.1  # %10 margin
        self.controller.send_command(f':SOUR:VOLT:PROT {protection_voltage}')
```

---

### 3. ⚠️ **KRİTİK**: Prodigit - Load Açılmadan Önce Parametre Kontrolü Yok

**Dosya**: `gui/gui/prodigit_tab.py:128-140`

**Sorun**: Load açılmadan önce current/voltage/power değerlerinin ayarlanmış olduğu kontrol edilmiyor.

**Kod**:
```python
def load_on(self):
    def _task():
        self.controller.load_on()  # Parametre kontrolü yok!
        return "Load turned ON. Monitoring started."
```

**Risk**: Parametreler ayarlanmadan load açılırsa beklenmeyen akım/voltaj değerleri oluşabilir.

**Öneri**: Load açılmadan önce mode ve değer kontrolü:
```python
def load_on(self):
    def _task():
        mode = self.mode_combo.get()
        value = float(self.value_entry.get())
        if value == 0.0:
            raise ValueError("Cannot enable load with zero value. Set parameters first.")
        # Mode ve değeri ayarla
        if mode == "CC":
            self.controller.set_mode_cc()
            self.controller.set_current(value)
        # ... diğer modlar
        self.controller.load_on()
        return "Load turned ON. Monitoring started."
```

---

### 4. ⚠️ **KRİTİK**: Global Emergency Stop Mekanizması Yok

**Dosya**: `gui/gui/main_window.py`, `gui/gui/device_tab.py`

**Sorun**: Tüm cihazları anında kapatacak global emergency stop butonu yok.

**Risk**: Acil durumlarda tüm cihazları hızlıca kapatma imkanı yok.

**Öneri**: MainWindow'a global emergency stop butonu eklenmeli:
```python
# main_window.py
def create_emergency_stop(self):
    self.emergency_btn = tk.Button(
        self.toolbar,
        text="🛑 EMERGENCY STOP",
        bg="red",
        fg="white",
        font=("Arial", 12, "bold"),
        command=self.emergency_stop_all
    )
    self.emergency_btn.pack(side='right', padx=10)

def emergency_stop_all(self):
    """Turn off all device outputs immediately"""
    for tab in [self.keithley_tab, self.prodigit_tab, self.sorensen_tab]:
        if tab and tab.controller:
            try:
                if hasattr(tab.controller, 'output_off'):
                    tab.controller.output_off()
                if hasattr(tab.controller, 'load_off'):
                    tab.controller.load_off()
            except:
                pass
```

---

## Yüksek Öncelikli Güvenlik Sorunları

### 5. ⚠️ **YÜKSEK**: Output Açılmadan Önce Parametre Doğrulama Yok

**Dosyalar**: `gui/gui/sorensen_tab.py`, `gui/gui/keithley_tab.py`, `gui/gui/prodigit_tab.py`

**Sorun**: Output açılmadan önce parametrelerin geçerli aralıkta olduğu kontrol edilmiyor.

**Risk**: Geçersiz parametrelerle output açılabilir.

**Öneri**: Her `output_on()` metodunda parametre doğrulama:
```python
def output_on(self):
    def _output_on():
        # Parametreleri kontrol et
        voltage = float(self.voltage_entry.get())
        current = float(self.current_entry.get())
        
        if voltage < 0 or voltage > self.device_spec.max_voltage:
            raise ValueError(f"Voltage out of range: {voltage}V")
        if current < 0 or current > self.device_spec.max_current:
            raise ValueError(f"Current out of range: {current}A")
        
        self.controller.output_on()
        return "Output turned ON"
```

---

### 6. ⚠️ **YÜKSEK**: Exception Durumunda Output Kapatma Eksik

**Dosyalar**: `gui/controllers/keithley_controller.py`, `gui/controllers/sorensen_controller.py`

**Sorun**: Bazı exception handler'larda output kapatılmıyor.

**Kod Örneği**: `keithley_controller.py:91-95`
```python
except Exception as e:
    self.controller = None
    self.status_bar.config(text=f"Connection failed: {e}", style="Error.TLabel")
    messagebox.showerror("Connection Error", str(e))
    return False
    # Output kapatılmıyor!
```

**Öneri**: Exception handler'larda output kapatma:
```python
except Exception as e:
    try:
        if self.controller:
            self.controller.output_off()
    except:
        pass
    self.controller = None
    # ... hata mesajları
```

---

### 7. ⚠️ **YÜKSEK**: Power Limit Kontrolü Eksik

**Dosyalar**: `gui/controllers/keithley_controller.py`, `gui/controllers/sorensen_controller.py`

**Sorun**: Voltaj ve akım limitleri kontrol ediliyor ama güç limiti (V × I) kontrol edilmiyor.

**Kod**: `keithley_controller.py:26-42`
```python
def set_voltage(self, voltage: float):
    if voltage < 0 or voltage > self.device_spec.max_voltage:
        raise ValueError(...)
    # Power kontrolü yok!
```

**Öneri**: Power limit kontrolü ekle:
```python
def set_voltage(self, voltage: float):
    if voltage < 0 or voltage > self.device_spec.max_voltage:
        raise ValueError(...)
    
    # Mevcut akım değerini al ve güç kontrolü yap
    if hasattr(self, '_last_current'):
        power = voltage * self._last_current
        if self.device_spec.max_power and power > self.device_spec.max_power:
            raise ValueError(f"Power limit exceeded: {power}W > {self.device_spec.max_power}W")
```

---

### 8. ⚠️ **YÜKSEK**: Bağlantı Kesilirken Output Kontrolü Zayıf

**Dosya**: `gui/controllers/base_controller.py:35-49`

**Sorun**: `disconnect()` metodunda output kapatma try-except içinde ve hata durumunda sessizce geçiliyor.

**Kod**:
```python
def disconnect(self):
    try:
        if hasattr(self, 'output_off'):
            self.output_off()
    except:
        pass  # Hata durumunda sessizce geçiliyor
```

**Öneri**: Daha güvenli disconnect:
```python
def disconnect(self):
    output_closed = False
    for attempt in range(3):  # 3 deneme
        try:
            if hasattr(self, 'output_off'):
                self.output_off()
                output_closed = True
                break
        except Exception as e:
            if attempt == 2:  # Son deneme
                logger.error(f"Failed to turn off output during disconnect: {e}")
            time.sleep(0.1)
    
    # Local mode'a geç
    try:
        if hasattr(self, 'local_mode'):
            self.local_mode()
    except:
        pass
    
    self.interface.disconnect()
    self.connected = False
```

---

### 9. ⚠️ **YÜKSEK**: Sorensen - OCP (Overcurrent Protection) Eksik

**Dosya**: `gui/controllers/sorensen_controller.py`

**Sorun**: Sorensen controller'da OCP ayarlama metodu yok.

**Risk**: Aşırı akım koruması olmadan çalışma riski.

**Öneri**: OCP metodu ekle:
```python
def set_ocp(self, ocp_current: float):
    """Set overcurrent protection"""
    if ocp_current < 0 or ocp_current > self.device_spec.max_current:
        raise ValueError(f"OCP current must be between 0 and {self.device_spec.max_current}A")
    
    cmd = 'SOUR:CURR:PROT {}'.format(ocp_current)
    self.send_command(cmd)
```

---

## Orta Öncelikli Güvenlik Sorunları

### 10. ⚠️ **ORTA**: Keithley - Mode Switch Sırasında Output Kontrolü

**Dosya**: `gui/controllers/keithley_controller.py:96-153`

**Sorun**: Mode switch sırasında output kapatılıyor ama başarısız olursa kontrol yok.

**Öneri**: Mode switch sonrası output durumunu kontrol et.

---

### 11. ⚠️ **ORTA**: Prodigit - Profile Çalışırken Manuel Kontrol Engellenmeli

**Dosya**: `gui/gui/prodigit_tab.py:327-369`

**Sorun**: Profile çalışırken UI disable ediliyor ama controller seviyesinde kontrol yok.

**Öneri**: Controller'da `is_busy()` kontrolü daha sıkı yapılmalı.

---

### 12. ⚠️ **ORTA**: Cihaz Hata Mesajları Kontrol Edilmiyor

**Dosyalar**: Tüm controller'lar

**Sorun**: Cihazdan gelen hata mesajları (`SYST:ERR?`) düzenli kontrol edilmiyor.

**Öneri**: Her komut sonrası hata kontrolü:
```python
def send_command(self, command: str):
    if not self.connected:
        raise Exception("Device not connected")
    self.interface.write(command)
    # Hata kontrolü ekle
    self._check_device_errors()

def _check_device_errors(self):
    try:
        error = self.query_command('SYST:ERR?')
        if error and '0,' not in error:
            raise Exception(f"Device error: {error}")
    except:
        pass  # Hata kontrolü başarısız olursa devam et
```

---

### 13. ⚠️ **ORTA**: Timeout Durumunda Güvenli Duruma Geçiş

**Dosyalar**: `gui/interfaces/ethernet_interface.py`, `gui/interfaces/serial_interface.py`

**Sorun**: Timeout durumunda output otomatik kapatılmıyor.

**Öneri**: Timeout exception'ında output kapatma mekanizması.

---

### 14. ⚠️ **ORTA**: Prodigit - Resistance Mode Üst Limit Yok

**Dosya**: `gui/controllers/prodigit_controller.py:94-100`

**Sorun**: Resistance için sadece pozitif kontrol var, üst limit yok.

**Öneri**: Makul bir üst limit ekle (örn. 1MΩ).

---

## Düşük Öncelikli İyileştirmeler

### 15. ⚠️ **DÜŞÜK**: GUI'da Limit Değerleri Gösterilmeli

**Dosyalar**: Tüm tab dosyaları

**Öneri**: Her input field'ın yanında max değer gösterilmeli (örn. "Voltage (V, max: 400):").

---

### 16. ⚠️ **DÜŞÜK**: Output Durumu Görsel Göstergesi

**Dosyalar**: Tüm tab dosyaları

**Öneri**: Output açık/kapalı durumu için LED benzeri görsel gösterge.

---

### 17. ⚠️ **DÜŞÜK**: Logging İyileştirmeleri

**Dosyalar**: Tüm controller'lar

**Öneri**: Güvenlik kritik işlemler için daha detaylı logging.

---

### 18. ⚠️ **DÜŞÜK**: Kullanıcı Onayı İyileştirmeleri

**Dosyalar**: `gui/gui/keithley_tab.py`, `gui/gui/prodigit_tab.py`

**Öneri**: Yüksek güç/voltaj değerleri için ekstra onay mesajı.

---

## Öncelik Matrisi

| Öncelik | Sorun Sayısı | Aciliyet |
|---------|--------------|----------|
| Kritik  | 4            | Hemen düzeltilmeli |
| Yüksek  | 5            | Kısa sürede düzeltilmeli |
| Orta    | 5            | Planlı olarak düzeltilmeli |
| Düşük   | 4            | İyileştirme olarak yapılabilir |

---

## Önerilen Düzeltme Sırası

1. **Faz 1 (Kritik - Hemen)**:
   - Sorensen OVP kontrolü
   - Keithley voltage protection
   - Prodigit parametre kontrolü
   - Global emergency stop

2. **Faz 2 (Yüksek - 1 hafta içinde)**:
   - Output öncesi parametre doğrulama
   - Exception handling iyileştirmeleri
   - Power limit kontrolü
   - Disconnect iyileştirmeleri
   - Sorensen OCP ekleme

3. **Faz 3 (Orta - 1 ay içinde)**:
   - Mode switch kontrolleri
   - Cihaz hata mesajları kontrolü
   - Timeout handling

4. **Faz 4 (Düşük - İyileştirme)**:
   - GUI iyileştirmeleri
   - Logging iyileştirmeleri

---

## Sonuç

GUI kodunda temel güvenlik kontrolleri mevcut ancak kritik eksiklikler var. Özellikle output açılmadan önce koruma ayarlarının kontrolü ve global emergency stop mekanizması acilen eklenmelidir. Bu düzeltmeler yapılmadan production ortamında kullanım önerilmez.

**Toplam Tespit Edilen Sorun**: 18  
**Kritik Sorun**: 4  
**Yüksek Öncelikli Sorun**: 5  
**Orta Öncelikli Sorun**: 5  
**Düşük Öncelikli Sorun**: 4

---

**Rapor Hazırlayan**: Güvenlik Denetimi Sistemi  
**Son Güncelleme**: 2025-01-20

