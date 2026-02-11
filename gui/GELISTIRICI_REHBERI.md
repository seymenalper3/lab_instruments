# Gelistirici Rehberi - Lab Instruments GUI

Bu dokuman, EV batarya test sistemi GUI uygulamasinin gelistiriciler icin teknik rehberidir.

## Sistem Genel Bakis

GUI uygulamasi 3 laboratuvar cihazini kontrol eder:

| Cihaz | Tipi | Baglanti |
|-------|------|----------|
| Keithley 2281S | Batarya Simulator | USB / Ethernet / GPIB |
| Sorensen SGX400-12D | Guc Kaynagi | RS232 / Ethernet / GPIB |
| Prodigit 34205A | Elektronik Yuk | RS232 / USB |

## Dizin Yapisi

```
gui/
  main.py                          # Uygulama giris noktasi
  models/
    device_config.py               # DeviceType, DeviceSpec, DeviceTiming, DEVICE_SPECS
  controllers/
    base_controller.py             # BaseDeviceController (abstract)
    sorensen_controller.py         # SorensenController
    keithley_controller.py         # KeithleyController
    prodigit_controller.py         # ProdigitController
    keithley/
      tests/
        pulse_test.py              # KeithleyPulseTest
        battery_model.py           # KeithleyBatteryModel
        profile_runner.py          # KeithleyProfileRunner
  gui/
    main_window.py                 # MainWindow - ana pencere
    device_tab.py                  # DeviceTab - tum tablarin base sinifi
    connection_widget.py           # ConnectionWidget - baglanti arayuzu
    keithley_tab.py                # KeithleyTab
    sorensen_tab.py                # SorensenTab
    prodigit_tab.py                # ProdigitTab
    monitoring_tab.py              # MonitoringTab - izleme ve loglama
    debug_console_tab.py           # DebugConsoleTab - log konsolu
  interfaces/
    base_interface.py              # DeviceInterface (abstract)
    serial_interface.py            # SerialInterface (RS232)
    ethernet_interface.py          # EthernetInterface
    visa_interface.py              # VISAInterface (USB/GPIB)
  utils/
    data_logger.py                 # DataLogger - genel veri kaydi
    keithley_logger.py             # KeithleyLogger - Keithley ozel loglama
    prodigit_logger.py             # ProdigitProfileLogger - Prodigit profil loglama
    app_logger.py                  # Uygulama seviyesi loglama
  tests/
    test_structure.py              # Import zinciri testi
    test_prod_digit_profile.py     # Prodigit profil testi
  examples/
    example_profile.csv            # Ornek profil dosyasi
  requirements.txt                 # Bagimliliklar
```

---

## 1. Yeni Cihaz Ekleme Adimlari

Sisteme yeni bir cihaz eklemek icin asagidaki 4 adimi takip edin.

### Adim 1: device_config.py'ye DeviceSpec Ekle

Dosya: `models/device_config.py`

Oncelikle `DeviceType` enum'a yeni cihazi ekleyin:

```python
class DeviceType(Enum):
    SORENSEN_SGX = "Sorensen SGX400-12"
    KEITHLEY_2281S = "Keithley 2281S"
    PRODIGIT_34205A = "Prodigit 34205A"
    YENI_CIHAZ = "Yeni Cihaz Model"           # <-- Yeni eklenen
```

Ardindan `DEVICE_SPECS` sozlugune yeni `DeviceSpec` ekleyin:

```python
DEVICE_SPECS = {
    # ... mevcut cihazlar ...

    DeviceType.YENI_CIHAZ: DeviceSpec(
        name="Yeni Cihaz Model XYZ",
        device_type=DeviceType.YENI_CIHAZ,
        max_voltage=50.0,                      # Cihaz kilavuzundan
        max_current=10.0,                      # Cihaz kilavuzundan
        max_power=500.0,                       # Opsiyonel
        supported_interfaces=[
            InterfaceType.USB,
            InterfaceType.RS232
        ],
        timing=DeviceTiming(                   # Opsiyonel - kilavuzdaki min olcum araligi
            min_measurement_interval_s=0.050,
            safety_factor=1.2
        ),
        default_commands={
            'identify': '*IDN?',
            'set_voltage': 'SOUR:VOLT {}',
            'set_current': 'SOUR:CURR {}',
            'output_on': 'OUTP ON',
            'output_off': 'OUTP OFF',
            'measure_voltage': 'MEAS:VOLT?',
            'measure_current': 'MEAS:CURR?',
            'query_error': 'SYST:ERR?'
        }
    )
}
```

Onemli noktalar:
- `max_voltage`, `max_current`, `max_power` degerlerini cihaz kilavuzundan alin.
- `timing` parametresi opsiyoneldir. Prodigit orneginde oldugu gibi, kilavuzda belirtilen minimum olcum araligi varsa ekleyin.
- `default_commands` sozlugundeki komutlar cihazin SCPI komut setine gore belirlenir.
- Ornek komut anahtarlari: `identify`, `set_voltage`, `set_current`, `output_on`, `output_off`, `measure_voltage`, `measure_current`, `query_error`

### Adim 2: Controller Olustur

Dosya: `controllers/yeni_cihaz_controller.py`

`BaseDeviceController` sinifini temel alarak yeni controller olusturun:

```python
#!/usr/bin/env python3
"""
Yeni Cihaz Controller
"""
import logging
from typing import Optional
from controllers.base_controller import BaseDeviceController
from models.device_config import DEVICE_SPECS, DeviceType

logger = logging.getLogger(__name__)


class YeniCihazController(BaseDeviceController):
    """Yeni Cihaz Model XYZ Controller"""

    def __init__(self, interface):
        super().__init__(interface, DEVICE_SPECS[DeviceType.YENI_CIHAZ])

    # --- Zorunlu metodlar (abstract) ---

    def measure_voltage(self) -> Optional[float]:
        """Gerilim olcumu"""
        try:
            cmd = self.device_spec.default_commands['measure_voltage']
            response = self.query_command(cmd)
            return float(response)
        except (ValueError, TypeError):
            return None

    def measure_current(self) -> Optional[float]:
        """Akim olcumu"""
        try:
            cmd = self.device_spec.default_commands['measure_current']
            response = self.query_command(cmd)
            return float(response)
        except (ValueError, TypeError):
            return None

    # --- Opsiyonel metodlar ---

    def set_voltage(self, voltage: float):
        """Gerilim ayarla"""
        if voltage < 0 or voltage > self.device_spec.max_voltage:
            raise ValueError(
                f"Gerilim 0-{self.device_spec.max_voltage}V araliginda olmali"
            )
        cmd = self.device_spec.default_commands['set_voltage'].format(voltage)
        self.send_command(cmd)

    def set_current(self, current: float):
        """Akim limiti ayarla"""
        if current < 0 or current > self.device_spec.max_current:
            raise ValueError(
                f"Akim 0-{self.device_spec.max_current}A araliginda olmali"
            )
        cmd = self.device_spec.default_commands['set_current'].format(current)
        self.send_command(cmd)

    def output_on(self):
        """Cikisi ac"""
        logger.warning("Cikis aciliyor - guvenlik kritik islem")
        cmd = self.device_spec.default_commands['output_on']
        self.send_command(cmd, check_errors=True)
        logger.info("Cikis basariyla acildi")

    def output_off(self):
        """Cikisi kapat"""
        logger.info("Cikis kapatiliyor")
        cmd = self.device_spec.default_commands['output_off']
        self.send_command(cmd, check_errors=True)
        logger.info("Cikis basariyla kapatildi")
```

Onemli kurallar:
- SCPI komutlarini **asla** hardcoded yazmayin. Her zaman `self.device_spec.default_commands['key']` uzerinden alin.
- `measure_voltage()` ve `measure_current()` zorunludur (abstract metod).
- `output_on()` cagrildiginda `logger.warning()`, `output_off()` icin `logger.info()` kullanin.
- Prodigit orneginde oldugu gibi, ozel timing gereksinimleri varsa `send_command()` ve `query_command()` override edilebilir:

```python
# Prodigit ornegi: timing icin override
def send_command(self, command: str, check_errors: bool = False):
    if not self.connected:
        raise Exception("Device not connected")
    self.interface.write(command)
    delay = self.device_spec.timing.send_delay_s if self.device_spec.timing else 0.1
    time.sleep(delay)

def query_command(self, command: str, check_errors: bool = False) -> str:
    if not self.connected:
        raise Exception("Device not connected")
    try:
        self.interface.connection.clear()
    except Exception:
        pass
    self.interface.write(command)
    write_delay = self.device_spec.timing.query_write_delay_s if self.device_spec.timing else 0.08
    time.sleep(write_delay)
    response = self.interface.read()
    read_delay = self.device_spec.timing.query_read_delay_s if self.device_spec.timing else 0.03
    time.sleep(read_delay)
    return response.strip()
```

### Adim 3: GUI Tab Olustur

Dosya: `gui/yeni_cihaz_tab.py`

`DeviceTab` sinifini temel alarak yeni tab olusturun:

```python
#!/usr/bin/env python3
"""
Yeni Cihaz device tab
"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui.device_tab import DeviceTab
from models.device_config import DEVICE_SPECS, DeviceType
from controllers.yeni_cihaz_controller import YeniCihazController
import threading


class YeniCihazTab(DeviceTab):
    """Yeni Cihaz kontrol tabi"""

    def __init__(self, parent):
        super().__init__(
            parent,
            DEVICE_SPECS[DeviceType.YENI_CIHAZ],
            YeniCihazController
        )
        self.test_threads = []

    def create_controls(self):
        """Cihaza ozel kontrolleri olustur"""
        # Gerilim ayari
        ttk.Label(self.control_frame, text="Voltage (V):").grid(
            row=0, column=0, sticky='w', padx=5, pady=2
        )
        self.voltage_entry = ttk.Entry(self.control_frame, width=10)
        self.voltage_entry.grid(row=0, column=1, padx=5, pady=2)
        self.voltage_entry.insert(0, "0")

        # Akim ayari
        ttk.Label(self.control_frame, text="Current (A):").grid(
            row=0, column=2, sticky='w', padx=5, pady=2
        )
        self.current_entry = ttk.Entry(self.control_frame, width=10)
        self.current_entry.grid(row=0, column=3, padx=5, pady=2)
        self.current_entry.insert(0, "0")

        # Butonlar
        btn_frame = ttk.Frame(self.control_frame)
        btn_frame.grid(row=1, column=0, columnspan=4, pady=10)

        ttk.Button(btn_frame, text="Set Parameters",
                   command=self.set_parameters).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Output ON",
                   command=self.output_on).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Output OFF",
                   command=self.output_off).pack(side='left', padx=5)

    def set_parameters(self):
        """Parametreleri ayarla"""
        def _set():
            voltage = float(self.voltage_entry.get())
            current = float(self.current_entry.get())
            self.controller.set_voltage(voltage)
            self.controller.set_current(current)
            return "Parametreler ayarlandi"
        result = self.safe_execute(_set)
        if result:
            messagebox.showinfo("Basarili", result)

    def output_on(self):
        """Cikisi ac"""
        def _on():
            self.controller.output_on()
            return "Cikis acildi"
        result = self.safe_execute(_on)
        if result:
            messagebox.showinfo("Basarili", result)

    def output_off(self):
        """Cikisi kapat"""
        def _off():
            self.controller.output_off()
            return "Cikis kapatildi"
        result = self.safe_execute(_off)
        if result:
            messagebox.showinfo("Basarili", result)
```

DeviceTab base sinifi asagidakileri otomatik saglar:
- Baglanti widget'i (`ConnectionWidget`) - arayuz tipi secimi ve connect/disconnect butonlari
- Durum cubugu (status bar) - baglanti durumu ve hata mesajlari
- Olcum paneli - voltage, current ve opsiyonel power goruntulemesi
- `safe_execute()` metodu - hata yakalama ve kullaniciya bildirim
- `on_connect()` / `on_disconnect()` - baglanti yonetimi

Uzun sureli islemler icin **daemon thread** kullanin:

```python
def run_long_test(self):
    """Uzun sureli testi baslat"""
    if not self.is_connected():
        messagebox.showerror("Hata", "Cihaz bagli degil")
        return

    test_thread = threading.Thread(
        target=self._run_long_test_thread,
        args=(param1, param2)
    )
    test_thread.daemon = True           # Daemon thread - uygulama kapaninca sonlanir
    self.test_threads.append(test_thread)
    test_thread.start()

def _run_long_test_thread(self, param1, param2):
    """Arka plan thread'inde calisan test"""
    try:
        # Test islemi...
        result = self.controller.some_long_operation()

        # GUI guncellemesi main thread'de yapilmali
        self.frame.after(0, lambda r=result: self._test_completed(r))
    except Exception as e:
        error_msg = str(e)
        self.frame.after(0, lambda msg=error_msg: self._test_failed(msg))

def _test_completed(self, result):
    """Main thread'de calisir - GUI guncelle"""
    messagebox.showinfo("Tamamlandi", f"Test basarili: {result}")

def _test_failed(self, error_msg):
    """Main thread'de calisir - hata goster"""
    messagebox.showerror("Hata", f"Test basarisiz: {error_msg}")
```

### Adim 4: MainWindow'a Kaydet

Dosya: `gui/main_window.py`

Import ekleyin:

```python
from gui.yeni_cihaz_tab import YeniCihazTab
```

`create_device_tabs()` metoduna yeni tabi ekleyin:

```python
def create_device_tabs(self):
    """Create all device tabs"""
    # ... mevcut tablar ...

    # Yeni Cihaz tab
    self.device_tabs['yeni_cihaz'] = YeniCihazTab(self.notebook)
    self.notebook.add(
        self.device_tabs['yeni_cihaz'].frame,
        text="Yeni Cihaz Model"
    )
    logger.debug("Yeni Cihaz tab created")
```

Bu kadar. Monitoring tab otomatik olarak yeni cihazin baglanti callback'lerini ayarlar.
`create_monitoring_tab()` metodu, `self.device_tabs` sozlugundeki tum cihazlar icin
connect/disconnect wrapper'lari olusturur. Yeni cihaz baglandiginda monitoring tab'a
otomatik kaydedilir.

---

## 2. Delegation Pattern (Keithley Ornegi)

Keithley controller kompleks test mantigi icerdigi icin delegation (kompozisyon) patterni kullanilir.
Test mantigi ayri siniflar halinde `controllers/keithley/tests/` altinda tutulur.

### Yapi

```
controllers/keithley/tests/
    __init__.py
    pulse_test.py        # KeithleyPulseTest
    battery_model.py     # KeithleyBatteryModel
    profile_runner.py    # KeithleyProfileRunner
```

### Nasil Calisir

Controller, test siniflarini `__init__` metodunda olusturur:

```python
class KeithleyController(BaseDeviceController):
    def __init__(self, interface):
        super().__init__(interface, DEVICE_SPECS[DeviceType.KEITHLEY_2281S])

        # Test runner'lar (kompozisyon)
        self._pulse_test = KeithleyPulseTest(self)
        self._battery_model = KeithleyBatteryModel(self)
        self._profile_runner = KeithleyProfileRunner(self)
```

Test runner sinifi, parent controller referansini alir:

```python
class KeithleyPulseTest:
    def __init__(self, controller):
        self.controller = controller

    def run(self, pulses=5, pulse_time=60.0, ...):
        # self.controller uzerinden cihaz komutlari gonderilir
        self.controller.send_command(':BATT:OUTP ON')
        v, i, rel = self.controller.measure_battery_data_buffer()
        # ...
```

Controller, public API'yi delegate eder:

```python
def run_battery_model_test(self, **kwargs):
    # Parametre dogrulama burada yapilir
    if not self.connected:
        raise Exception("Device not connected")
    # ...
    # Asil islem module delegate edilir
    return self._battery_model.run(**kwargs)

def run_current_profile(self, profile_path, **kwargs):
    return self._profile_runner.run(profile_path=profile_path, **kwargs)
```

### Avantajlar

- Her test modulu bagimsiz olarak test edilebilir
- Controller sinifi sismez (1000+ satir yerine mantiksal bolunme)
- Yeni test tipleri eklemek kolay
- Geriye donuk uyumluluk korunur (public API degismez)

---

## 3. Threading Modeli

Uzun sureli test islemleri (pulse test, batarya model, profil calistirma) arka plan thread'lerinde calisir.

### Temel Kurallar

**1. Daemon thread kullanin:**

```python
test_thread = threading.Thread(target=self._run_test_thread, args=(...))
test_thread.daemon = True    # Uygulama kapaninca thread otomatik sonlanir
self.test_threads.append(test_thread)
test_thread.start()
```

**2. Busy flag ile cihaz durumunu isaretleyin:**

```python
# Controller ici - test baslarken
self.set_busy(True)

# Controller ici - test bitince (MUTLAKA finally blogunda)
try:
    # test islemi...
finally:
    self.set_busy(False)    # Her durumda temizle
```

`set_busy()` ve `is_busy()` metodlari `threading.Lock()` ile korunur:

```python
class BaseDeviceController:
    def __init__(self, ...):
        self._busy_lock = threading.Lock()

    def set_busy(self, busy: bool):
        with self._busy_lock:
            self.busy = busy

    def is_busy(self) -> bool:
        with self._busy_lock:
            return self.busy
```

**3. GUI guncellemelerini main thread'e gonderin:**

tkinter thread-safe degildir. Arka plan thread'inden GUI guncellemesi yapmak icin
`self.frame.after(0, callback)` kullanin:

```python
def _run_test_thread(self, ...):
    try:
        result = self.controller.run_test(...)
        # GUI guncellemesi main thread'de
        self.frame.after(0, lambda r=result: self._on_test_complete(r))
    except Exception as e:
        error_msg = str(e)
        self.frame.after(0, lambda msg=error_msg: self._on_test_error(msg))
```

**4. Monitoring tab busy cihazlari "[BUSY]" ile gosterir:**

Monitoring tab, her cihazin `is_available_for_monitoring()` metodunu kontrol eder:

```python
def is_available_for_monitoring(self) -> bool:
    return self.is_connected() and not self.is_busy()
```

Busy olan cihazlardan olcum alinmaz, boylece test islemini bozmaz.

**5. Uygulama kapanirken thread temizligi:**

`MainWindow.on_closing()` metodu, tum test thread'lerinin tamamlanmasini bekler
(timeout ile) ve ardindan cihazlari disconnect eder:

```python
def on_closing(self):
    for name, tab in self.device_tabs.items():
        if hasattr(tab, 'test_threads'):
            for thread in tab.test_threads:
                if thread.is_alive():
                    thread.join(timeout=3.0)
    # Sonra disconnect
    for name, tab in self.device_tabs.items():
        if tab.is_connected():
            tab.on_disconnect()
```

---

## 4. Test Yazma ve Calistirma

### Test Dosyalari

Mevcut testler `gui/tests/` altindadir:

| Dosya | Aciklama |
|-------|----------|
| `test_structure.py` | Import zinciri testi |
| `test_prod_digit_profile.py` | Prodigit profil yuklemesi testi |
| `test_monitoring_fix.py` | Monitoring duzeltme testi |
| `test_pulse_simple.py` | Basit pulse test |

### Cihaz Olmadan Import Zinciri Testi

Yeni bir modul ekledikten sonra, import zincirinin calistigini dogrulayin.
Bu testler fiziksel cihaz gerektirmez:

```bash
cd gui
python -c "from gui.main_window import MainWindow; print('MainWindow OK')"
python -c "from controllers.keithley_controller import KeithleyController; print('Keithley OK')"
python -c "from controllers.prodigit_controller import ProdigitController; print('Prodigit OK')"
python -c "from controllers.sorensen_controller import SorensenController; print('Sorensen OK')"
```

Yeni cihaz ekledikten sonra:

```bash
cd gui
python -c "from controllers.yeni_cihaz_controller import YeniCihazController; print('YeniCihaz OK')"
python -c "from gui.yeni_cihaz_tab import YeniCihazTab; print('YeniCihazTab OK')"
```

### GUI Baslatma Testi

Tum tablarin gorundugunun hizli dogrulamasi:

```bash
cd gui
python main.py
```

Beklenen sonuc:
- Ana pencere acilir (1200x800)
- Tum cihaz tablari gorunur (Sorensen, Keithley, Prodigit + yeni ekledikleriniz)
- Monitoring & Logging tabi gorunur
- Debug Console tabi gorunur
- Emergency Stop butonu gorunur

### Yeni Test Dosyasi Olusturma

```python
#!/usr/bin/env python3
"""
Test: Yeni cihaz controller import ve temel islevsellik
"""
import sys
sys.path.insert(0, '.')

def test_import():
    """Import zinciri calisiyor mu?"""
    from controllers.yeni_cihaz_controller import YeniCihazController
    from models.device_config import DEVICE_SPECS, DeviceType
    assert DeviceType.YENI_CIHAZ in DEVICE_SPECS
    print("Import testi BASARILI")

def test_device_spec():
    """DeviceSpec dogru tanimlanmis mi?"""
    from models.device_config import DEVICE_SPECS, DeviceType
    spec = DEVICE_SPECS[DeviceType.YENI_CIHAZ]
    assert spec.max_voltage > 0
    assert spec.max_current > 0
    assert 'identify' in spec.default_commands
    assert 'measure_voltage' in spec.default_commands
    assert 'measure_current' in spec.default_commands
    print("DeviceSpec testi BASARILI")

if __name__ == '__main__':
    test_import()
    test_device_spec()
    print("Tum testler BASARILI")
```

---

## 5. Git Workflow

### Branch Stratejisi

- `main` branch: kararli surum, dogrudan commit yapilmaz
- Feature branch'ler: `feature/yeni-ozellik`
- Bugfix branch'ler: `fix/bug-aciklamasi`
- Refactoring branch'ler: `refactor/aciklama`

### Commit Mesaj Formati

Commit mesajlari prefix ile baslar:

| Prefix | Kullanim |
|--------|----------|
| `feat:` | Yeni ozellik |
| `fix:` | Hata duzeltme |
| `refactor:` | Kod yeniden duzenleme |
| `docs:` | Dokumantasyon |
| `test:` | Test ekleme/duzeltme |

Ornek commit mesajlari (mevcut repo'dan):

```
refactor: Modularize Keithley controller with delegation pattern
feat: Add Excel file support for profiles and logs
fix: Add Prodigit CC CSV profile support and documentation
```

### Commit Oncesi Kontrol Listesi

1. Import zinciri testini calistirin:
   ```bash
   cd gui
   python -c "from gui.main_window import MainWindow; print('OK')"
   ```

2. GUI'nin acildigini dogrulayin:
   ```bash
   cd gui
   python main.py
   ```

3. Eklediginiz testleri calistirin:
   ```bash
   cd gui
   python tests/test_structure.py
   ```

---

## 6. Bagimlilik Yonetimi

### requirements.txt

Dosya: `gui/requirements.txt`

```
pyserial>=3.5           # RS232 baglanti (zorunlu)
pyvisa>=1.11.3          # VISA framework (zorunlu)
pyvisa-py>=0.5.2        # Pure-Python VISA backend (zorunlu)
pandas>=1.3.0           # Profil ve veri islemleri
openpyxl>=3.0.0         # Excel dosya destegi
Pillow>=9.0.0           # Logo gorseli icin
```

### Zorunlu ve Opsiyonel Bagimliliklar

| Paket | Zorunlu? | Kullanan Modul |
|-------|----------|----------------|
| pyserial | Evet | interfaces/serial_interface.py |
| pyvisa | Evet | interfaces/visa_interface.py |
| pyvisa-py | Evet | VISA backend |
| pandas | Hayir | Profil yuklemesi, veri isleme |
| openpyxl | Hayir | Excel dosya okuma/yazma |
| Pillow | Hayir | Logo gorseli (main_window.py) |
| matplotlib | Hayir | Monitoring tab grafik cizimi |

### Lazy Import Pattern

Opsiyonel bagimliliklar kullanildigi yerde import edilir, dosya basinda degil.
Bu sayede paket yuklu olmasa bile uygulama calisabilir.

```python
# YANLIS - top-level import
# Paket yuklu degilse uygulama hic acilmaz
import pandas as pd

class MyController:
    def load_profile(self, path):
        df = pd.read_csv(path)
        ...
```

```python
# DOGRU - lazy import
# Paket yuklu degilse sadece bu metod hata verir, uygulama calisir
class MyController:
    def load_profile(self, path):
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas paketi gerekli: pip install pandas")
        df = pd.read_csv(path)
        ...
```

Monitoring tab'daki matplotlib ornegi:

```python
# gui/monitoring_tab.py basinda
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Matplotlib not available - plotting disabled")
```

Excel dosya destegi ornegi (Prodigit controller'dan):

```python
if str(path).endswith('.xlsx') or str(path).endswith('.xls'):
    try:
        import openpyxl  # Lazy import
        df = pd.read_excel(path, engine='openpyxl')
    except ImportError:
        raise Exception("Excel support requires openpyxl. Install: pip install openpyxl")
else:
    df = pd.read_csv(path)
```

---

## 7. Kod Standartlari

### SCPI Komutlari

SCPI komutlari `device_config.py` icinde tanimlanir. Controller kodunda hardcoded SCPI komutu yazilmaz.

```python
# YANLIS
def output_on(self):
    self.send_command('OUTP ON')

# DOGRU
def output_on(self):
    cmd = self.device_spec.default_commands['output_on']
    self.send_command(cmd)
```

Istisna: Keithley controller'daki mod-spesifik komutlar (`:BATT:OUTP ON` gibi) device_config'de
tanimlanmis komutlara ek olarak kullanilabilir. Ancak genel komutlar her zaman
`default_commands` uzerinden alinmalidir.

### Timing Parametreleri

Cihaz iletisim zamanlama parametreleri `DeviceTiming` dataclass'i ile tanimlanir:

```python
@dataclass
class DeviceTiming:
    min_measurement_interval_s: float = 0.050  # Kilavuzdaki minimum aralik
    safety_factor: float = 1.2                 # %20 guvenlik payasi

    @property
    def send_delay_s(self) -> float:
        return self.min_measurement_interval_s * self.safety_factor

    @property
    def query_write_delay_s(self) -> float:
        return self.min_measurement_interval_s * 1.1

    @property
    def query_read_delay_s(self) -> float:
        return 0.010
```

Timing degerleri cihaz kilavuzundan alinir ve `device_config.py` icinde tek bir yerde tanimlanir.
Controller kodu, hardcoded `time.sleep()` degerleri yerine `self.device_spec.timing` kullanir.

### Print Statement ve Loglama

- Print statement'larda emoji kullanilmaz (Windows terminal uyumlulugu)
- Guvenlik kritik islemler `logger.warning()` ile loglanir (output_on gibi)
- Normal islemler `logger.info()` ile loglanir
- Debug bilgileri `logger.debug()` ile loglanir
- Hata durumlari `logger.error()` ile loglanir

```python
# YANLIS
print("Cikis acildi")

# DOGRU
logger.warning("Turning output ON - safety critical operation")
logger.info("Output turned ON successfully")
```

### Busy Flag Temizligi

Busy flag her zaman `finally` blogu icinde temizlenir. Aksi halde, bir hata
durumunda cihaz sonsuza kadar BUSY kalir ve monitoring calismazc

```python
def run_test(self):
    self.set_busy(True)
    try:
        # test islemi...
    except Exception as e:
        # hata isleme...
        raise
    finally:
        self.set_busy(False)    # MUTLAKA burada temizle
```

### Output Kapama Guvenligi

Disconnect islemi sirasinda output'lar 3 deneme ile kapatilmaya calisilir.
Yeni controller yazarken ayni patterni takip edin:

```python
# BaseDeviceController.disconnect() icinde otomatik yapilir:
# 1. output_off() veya load_off() 3 kez denenir
# 2. local_mode() cagrilir (varsa)
# 3. interface.disconnect() cagrilir
```

### Parametre Dogrulama

Kullanicidan gelen parametreler controller metodlarinda dogrulanir:

```python
def set_voltage(self, voltage: float):
    if voltage < 0 or voltage > self.device_spec.max_voltage:
        raise ValueError(f"Voltage must be between 0 and {self.device_spec.max_voltage}V")
    # ...
```

Guc limiti kontrolu de yapilmalidir (varsa):

```python
if self.device_spec.max_power:
    power = voltage * current
    if power > self.device_spec.max_power:
        raise ValueError(
            f"Power limit exceeded: {power:.1f}W > {self.device_spec.max_power}W"
        )
```

---

## Hizli Referans: Yeni Cihaz Ekleme Ozeti

| Adim | Dosya | Islem |
|------|-------|-------|
| 1 | `models/device_config.py` | DeviceType enum + DEVICE_SPECS dict |
| 2 | `controllers/yeni_cihaz_controller.py` | BaseDeviceController'dan turetme |
| 3 | `gui/yeni_cihaz_tab.py` | DeviceTab'dan turetme |
| 4 | `gui/main_window.py` | Import + create_device_tabs() |
| 5 | Test | Import testi + GUI testi |
