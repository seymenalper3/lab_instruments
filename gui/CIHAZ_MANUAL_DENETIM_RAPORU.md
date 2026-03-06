# Cihaz Manual Denetim Raporu
# Device Manual vs GUI Code Audit Report

**Tarih:** 2026-02-11
**Kapsam:** Sorensen SGX400-12D ve Prodigit 34205A
**Referans Manualler:**
- Sorensen: `smt-sorensen-sgx-pogramming-manual.pdf` (M551601-01 Rev A)
- Prodigit: `90034000A5_34000A series Operation Manual-rD.pdf`

**Not:** Keithley 2281S bu denetimin disinda tutuldu - lab testleri ile ayri olarak dogrulanacak.

---

## Ozet

| Seviye | Prodigit | Sorensen | Toplam |
|--------|----------|----------|--------|
| KRITIK  | 2        | 1        | 3      |
| ORTA    | 2        | 1        | 3      |
| DUSUK   | 1        | 1        | 2      |
| BILGI   | 0        | 1        | 1      |
| **Toplam** | **5**  | **4**    | **9**  |

---

## PRODIGIT 34205A Bulgulari

### P1. [KRITIK] set_power komutu YANLIS: `POW:HIGH` -> `CP:HIGH`

**Dosya:** `gui/models/device_config.py` satir 185
**Mevcut kod:** `'set_power': 'POW:HIGH {}'`
**Manual (sayfa 128, 134, 141):**

Manual iki format tanimlar (Simple ve Complex):

| Mod | Simple Format | Complex Format | Kisaltma |
|-----|---------------|----------------|----------|
| CC  | `CC:HIGH`     | `[PRESet:]CC\|CURR:HIGH` | CURR |
| CV  | `CV:HIGH`     | `[PRESet:]CV\|VOLT:HIGH` | VOLT |
| CR  | `CR:HIGH`     | `[PRESet:]CR\|RES:HIGH`  | RES  |
| **CP** | **`CP:HIGH`** | **`[PRESet:]CP:HIGH`** | **YOK** |

Guc (CP) modu icin `POWer` veya `POW` kisaltmasi **mevcut degil**.
Diger modlarin uzun isim alternatifi var (CURR, VOLT, RES) ama CP'nin yok.

**Etki:** `POW:HIGH 100` komutu cihaz tarafindan taninmayacak. CP modunda guc ayarlamasi calismayacak.

**Duzeltme:**
```python
# device_config.py
'set_power': 'CP:HIGH {}',  # Onceki: 'POW:HIGH {}'
```

---

### P2. [KRITIK] query_mode ve query_load_status sayi donduruyor, string degil

**Dosyalar:**
- `gui/controllers/prodigit_controller.py` satir 277-291
- `gui/gui/prodigit_tab.py` satir 338-342

**Manual (sayfa 130, 137):**

| Sorgu | Donus Formati |
|-------|---------------|
| `MODE?` | `0`:CC, `1`:CR, `2`:CV, `3`:CP |
| `LOAD?` | `0`:OFF, `1`:ON |

**Kod sorunu - query_mode():**
```python
# prodigit_controller.py satir 280
return self.query_command(cmd)  # "0", "1", "2" veya "3" donduruyor
```
GUI'da `f"Mode: {mode}"` seklinde gosteriliyor -> kullanici "Mode: 0" goruyor.

**Kod sorunu - query_load_status():**
```python
# prodigit_tab.py satir 342
foreground="green" if "ON" in load_status else "red"
```
Cihaz `"1"` donduruyor, `"ON"` degil. Dolayisiyla `"ON" in "1"` her zaman `False` ->
load status **her zaman kirmizi** gosteriliyor, load acik olsa bile!

**Etki:** Yuksek - Load status gostergesi herzaman yanlis renk gosteriyor.

**Duzeltme:**
```python
# prodigit_controller.py
MODE_MAP = {'0': 'CC', '1': 'CR', '2': 'CV', '3': 'CP'}
LOAD_MAP = {'0': 'OFF', '1': 'ON'}

def query_mode(self) -> Optional[str]:
    try:
        cmd = self.device_spec.default_commands['query_mode']
        raw = self.query_command(cmd).strip()
        return self.MODE_MAP.get(raw, raw)
    except Exception:
        return None

def query_load_status(self) -> Optional[str]:
    try:
        cmd = self.device_spec.default_commands['query_load']
        raw = self.query_command(cmd).strip()
        return self.LOAD_MAP.get(raw, raw)
    except Exception:
        return None
```

---

### P3. [ORTA] query_error komutu yanlis: `SYST:ERR?` -> `ERR?`

**Dosya:** `gui/models/device_config.py` satir 195
**Mevcut kod:** `'query_error': 'SYST:ERR?'`
**Manual (sayfa 130, 137):**

| Format | Komut |
|--------|-------|
| Simple | `ERR {?}` |
| Complex | `[STATe:] ERRor {?}` |

Prodigit'te `SYSTem:ERRor?` komutu **mevcut degil**. Dogru komut `ERR?` veya `STAT:ERR?`.

**Etki:** Orta - Kod zaten `send_command` icinde hata kontrolunu atliyor (satir 44: "Prodigit doesn't support SYST:ERR?"), ama `query_error()` metodu dogrudan cagrilirsa timeout alir.

**Duzeltme:**
```python
# device_config.py
'query_error': 'ERR?',  # Onceki: 'SYST:ERR?'
```

---

### P4. [ORTA] Yardim metninde yanlis cihaz ozellikleri

**Dosya:** `gui/gui/prodigit_tab.py` satir 559-562

**Mevcut kod (Help Guide):**
```
• Do not exceed device ratings:
  - Max Current: 120A
  - Max Voltage: 150V
  - Max Power: 1200W
```

**Gercek 34205A ozellikleri (device_config.py + manual sayfa 13):**
```
  - Max Current: 160A
  - Max Voltage: 600V
  - Max Power: 5000W
```

Yardim metnindeki degerler muhtemelen daha kucuk bir 34000A modelinden (ornegin 34201A).

**Etki:** Orta - Kullanici yanlis limitlere gore calisabilir.

**Duzeltme:** Yardim metnindeki degerleri `self.device_spec` uzerinden dinamik olarak al.

---

### P5. [DUSUK] Prodigit Limit komutlari icin POWer formu mevcut (referans notu)

**Manual (sayfa 136, Table 4-3B):**
```
LIMit:CURRent:{HIGH|LOW}  -> Akim limiti
LIMit:POWer:{HIGH|LOW}    -> Guc limiti  (POWer burada VAR!)
LIMit:VOLTage:{HIGH|LOW}  -> Gerilim limiti
```

Ilginc sekilde, `POWer` kelimesi **limit komutlarinda** kullaniliyor ama **set komutlarinda** (`CP:HIGH`) kullanilmiyor. Bu Prodigit'in komut yapisindaki bir tutarsizlik.

**Etki:** Bilgi - Gelecekte limit komutlari eklenirse `LIMit:POWer:HIGH` kullanilmali.

---

## SORENSEN SGX400-12D Bulgulari

### S1. [KRITIK] set_ocp komutu MEVCUT DEGIL: `SOUR:CURR:PROT` -> yok

**Dosyalar:**
- `gui/models/device_config.py` satir 123
- `gui/controllers/sorensen_controller.py` satir 67-75

**Mevcut kod:**
```python
# device_config.py
'set_ocp': 'SOUR:CURR:PROT {}',

# sorensen_controller.py
def set_ocp(self, ocp_current: float):
    cmd = self.device_spec.default_commands['set_ocp'].format(ocp_current)
    self.send_command(cmd, check_errors=True)
```

**Manual SOURCE SCPI Command Tree (Section 8.5.1, sayfa 8-10 ~ 8-11):**
```
SOURce
    :CURRent       -> Akim ayarla (SOUR:CURR)
    :CURRent:LIMit -> Yazilimsal ust limit (SOUR:CURR:LIM)
    :CURRent:RAMP  -> Rampa
    :VOLTage       -> Gerilim ayarla (SOUR:VOLT)
    :VOLTage:PROTection -> OVP donanim koruma (SOUR:VOLT:PROT)
    :POWer         -> Guc regulasyonu (SGX-unique, Section 8.13)
```

`SOURce:CURRent:PROTection` komutu **komut agacinda MEVCUT DEGIL**.
Sadece `SOURce:VOLTage:PROTection` (OVP) var.

Akim icin mevcut secenek: `SOURce:CURRent:LIMit` - bu bir "soft limit" (yazilimsal limit).
Manual aciklamasi (sayfa 8-11): *"Sets an upper soft limit on the programmed output current for the supply. The soft limit prevents the supply from being inadvertently programmed above the soft limit."*

**Onemli fark:**
- **OVP** (`SOUR:VOLT:PROT`): Donanim korumasi - asim durumunda output kapanir (trip)
- **Current Limit** (`SOUR:CURR:LIM`): Yazilim limiti - bu degerin ustune programlama engellenir ama trip yok

**Etki:** Kritik - `set_ocp()` cagrildiginda cihaz `-102 Syntax Error` dondurecek. `check_errors=True` ile cagrildigindan hata yakalanir ama islem basarisiz olur.

**Duzeltme secenekleri:**
1. `SOUR:CURR:LIM {}` olarak degistir (davranis farki: soft limit, trip yok)
2. `set_ocp()` metodunu kaldir ve SGX'in OCP desteklemedigini belgele
3. GUI'dan OCP butonunu kaldir veya "Current Soft Limit" olarak yeniden adlandir

**Onerilen:**
```python
# device_config.py
'set_current_limit': 'SOUR:CURR:LIM {}',  # Onceki: 'set_ocp': 'SOUR:CURR:PROT {}'

# sorensen_controller.py
def set_current_limit(self, limit_current: float):
    """Set current soft limit (NOT hardware OCP - SGX doesn't support OCP)"""
    ...
```

---

### S2. [ORTA] measure_power() hesapla yerine MEAS:POW? kullanilabilir

**Dosya:** `gui/controllers/sorensen_controller.py` satir 111-119

**Mevcut kod:**
```python
def measure_power(self) -> Optional[float]:
    voltage = self.measure_voltage()
    current = self.measure_current()
    if voltage is not None and current is not None:
        return voltage * current
```

**Manual Section 8.13.4 (SGX MEASURE, sayfa 8-36):**
```
MEASure:POWer? - "Returns the value for present power in watts being
dissipated by the load. The power is measured by taking voltage and
current measurement pairs three times, and averaging the result to
a single wattage reading."
```

SGX modeli `MEAS:POW?` komutunu destekliyor. Bu komut 3 olcum yapip ortalamasini alir,
bizim V*I hesaplamamizdan daha dogru sonuc verir.

**Etki:** Dusuk - Mevcut hesaplama calisir ama tek bir V ve I olcumune dayanir,
cihazin kendi 3-olcum ortalamasindan daha az hassas.

**Duzeltme:**
```python
# device_config.py - Sorensen commands'a ekle
'measure_power': 'MEAS:POW?',

# sorensen_controller.py
def measure_power(self) -> Optional[float]:
    try:
        cmd = self.device_spec.default_commands['measure_power']
        response = self.query_command(cmd)
        return float(response)
    except Exception as e:
        logger.debug(f"Error measuring power: {e}")
        return None
```

---

### S3. [DUSUK] SOUR:POW guc regulasyonu destegi mevcut (kullanilmiyor)

**Manual Section 8.13.2 (sayfa 8-30):**
```
SOURce:POWer <NRf> - Power regulation modu
```

SGX, guc regulasyonu modunu destekliyor. Ancak manualda onemli uyarilar var:

> *"Power mode is easily exited unintentionally by re-programming a voltage
> or current value, or issuing certain other commands that have a material
> influence over the power control loop."*
>
> *"THIS COULD CAUSE EXCESS POWER BEING DELIVERED TO THE LOAD."*

**Etki:** Bilgi - Mevcut GUI'da guc regulasyonu yok. Eklenmesi istenirse dikkatli
bir guvenlik tasarimi gerekir (output off -> V/I/OVP ayarla -> POW ayarla -> output on).

---

### S4. [BILGI] Sorensen sequence programlama destegi

**Manual Section 8.13.3:** SGX, 50 adede kadar programlanabilir sekans destekler.
Her sekans 20 adim icerebilir. Adimlar: VIMODE, RAMPTOV, RAMPTOC, POWERSETTINGS.

Bu ozellik su an GUI'da kullanilmiyor. Gelecekte Sorensen profil calistirma
ozelligi eklenmek istenirse bu arayuz kullanilabilir.

---

## Dogrulanan Komutlar (Sorunsuz)

### Sorensen SGX400-12D - Dogru Komutlar

| Fonksiyon | Koddaki Komut | Manual Referansi | Durum |
|-----------|---------------|------------------|-------|
| identify | `*IDN?` | IEEE 488.2, sayfa 8-9 | OK |
| set_voltage | `SOUR:VOLT {}` | Section 8.5.2 `SOURce:VOLTage` | OK |
| set_current | `SOUR:CURR {}` | Section 8.5.2 `SOURce:CURRent` | OK |
| set_ovp | `SOUR:VOLT:PROT {}` | Section 8.5.2 `SOURce:VOLTage:PROTection` | OK |
| output_on | `OUTP:STAT ON` | Section 8.7.2 `OUTPut:STATe ON` | OK |
| output_off | `OUTP:STAT OFF` | Section 8.7.2 `OUTPut:STATe OFF` | OK |
| measure_voltage | `MEAS:VOLT?` | Section 8.6.2 `MEASure:VOLTage?` | OK |
| measure_current | `MEAS:CURR?` | Section 8.6.2 `MEASure:CURRent?` | OK |
| query_error | `SYST:ERR?` | Section 8.9.2 `SYSTem:ERRor?` | OK |

### Prodigit 34205A - Dogru Komutlar

| Fonksiyon | Koddaki Komut | Manual Referansi | Durum |
|-----------|---------------|------------------|-------|
| identify | `*IDN?` | Standart IEEE 488.2 | OK |
| set_mode_cc | `STAT:MODE CC` | Table 4-4B `[STATe:]MODE CC` | OK |
| set_mode_cv | `STAT:MODE CV` | Table 4-4B `[STATe:]MODE CV` | OK |
| set_mode_cp | `STAT:MODE CP` | Table 4-4B `[STATe:]MODE CP` | OK |
| set_mode_cr | `STAT:MODE CR` | Table 4-4B `[STATe:]MODE CR` | OK |
| set_current | `CURR:HIGH {}` | Table 4-1B `CC\|CURR:HIGH` | OK |
| set_voltage | `VOLT:HIGH {}` | Table 4-1B `CV\|VOLT:HIGH` | OK |
| set_resistance | `RES:HIGH {}` | Table 4-1B `CR\|RES:HIGH` | OK |
| load_on | `STAT:LOAD ON` | Table 4-4B `[STATe:]LOAD ON` | OK |
| load_off | `STAT:LOAD OFF` | Table 4-4B `[STATe:]LOAD OFF` | OK |
| measure_voltage | `MEAS:VOLT?` | Table 4-6 `MEAS:VOLT?` | OK |
| measure_current | `MEAS:CURR?` | Table 4-6 `MEAS:CURR?` | OK |
| measure_power | `MEAS:POW?` | Table 4-6 `MEAS:POW?` | OK |
| query_mode | `STAT:MODE?` | Table 4-4B `[STATe:]MODE?` | OK (donus formati sorunu P2'de) |
| query_load | `STAT:LOAD?` | Table 4-4B `[STATe:]LOAD?` | OK (donus formati sorunu P2'de) |

---

## Oncelik Sirasi (Onerilen Duzeltme Sirasi)

1. **P1** - `POW:HIGH` -> `CP:HIGH` (tek satir degisiklik, CP modu tamamen bozuk)
2. **S1** - `SOUR:CURR:PROT` kaldir/degistir (mevcut olmayan komut, hata uretir)
3. **P2** - MODE?/LOAD? donus degerlerini maple (load gostergesi her zaman yanlis)
4. **P3** - `SYST:ERR?` -> `ERR?` (error query calismaz)
5. **S2** - `MEAS:POW?` kullan (hassasiyet iyilestirmesi)
6. **P4** - Yardim metni guncelle (yanlis cihaz specs)

---

## Lab Dogrulama Plani

Bu rapordaki bulgularin cogu manual incelemesine dayanmaktadir. Kesin dogrulama
icin asagidaki testler onerilir:

### Prodigit ile test:
1. `CP:HIGH 100` gonder -> guc ayarlanir mi? (P1 dogrulamasi)
2. `POW:HIGH 100` gonder -> hata mi doner? (P1 dogrulamasi)
3. `MODE?` gonder -> "0"/"1"/"2"/"3" mu doner yoksa "CC"/"CR" mu? (P2 dogrulamasi)
4. `LOAD?` gonder -> "0"/"1" mi doner yoksa "OFF"/"ON" mu? (P2 dogrulamasi)
5. `ERR?` gonder -> yanit var mi? (P3 dogrulamasi)

### Sorensen ile test:
1. `SOUR:CURR:PROT 5.0` gonder -> hata donuyor mu? (S1 dogrulamasi)
2. `SOUR:CURR:LIM 5.0` gonder -> limit ayarlaniyor mu? (S1 alternatif)
3. `MEAS:POW?` gonder -> guc degeri donuyor mu? (S2 dogrulamasi)
