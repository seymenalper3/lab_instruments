# Laboratuvar Cihaz Kontrol Sistemi -- Mimari Dokumani

## 1. Genel Bakis

Bu proje, elektrikli arac (EV) batarya testleri icin kullanilan uc laboratuvar cihazini tek bir masaustu GUI uygulamasindan kontrol etmeye yarayan bir yazilimdir. Uygulama Python ile yazilmis olup GUI katmaninda tkinter, cihaz haberlesmesinde ise SCPI (Standard Commands for Programmable Instruments) protokolunu kullanir.

### 1.1 Kontrol Edilen Cihazlar

| Cihaz | Tur | Desteklenen Arayuzler | Temel Islev |
|-------|-----|----------------------|-------------|
| Keithley 2281S | Batarya Simulatoru / Emulasyon | USB, Ethernet, GPIB | Sarj (Power Supply modu), desarj (Battery Test modu), puls testi, batarya model olusturma |
| Sorensen SGX400-12D | Guc Kaynagi | RS232, Ethernet, GPIB | Gerilim/akim ayari, OVP/OCP korumalari, cikis kontrolu |
| Prodigit 34205A | Elektronik Yuk | RS232, USB | CC/CV/CP/CR modlari, akiim profili calistirma, yuk kontrolu |

### 1.2 Uygulamanin Calistirilmasi

```
cd gui/
python main.py
```

Uygulama `main.py` uzerinden baslatilir. Bu dosya once loglama sistemini (`AppLogger`) baslatir, ardindan `MainWindow` sinifini olusturup tkinter olay dongusunu calistirir.

---

## 2. Dizin Yapisi

```
gui/
|-- main.py                          # Uygulama giris noktasi
|-- requirements.txt                 # Python bagimliliklari
|
|-- controllers/                     # Cihaz kontrol mantigi
|   |-- base_controller.py           # Soyut temel controller (ABC)
|   |-- keithley_controller.py       # Keithley 2281S controller
|   |-- keithley/
|   |   +-- tests/
|   |       |-- pulse_test.py        # Puls testi runner
|   |       |-- battery_model.py     # Batarya model olusturucu
|   |       +-- profile_runner.py    # Akim profili calistirici
|   |-- prodigit_controller.py       # Prodigit 34205A controller
|   +-- sorensen_controller.py       # Sorensen SGX controller
|
|-- gui/                             # GUI bilesenler (tkinter)
|   |-- main_window.py               # Ana pencere, tab yoneticisi
|   |-- device_tab.py                # Genel cihaz tab base class
|   |-- connection_widget.py         # Baglanti ayarlari widget'i
|   |-- keithley_tab.py              # Keithley ozel GUI
|   |-- prodigit_tab.py              # Prodigit ozel GUI
|   |-- sorensen_tab.py              # Sorensen ozel GUI
|   |-- monitoring_tab.py            # Canli izleme ve veri kaydi
|   +-- debug_console_tab.py         # Uygulama log konsolu
|
|-- interfaces/                      # Haberlesme arayuzleri
|   |-- base_interface.py            # Soyut arayuz sinifi (ABC)
|   |-- serial_interface.py          # RS232 (pyserial)
|   |-- ethernet_interface.py        # TCP soket
|   +-- visa_interface.py            # PyVISA (USB/GPIB)
|
|-- models/
|   +-- device_config.py             # Cihaz tanimlari, SCPI komutlari, limitler
|
|-- utils/
|   |-- app_logger.py                # Merkezi loglama sistemi (Singleton)
|   |-- data_logger.py               # Monitoring veri toplama ve kayit
|   |-- keithley_logger.py           # Keithley profil/test log kaydedici
|   +-- prodigit_logger.py           # Prodigit profil log kaydedici
|
|-- examples/
|   +-- example_profile.csv          # Ornek akim profili
|
|-- assets/
|   +-- logo.png                     # Uygulama logosu
|
+-- tests/                           # Test dosyalari
```

---

## 3. Katmanli Mimari

Sistem dort katmandan olusur. Her katman yalnizca bir alt katmanla iletisim kurar:

```
+------------------------------------------------------------------+
|                        GUI Katmani                               |
|  MainWindow -> DeviceTab (Keithley/Sorensen/Prodigit Tab)        |
|  MonitoringTab, DebugConsoleTab, ConnectionWidget                |
+-------------------------------+----------------------------------+
                                |
                                v
+------------------------------------------------------------------+
|                     Controller Katmani                            |
|  BaseDeviceController (ABC)                                      |
|    +-- KeithleyController (+ test runner delegeleri)              |
|    +-- SorensenController                                        |
|    +-- ProdigitController                                        |
+-------------------------------+----------------------------------+
                                |
                                v
+------------------------------------------------------------------+
|                     Interface Katmani                             |
|  DeviceInterface (ABC)                                           |
|    +-- SerialInterface   (RS232 / pyserial)                      |
|    +-- EthernetInterface (TCP soket)                              |
|    +-- VISAInterface     (PyVISA / USB / GPIB)                   |
+-------------------------------+----------------------------------+
                                |
                                v
+------------------------------------------------------------------+
|                     Fiziksel Cihaz                                |
|  Keithley 2281S | Sorensen SGX400-12D | Prodigit 34205A          |
+------------------------------------------------------------------+
```

### 3.1 Veri Akisi

Tipik bir islem su siralamayla gerceklesir:

```
Kullanici GUI'de bir deger girer
        |
        v
GUI Tab (ornegin KeithleyTab) -> safe_execute() ile controller metodunu cagirir
        |
        v
Controller (ornegin KeithleyController.set_voltage())
  - Parametre dogrulamasini yapar (max gerilim, guc limiti)
  - SCPI komutunu device_spec.default_commands sozlugundan alir
  - send_command() veya query_command() cagirir
        |
        v
BaseDeviceController.send_command()
  - Baglanti durumunu kontrol eder
  - Interface uzerinden write() cagirir
  - Hata durumunda _handle_timeout() ile guvenli kapatma yapar
        |
        v
Interface (ornegin VISAInterface.write())
  - SCPI komutunu fiziksel baglanti uzerinden gonderir
  - Yanit bekler (query durumunda)
        |
        v
Fiziksel Cihaz komutu isler ve yanit doner
```

---

## 4. Temel Mimari Desenler

### 4.1 Soyut Temel Siniflar (Abstract Base Classes)

Hem controller hem de interface katmaninda ABC kullanilir. Bu sayede yeni bir cihaz veya haberlesme yontemi eklemek icin mevcut kodun degistirilmesine gerek kalmaz (Acik/Kapali Ilkesi).

**DeviceInterface (ABC)** -- `interfaces/base_interface.py`:

```python
class DeviceInterface(ABC):
    @abstractmethod
    def connect(self): ...
    @abstractmethod
    def disconnect(self): ...
    @abstractmethod
    def write(self, command): ...
    @abstractmethod
    def query(self, command): ...
    def is_connected(self) -> bool: ...
```

**BaseDeviceController (ABC)** -- `controllers/base_controller.py`:

```python
class BaseDeviceController(ABC):
    def __init__(self, interface: DeviceInterface, device_spec: DeviceSpec): ...
    def connect(self) -> bool: ...
    def disconnect(self): ...
    def send_command(self, command, check_errors=False): ...
    def query_command(self, command, check_errors=False) -> str: ...
    def set_busy(self, busy: bool): ...       # threading.Lock korumasinda
    def is_busy(self) -> bool: ...            # threading.Lock korumasinda
    def is_available_for_monitoring(self) -> bool: ...
    @abstractmethod
    def measure_voltage(self) -> Optional[float]: ...
    @abstractmethod
    def measure_current(self) -> Optional[float]: ...
    def get_measurements(self) -> MeasurementData: ...
```

Her cihaz controller'i bu soyut sinifi genisletir ve `measure_voltage()`, `measure_current()` metodlarini somutlastirir. Ayrica cihaza ozgu metodlar (ornegin `output_on/off`, `set_mode_cc`) eklenir.

### 4.2 Delegation (Delege) Deseni -- Keithley Test Runner'lari

Keithley 2281S en karmasik cihazdir: puls testi, batarya model olusturma ve akim profili calistirma gibi uzun sureli islemler icerir. Bu karmasiklik tek sinifta toplanmak yerine, **composition (bilesim)** yoluyla ayri runner siniflarona devredilir:

```python
class KeithleyController(BaseDeviceController):
    def __init__(self, interface):
        super().__init__(interface, DEVICE_SPECS[DeviceType.KEITHLEY_2281S])

        # Test runner'lar -- composition ile delegasyon
        self._pulse_test = KeithleyPulseTest(self)
        self._battery_model = KeithleyBatteryModel(self)
        self._profile_runner = KeithleyProfileRunner(self)

    def run_battery_model_test(self, **kwargs):
        # Dogrudan islem yapmak yerine runner'a devreder
        return self._battery_model.run(**kwargs)

    def run_current_profile(self, profile_path, **kwargs):
        return self._profile_runner.run(profile_path=profile_path, **kwargs)
```

Her runner sinifi `controller` referansini alir ve tum cihaz haberlesimini controller uzerinden yapar. Boylece:

- **KeithleyPulseTest** (`controllers/keithley/tests/pulse_test.py`): Puls fazi ve dinlenme fazini yonetir, EVOC/ESR olcumu yapar, CSV'ye kaydeder.
- **KeithleyBatteryModel** (`controllers/keithley/tests/battery_model.py`): Tam batarya model olusturma surecini (desarj -> sarj -> karakterizasyon -> model kaydetme -> CSV cikarma) yonetir.
- **KeithleyProfileRunner** (`controllers/keithley/tests/profile_runner.py`): CSV'den okunan akim profilini sarj/desarj modlari arasinda otomatik gecisle calistirir.

Bu yapi, her test turunu bagimsiz olarak gelistirmeyi, test etmeyi ve degistirmeyi kolaylastirir.

### 4.3 Tek Dogru Kaynak (Single Source of Truth) -- device_config.py

Tum SCPI komutlari, cihaz limitleri ve zamanlama parametreleri `models/device_config.py` icindeki `DEVICE_SPECS` sozlugunde tanimlanir. Controller'lar kendi icerisinde komut string'i barindirmaz; bunun yerine `device_spec.default_commands` sozlugundan okur.

```python
DEVICE_SPECS = {
    DeviceType.SORENSEN_SGX: DeviceSpec(
        name="Sorensen SGX400-12 D",
        max_voltage=400.0,
        max_current=12.0,
        max_power=4800.0,
        supported_interfaces=[InterfaceType.RS232, InterfaceType.ETHERNET, InterfaceType.GPIB],
        default_commands={
            'identify': '*IDN?',
            'set_voltage': 'SOUR:VOLT {}',
            'measure_voltage': 'MEAS:VOLT?',
            # ...
        }
    ),
    DeviceType.KEITHLEY_2281S: DeviceSpec(...),
    DeviceType.PRODIGIT_34205A: DeviceSpec(
        timing=DeviceTiming(min_measurement_interval_s=0.050, safety_factor=1.2),
        # ...
    ),
}
```

Bu yaklasim sayesinde:
- Bir SCPI komutunu degistirmek icin tek bir yer vardir.
- Cihaz limitleri (max gerilim, akim, guc) controller'da dogrulama icin kullanilir.
- Yeni bir cihaz eklemek `DEVICE_SPECS`'e bir giris eklemek ve yeni controller yazmak kadar basittir.

### 4.4 Interface Soyutlamasi

Uc farkli haberlesme yontemi ortak `DeviceInterface` arayuzu arkasinda soyutlanir:

| Interface | Kutuphane | Kullanim Alani |
|-----------|-----------|----------------|
| `SerialInterface` | pyserial | Sorensen (RS232), Prodigit (RS232) |
| `EthernetInterface` | socket (stdlib) | Sorensen, Keithley (TCP/IP) |
| `VISAInterface` | PyVISA | Keithley (USB/GPIB), Prodigit (USB/ASRL) |

`DeviceTab._create_interface()` metodu, kullanicinin sectigi baglanti turune gore uygun interface nesnesini olusturur:

```python
def _create_interface(self, config: ConnectionConfig):
    if config.interface_type.value == "RS232":
        return SerialInterface(**config.parameters)
    elif config.interface_type.value == "Ethernet":
        return EthernetInterface(**config.parameters)
    elif config.interface_type.value in ["USB", "GPIB"]:
        return VISAInterface(**config.parameters)
```

### 4.5 Thread Yonetimi ve Busy Mekanizmasi

Uzun sureli testler (puls testi, batarya model, profil calistirma) ana GUI thread'ini bloke etmemek icin daemon thread'lerde calistirilir.

**Busy Flag**: `BaseDeviceController` icerisinde `threading.Lock` ile korunan bir `busy` bayragina sahiptir:

```python
class BaseDeviceController(ABC):
    def __init__(self, ...):
        self.busy = False
        self._busy_lock = threading.Lock()

    def set_busy(self, busy: bool):
        with self._busy_lock:
            self.busy = busy

    def is_busy(self) -> bool:
        with self._busy_lock:
            return self.busy

    def is_available_for_monitoring(self) -> bool:
        return self.is_connected() and not self.is_busy()
```

Bir test basladiginda:
1. `set_busy(True)` cagirilir.
2. Monitoring sistemi `is_available_for_monitoring()` kontroluyle bu cihazi atlayarak interferans onlenir.
3. Test tamamlandiginda `set_busy(False)` `finally` blogu icerisinde cagirilir (hata durumunda bile).

**GUI Thread Guvenligi**: tkinter tek-thread'li oldugu icin, arka plan thread'lerinden dogrudan GUI guncellemesi yapilmaz. Bunun yerine:
- `MonitoringTab.update_display()` metodu tkinter `.after()` ile periyodik olarak cagirilir.
- `DataLogger` bir `queue.Queue` kullanarak arka plan thread'inden GUI thread'ine veri aktarir.

```
[Monitoring Daemon Thread]                  [GUI Ana Thread]
        |                                         |
        |  controller.get_measurements()          |
        |  data_queue.put(veri)  -------->   .after() ile update_display()
        |                                    data_queue.get_nowait()
        |                                    widget'leri guncelle
```

### 4.6 DeviceTiming -- Zamanlama Yonetimi

Prodigit 34205A cihazi ardisik komutlar arasinda minimum bekleme suresi gerektirir (manual'den: 50ms). Bu gereksinim `DeviceTiming` dataclass'i ile modellenir:

```python
@dataclass
class DeviceTiming:
    min_measurement_interval_s: float = 0.050   # Manual minimum
    safety_factor: float = 1.2                  # %20 guvenlik payi

    @property
    def send_delay_s(self) -> float:
        return self.min_measurement_interval_s * self.safety_factor  # 60ms

    @property
    def query_write_delay_s(self) -> float:
        return self.min_measurement_interval_s * 1.1  # 55ms

    @property
    def query_read_delay_s(self) -> float:
        return 0.010  # 10ms -- buffer temizligi
```

`ProdigitController`, `send_command()` ve `query_command()` metodlarini override ederek bu gecikmeleri otomatik olarak uygular. Ayrica `query_command()` icinde `write() + read()` seklinde ayristirma yaparak zamanlama uzerinde daha ince kontrol saglar.

---

## 5. GUI Katmani

### 5.1 Genel Yapi

```
MainWindow (Tk root)
|-- Header (logo + baslik + acil durdurma butonu)
|-- Notebook (ttk.Notebook -- sekme yoneticisi)
    |-- SorensenTab (DeviceTab'dan turetilmis)
    |-- KeithleyTab (DeviceTab'dan turetilmis)
    |-- ProdigitTab (DeviceTab'dan turetilmis)
    |-- MonitoringTab
    +-- DebugConsoleTab
```

### 5.2 DeviceTab -- Temel Cihaz Sekmesi

`DeviceTab` tum cihaz sekmelerinin temel sinifidir. Su bilesenlerden olusur:

- **ConnectionWidget**: Arayuz secimi (RS232/Ethernet/USB/GPIB), baglanti parametreleri, Connect/Disconnect butonu.
- **Status Bar**: Baglanti durumu mesaji.
- **Control Frame**: Alt siniflar tarafindan cihaza ozel kontroller eklenir (`create_controls()` override).
- **Measurements Frame**: Canli gerilim, akim ve guc gostergeleri.

Baglanti akisi:

```
Kullanici "Connect" tiklar
    |
    v
ConnectionWidget._on_connect_click()
    |
    v
ConnectionWidget._get_connection_config()  -- ConnectionConfig olusturur
    |
    v
DeviceTab.on_connect(config)
    |-- _create_interface(config) -- uygun interface nesnesini olusturur
    |-- controller = ControllerClass(interface)
    |-- controller.connect()
    |       |-- interface.connect()
    |       |-- identify() (*IDN? gonderir)
    |       +-- remote_mode() (varsa)
    |-- MainWindow monitoring_tab'a controller'i kaydeder
    v
Baglanti basarili -- GUI guncellenir
```

Baglanti koparmada ise controller'in `disconnect()` metodu oncelikle cihaz cikislarini kapatir (`output_off` veya `load_off`), ardindan `local_mode()` ile cihazi lokal moda alir ve fiziksel baglanti sonlandirilir.

### 5.3 ConnectionWidget -- Baglanti Ayarlari

`ConnectionWidget`, her cihaz sekmesinde tekrar kullanilan bagimsiz bir bilesiktir. Ozellikleri:

- Desteklenen arayuzleri `DeviceSpec.supported_interfaces` listesinden dinamik olarak yükler.
- Secilen arayuze gore (RS232, Ethernet, VISA) farkli ayar panelleri gosterir.
- Baglanti ayarlarini `~/.lab_instruments/connection_settings.json` dosyasina kaydeder ve bir sonraki sefere yuklenir.
- VISA cihazlari icin "Detect" butonu ile `pyvisa.ResourceManager().list_resources()` calistirilir.
- Keithley Ethernet baglantisi icin IP adresi kilavuzu sunar.

### 5.4 MonitoringTab -- Canli Izleme

Monitoring sekmesi tum bagli cihazlardan es zamanli olcum toplayarak canli gosterim ve CSV/Excel kaydedilmesini saglar.

**Cift Hizli Sistem**:
- **Veri Ornekleme Hizi** (`sampling_rate_s`): Cihazlardan ne siklikta olcum alinacagini belirler. Minimum 0.2 saniye (5 Hz).
- **GUI Guncelleme Hizi** (`gui_update_rate_s`): Ekranin ne siklikta yenilenecegini belirler.

Hazir on-ayarlar: Yavas (5s/2s), Standart (1s/1s), Hizli (0.5s/0.5s), Maksimum (0.2s/1s).

**DataLogger**:
- Arka plan thread'inde calisan `_monitoring_worker()` tum cihazlardan `get_measurements()` cagirir.
- Busy cihazlari atlayarak calisan testlere mudahale etmez.
- Veri `queue.Queue` uzerinden GUI thread'ine aktarilir.
- Bellek tasmasini onlemek icin maksimum 100.000 veri noktasi siniri vardir (FIFO); limit asildiginda en eski %50 silinir.
- CSV ve Excel formatlarinda kaydetme destegi sunar.
- Matplotlib ile canli grafik olusturma ozelligi vardir (matplotlib yuklu ise).

### 5.5 DebugConsoleTab -- Hata Ayiklama Konsolu

`AppLogger` tarafindan uretilen tum log mesajlari bir `queue.Queue` uzerinden bu sekmeye aktarilir. Kullanici uygulama icerisindeki tum olaylari gercek zamanli takip edebilir.

### 5.6 Acil Durdurma (Emergency Stop)

`MainWindow` basliginda yer alan EMERGENCY STOP butonu tum bagli cihazlarin cikislarini aninda kapatir:

```python
def emergency_stop_all(self):
    for name, tab in self.device_tabs.items():
        if tab.controller and tab.is_connected():
            if hasattr(tab.controller, 'output_off'):
                tab.controller.output_off()
            if hasattr(tab.controller, 'load_off'):
                tab.controller.load_off()
```

---

## 6. Controller Detaylari

### 6.1 SorensenController

En basit controller. `BaseDeviceController`'i dogrudan genisletir.

**Desteklenen islemler:**
- `set_voltage(V)`, `set_current(A)`: Parametre dogrulamasi + guc limiti kontrolu
- `set_ovp(V)`, `set_ocp(A)`: Asiri gerilim/akim korumasi
- `output_on()`, `output_off()`: Cikis kontrolu
- `measure_voltage()`, `measure_current()`, `measure_power()`: Olcum
- Guc limiti kontrolu: `_last_voltage * current` veya `voltage * _last_current` hesabini yapar

### 6.2 KeithleyController

En karmasik controller. Iki farkli calisma modu vardir:

**Mod Yonetimi:**
- **Power Supply modu** (`current_mode = 'power'`): Sarj islemi. `:SOUR:VOLT`, `:SOUR:CURR`, `:OUTP ON/OFF` komutlari kullanilir.
- **Battery Test modu** (`current_mode = 'test'`): Desarj islemi. `:BATT:TEST:*`, `:BATT:OUTP ON/OFF` komutlari kullanilir.

Mod gecisi `switch_to_power_supply_mode()` ve `switch_to_battery_test_mode()` ile yapilir. Her geciste:
1. Tum cikislar kapatilir ve dogrulanir.
2. `*CLS` ile buffer temizlenir.
3. Mod komutu gonderilir.
4. `mode_switch_delay` (varsayilan 3s) beklenir.
5. Mod sorgulanarak gecis dogrulanir (3 deneme).

**Olcum Stratejileri:**
- Power Supply modunda: `measure_voltage_current_combined()` tek sorguda V ve I okur.
- Battery Test modunda: `measure_battery_data_buffer()` oncelikle `:BATT:DATA:DATA?` buffer'dan, basarisiz olursa `:MEAS:VOLT?` / `:MEAS:CURR?` direkt sorgularla okur.

**Ethernet vs USB Kisitlamasi:**
Puls testi ve profil calistirma yalnizca USB/GPIB baglantisinda desteklenir. Ethernet ile buffer veri okuma guvenilir calismadigi icin bu testler Ethernet'te engellenir. `is_ethernet_connection()` kontrolu yapilir ve istisnai durum firlatilir.

### 6.3 ProdigitController

**Zamanlama Override'i:**
`send_command()` ve `query_command()` override edilerek DeviceTiming parametreleri uygulanir. `query_command()` icinde `write()` + `read()` ayristirmasi yapilir ve her adimda hesaplanan gecikme eklenir. Ayrica her sorgudan once `connection.clear()` ile buffer temizlenir.

**Olcum Dogrulamasi:**
`get_measurements()` override edilerek uc olcum (V, I, P) atomik sekilde alinir ve tutarlilik kontrolu yapilir: `|P - V*I| > %5` ise guc degeri yeniden hesaplanir.

**Profil Calistirma (`run_cc_profile`):**
- CSV'den akim profili yukler (`load_current_profile()`)
- CC modunda segment segment calistirir
- Her segment'te belirli araliklarla olcum alir
- `threading.Event` tabanli abort mekanizmasi sunar (`request_profile_abort()`)
- Temizlik: 3 denemeyle `load_off()` cagirir; basarisiz olursa log dosyasina uyari yazar

**Guvenlik Limitleri:**
```python
PROFILE_MIN_DWELL_S = 1.0           # Minimum segment suresi
PROFILE_MAX_DURATION_S = 14400.0    # Maksimum toplam sure (~4 saat)
PROFILE_SAFE_CURRENT_A = 120.0      # Surekli akim limiti
PROFILE_MAX_SEGMENTS = 100000       # Maksimum segment sayisi
```

---

## 7. Interface Katmani

### 7.1 SerialInterface

`pyserial` kullanir. Baglanti parametreleri: port, baudrate, bytesize, parity, stopbits, rtscts. Varsayilan baud rate Sorensen icin 9600, Prodigit icin 115200'dur.

Komut gonderim formati: `komut\r\n` (CR+LF sonlandirma).

### 7.2 EthernetInterface

Standart `socket` kutuphanesi kullanir. TCP baglantisi kurar, `TCP_NODELAY` ile Nagle algoritmasini devre disi birakir (dusuk gecikme). Buyuk veri yanitlari icin `_read_large_response()` chunk-based okuma yapar.

### 7.3 VISAInterface

`pyvisa` kutuphanesi kullanir. Hem USB (USBTMC), hem GPIB, hem de VISA-Serial (ASRL) kaynaklarini destekler. ASRL kaynaklar icin ozel seri port yapilandirmasi yapar (Prodigit).

**Kaynak Tespiti:**
`get_available_resources()` statik metodu ile sistemde mevcut VISA kaynaklari listelenir. GUI'deki "Detect" butonu bu metodu cagirir.

---

## 8. Model Katmani -- device_config.py

Tum cihaz bilgilerinin merkezilestirildigi dosya. Su veri yapilarini icerir:

### 8.1 Enum Tanimlari

```python
class InterfaceType(Enum):
    RS232 = "RS232"
    ETHERNET = "Ethernet"
    USB = "USB"
    GPIB = "GPIB"

class DeviceType(Enum):
    SORENSEN_SGX = "Sorensen SGX400-12"
    KEITHLEY_2281S = "Keithley 2281S"
    PRODIGIT_34205A = "Prodigit 34205A"
```

### 8.2 Dataclass'lar

| Sinif | Amac |
|-------|------|
| `ConnectionConfig` | Baglanti parametrelerini tasiyan degismez nesne. Factory metotlari: `create_serial()`, `create_ethernet()`, `create_visa()` |
| `DeviceTiming` | Zamanlama parametreleri (minimum olcum araligi, guvenlik carpani, hesaplanmis gecikmeler) |
| `DeviceSpec` | Cihaz adi, tur, max gerilim/akim/guc, desteklenen arayuzler, varsayilan SCPI komutlari, zamanlama |
| `MeasurementData` | Zaman damgasi, gerilim, akim, guc verilerini tasiyan olcum nesnesi. `to_dict()` ile CSV'ye donusturulur |

---

## 9. Loglama Sistemi

### 9.1 AppLogger (Singleton)

`utils/app_logger.py` icindeki `AppLogger` sinifi Singleton deseniyle calisir. Uc farkli handler'a sahiptir:

| Handler | Seviye | Hedef | Format |
|---------|--------|-------|--------|
| `RotatingFileHandler` | DEBUG | `logs/app_YYYYMMDD.log` (10MB, 5 yedek) | Detayli (tarih, seviye, modul:satir, mesaj) |
| `StreamHandler` | INFO | Konsol (stdout) | Sade (saat, seviye, mesaj) |
| `QueueHandler` | DEBUG | GUI Debug Console | Orta (saat, seviye, modul, mesaj) |

### 9.2 Ozel Logger'lar

- **KeithleyLogger**: Profil calistirma ve test verilerini yapilandirilmis formatta kaydeder. Satirlar: step, mode, set_current, measured_v, measured_i, elapsed, status. CSV ve Excel formatlarinda kayit destegi.
- **ProdigitProfileLogger**: CC profil calistirma verilerini kaydeder. Segment bazli: segment_index, set_current, measured_v/i/p, elapsed, status.
- **DataLogger**: Monitoring sekmesi icin coklu cihaz verisini toplar ve kaydeder.

---

## 10. Guvenlik Mekanizmalari

### 10.1 Cikis Kontrolu

- **Baglanti koparilirken**: `BaseDeviceController.disconnect()` oncelikle `output_off()` veya `load_off()` cagirir (3 deneme).
- **Uygulama kapatilirken**: `MainWindow.on_closing()` tum cihazlarin cikislarini kapatir, calisan thread'lerin bitmesini bekler (timeout ile).
- **Acil durdurma**: EMERGENCY STOP butonu tum cihazlarin cikislarini aninda kapatir.
- **Test hatalarinda**: Her test runner `finally` blogunda cikislari kapatir.

### 10.2 Parametre Dogrulamasi

Tum `set_voltage()`, `set_current()` gibi metodlar:
- Negatif deger kontrolu
- Maksimum limit kontrolu (`device_spec.max_voltage`, `max_current`)
- Guc limiti kontrolu (`V * I <= max_power`)
- Prodigit CC profil: negatif akim reddedilir, minimum segment suresi uygulanir

### 10.3 Timeout Yonetimi

`BaseDeviceController._handle_timeout()` bir timeout durumunda:
1. Olcum devam edip etmedigini kontrol eder (Keithley status register sorgusu).
2. Olcum yoksa cikislari kapatir.
3. Olcum devam ediyorsa cikis kapatma islemi atlanir (cihaz hata vermesini onlemek icin).

### 10.4 Bellek Korumalari

- `DataLogger.MAX_DATA_POINTS = 100_000`: Limit asildiginda en eski %50 silinir.
- `MonitoringTab` ekran goruntusunuu 1000 satirla sinirlar.
- `AppLogger` 10MB dosya siniri + 5 yedek ile rotating loglama yapar.

---

## 11. Cihaza Ozel Akim Profili Destegi

### 11.1 Profil Dosya Formati

CSV veya Excel (xlsx) formatinda, iki zorunlu sutunlu:

```csv
time_s,current_a
0,0.5
10,1.0
20,0.0
30,-1.0
```

- `time_s`: Segment baslangic zamani (saniye)
- `current_a`: Hedef akim (amper)
  - Pozitif degerler: Sarj (Keithley Power Supply modu)
  - Negatif degerler: Desarj (Keithley Battery Test modu)
  - Prodigit: Yalnizca pozitif degerler kabul edilir

`duration_s` otomatik hesaplanir: `sonraki_zaman - mevcut_zaman`. Son segment icin ortalama sure veya varsayilan 10s kullanilir.

### 11.2 Keithley Profil Akisi

```
Profil yuklenir (CSV/Excel)
    |
    v
Segmentler mode'a gore gruplanir (charge/discharge)
    |
    +-- Pozitif akim grubu -> Power Supply moduna gec
    |       -> run_charge_segments()
    |       -> Her segment icin: SOUR:CURR ayarla, OUTP ON, periyodik olcum al
    |
    +-- Negatif akim grubu -> Battery Test moduna gec
    |       -> run_discharge_segments()
    |       -> Sabit desarj akimi, BATT:OUTP ON, buffer'dan olcum al
    |
    +-- Mod degisimleri tekrarlanir
    |
    v
Log dosyasi kaydedilir (CSV/Excel)
```

### 11.3 Prodigit Profil Akisi

```
Profil yuklenir ve dogrulanir
    |
    v
CC moduna gecilir, akim 0A'ya ayarlanir, yuk acilir
    |
    v
Her segment icin:
    -> set_current(hedef_akim)
    -> sample_period araliklarla get_measurements()
    -> Abort event kontrol edilir
    |
    v
Yuk kapatilir, log dosyasi kaydedilir
```

---

## 12. Cikti Dosyalari

| Kaynak | Dosya Adi Formati | Dizin | Icerik |
|--------|-------------------|-------|--------|
| Monitoring | Kullanici secer | Kullanici secer | Tum cihazlarin canli olcum verileri |
| Keithley Puls Testi | `pulse_bt_YYYYMMDD_HHMMSS.csv`, `rest_evoc_YYYYMMDD_HHMMSS.csv` | `logs/` | Puls fazi V/I ve dinlenme fazi VOC/ESR verileri |
| Keithley Batarya Model | `battery_model_slotN_*.csv`, `battery_measurements_*.csv` | `battery_models/` | SOC-VOC-ESR tablosu ve ham olcum verileri |
| Keithley Profil | `keithley_log_YYYYMMDD_HHMMSS.{csv,xlsx}` | `logs/` | Step, mod, ayarlanan/olculen degerler, gecen sure |
| Prodigit Profil | `prodigit_cc_profile_*.{csv,xlsx}` | `logs/` | Segment bazli olcum verileri |

---

## 13. Baglanti Ayarlari Kaliciligi

`ConnectionWidget` baglanti ayarlarini `~/.lab_instruments/connection_settings.json` dosyasinda saklar. JSON yapisi:

```json
{
  "KEITHLEY_2281S_ethernet": {
    "ip": "192.168.1.100",
    "port": 5025
  },
  "SORENSEN_SGX_ethernet": {
    "ip": "192.168.0.200",
    "port": 9221
  },
  "KEITHLEY_2281S_usb": {
    "resource": "USB0::0x05E6::0x2281S::4587429::0::INSTR"
  }
}
```

Seri port ayarlari kaydedilmez, cunku port isimleri oturumlar arasi degisebilir.

---

## 14. Platform Destegi

Uygulama Linux ve Windows'ta calisir.

| Ozellik | Linux | Windows |
|---------|-------|---------|
| GUI (tkinter) | Tam destek | Tam destek |
| RS232 (pyserial) | `/dev/ttyUSB*`, `/dev/ttyS*` | `COM1`, `COM3`, ... |
| Ethernet (socket) | Tam destek | Firewall dikkat |
| USB/GPIB (PyVISA) | Tam destek | NI-VISA driver gerekli |
| PyInstaller paketleme | Desteklenir | `build_windows.bat` ile |

Windows'a ozel hata mesajlari (driver bulunamadi, port erisim hatasi, firewall engeli) tum interface siniflarinda tanimlanmistir.

---

## 15. Yeni Cihaz Ekleme Rehberi

Yeni bir laboratuvar cihazi eklemek icin su adimlar izlenir:

1. **device_config.py**: `DeviceType` enum'una yeni giris, `DEVICE_SPECS` sozlugune `DeviceSpec` tanimla.
2. **Controller olustur**: `BaseDeviceController`'dan turet, `measure_voltage()` ve `measure_current()` somutlastir, cihaza ozel metodlari ekle.
3. **GUI sekmesi olustur**: `DeviceTab`'dan turet, `create_controls()` override et.
4. **MainWindow'a ekle**: `create_device_tabs()` icerisinde yeni sekmeyi notebook'a ekle.
5. **Gerekirse interface ekle**: Yeni bir haberlesme protokolu gerekiyorsa `DeviceInterface`'den turet.

---

## 16. Bagimliliklar

| Paket | Amac | Zorunlu |
|-------|------|---------|
| tkinter | GUI | Evet (Python ile gelir) |
| pyserial | RS232 haberlesmesi | Evet |
| pyvisa | USB/GPIB haberlesmesi | Hayir (yoksa USB/GPIB devredisi) |
| pandas | Profil dosyasi okuma/yazma | Profil islemleri icin |
| openpyxl | Excel dosya destegi | Excel islemleri icin |
| Pillow (PIL) | Logo gosterimi | Hayir (yoksa logo goruntulenmez) |
| matplotlib | Grafik cizimi | Hayir (yoksa grafik devredisi) |
