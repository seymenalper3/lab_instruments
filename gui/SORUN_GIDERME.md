# Sorun Giderme Kilavuzu

Bu belge, EV batarya test sistemi GUI uygulamasinin sorun giderme rehberidir. Sistem asagidaki uc cihazi kontrol eder:

- **Keithley 2281S** - Batarya Simulatoru (USB / Ethernet / GPIB)
- **Sorensen SGX400-12D** - Guc Kaynagi (RS232 / Ethernet / GPIB)
- **Prodigit 34205A** - Elektronik Yuk (RS232 / USB)

---

## 1. Baglanti Sorunlari

### VISA / USB / GPIB

**"PyVISA not available" hatasi:**

PyVISA ve backend paketi yuklu degil. Asagidaki komutla yukleyin:

```bash
pip install pyvisa pyvisa-py
```

**Platform farkliliklari:**

- **Linux:** `pyvisa-py` backend olarak kullanilir, NI-VISA driver yuklemek gerekmez. Ancak USB cihazlar icin `libusb` kutuphanesi gerekebilir. Dagitima gore `sudo apt install libusb-1.0-0` veya benzeri komutla yuklenebilir.
- **Windows:** NI-VISA driver kurulmalidir. [ni.com](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html) adresinden indirip yukleyin.

**VISA resource string ornekleri:**

```
USB0::0x05E6::0x2281::SERIAL::INSTR
GPIB0::24::INSTR
TCPIP0::192.168.1.100::5025::SOCKET
```

**"Resource not found" hatasi:**

Cihaz fiziksel olarak bagli mi ve acik mi kontrol edin. Asagidaki komutla bagli cihazlari listeleyin:

```bash
python -c "import pyvisa; rm = pyvisa.ResourceManager(); print(rm.list_resources())"
```

Bu komut bos liste donduruyorsa cihaz bilgisayara bagli degil veya driver eksik demektir.

### Serial / RS232

**Port isimleri:**

- **Linux:** `/dev/ttyUSB0` veya `/dev/ttyS0`
- **Windows:** `COM3`, `COM4` vb. (Device Manager'dan port numarasini kontrol edin)

**Baud rate ayarlari:**

Baud rate cihaz ayariyla uyusmalidir. Varsayilan degerler:

| Cihaz | Baud Rate |
|-------|-----------|
| Prodigit 34205A | 115200 |
| Sorensen SGX400-12D | 9600 |

**"Permission denied" hatasi:**

- **Linux:** Kullanicinin `dialout` grubunda olmasi gerekir. Asagidaki komutu calistirin ve oturumu kapatip tekrar acin:

  ```bash
  sudo usermod -aG dialout $USER
  ```

- **Windows:** Port baska bir program tarafindan kullaniliyor olabilir. Diger terminal programlarini (PuTTY, Tera Term vb.) kapatin.

### Ethernet

**Genel kontroller:**

- IP adresi ve port numarasinin dogru oldugunu dogrulayin.
- Keithley 2281S varsayilan port numarasi: **5025**
- Firewall kurallarinin baglantiya izin verdiginden emin olun.

**Onemli kisitlama:** Keithley 2281S cihazinda pulse test ve profil calistirma Ethernet baglantisi uzerinden desteklenmez. Bu ozellikler icin **USB baglanti** kullanin.

---

## 2. Import / Baslatma Hatalari

Asagidaki tablo, sik karsilasilan modul hatalarini ve cozumlerini listeler:

| Hata Mesaji | Cozum | Aciklama |
|-------------|-------|----------|
| `ModuleNotFoundError: No module named 'pandas'` | `pip install pandas` | pandas lazy import olarak yuklenir; GUI pandas olmadan acilir ancak profil yukleme icin gereklidir |
| `ModuleNotFoundError: No module named 'openpyxl'` | `pip install openpyxl` | Sadece Excel (.xlsx) dosyalari icin gereklidir, CSV kullanirken gerekmez |
| `ModuleNotFoundError: No module named 'pyvisa'` | `pip install pyvisa pyvisa-py` | USB ve GPIB baglanti icin gereklidir |
| `ModuleNotFoundError: No module named 'PIL'` | `pip install Pillow` | Logo gosterimi icin gereklidir, yuklu olmasa da GUI calisir |
| `ModuleNotFoundError: No module named 'matplotlib'` | `pip install matplotlib` | Grafik cizimi icin gereklidir, yuklu olmasa da GUI calisir |

**Genel cozum:** Tum bagimliliklari tek seferde yuklemek icin:

```bash
pip install -r requirements.txt
```

---

## 3. Timing / Timeout Sorunlari

### Prodigit 34205A

Prodigit 34205A cihazinin kilavuz spesifikasyonuna gore olcum komutlari arasinda **minimum 50ms bekleme** suresi gereklidir.

Timing parametreleri `device_config.py` dosyasindaki `DeviceTiming` sinifi ile konfigure edilir. Mevcut ayarlar:

| Parametre | Deger |
|-----------|-------|
| `send` | 60ms |
| `query_write` | 55ms |
| `query_read` | 10ms |

**"Timeout" hatasi aliyorsaniz:**

- Baud rate ayarinin dogru oldugunu kontrol edin (115200 olmali).
- Seri kablo uzunlugunu mumkun oldugunca kisa tutun.
- Farkli bir USB-Serial donusturucu deneyin.

### Keithley 2281S

- Mod degisimi (ornegin simulatordan olcume gecis) **3 saniyeye kadar** surebilir (`mode_switch_delay=3.0`).
- Ethernet baglantisinda timeout varsayilan degeri **5 saniye**.
- VISA timeout varsayilan degeri **5000ms**.
- Buffer veri okuma islemi Ethernet uzerinden guvenilir degildir. Veri okuma icin **USB baglanti** kullanin.

### Sorensen SGX400-12D

Standart SCPI timing kullanir, ozel gecikme ayarina gerek yoktur.

---

## 4. Test Sirasinda Sorunlar

**"[BUSY]" gosteriliyor monitoring sekmesinde:**

Bu normal bir durumdur. Cihaz test modundayken monitoring okumalari yapilamaz. Test bitene kadar bekleyin, test tamamlandiginda monitoring degerleri tekrar goruntulenir.

**"Device is busy with another operation" hatasi:**

Onceki test veya islem henuz tamamlanmadi. Islemin bitmesini bekleyin. Eger islem takildiysa cihazi resetlemeniz gerekebilir.

**Pulse test Ethernet uzerinden calismaz:**

Pulse test, Keithley 2281S cihazinda yalnizca USB baglanti uzerinden desteklenir. Ethernet baglantisini kesin ve USB ile tekrar baglanin.

**Profil calistirma sirasinda mod degisimi hatasi:**

Cihazin onceki islemi tamamlamasini bekleyin. Mod degisimi 3 saniyeye kadar surebilir. Acele etmeden islemin sonlanmasini bekleyip tekrar deneyin.

**Battery model testi cok uzun suruyor:**

Battery model testleri saatlerce surebilir, bu normaldir. Testi kesmeden tamamlanmasini bekleyin. Erken sonlandirma veri kaybina neden olabilir.

---

## 5. Veri Kaydetme Sorunlari

**"No data to save" hatasi:**

Kaydetmeden once monitoring sekmesinde veri toplamaya baslamis olmaniz gerekir. Once monitoring'i baslatin, veri toplandiktan sonra kaydetme islemini yapin.

**Excel kaydetme hatasi:**

`openpyxl` paketinin yuklu oldugundan emin olun:

```bash
pip install openpyxl
```

Excel yerine CSV formatinda kaydetmeyi tercih ederseniz `openpyxl` paketine ihtiyac duyulmaz.

**Dosya izin hatasi:**

`logs/` klasorunun yazilabilir oldugundan emin olun. Bu klasor normalde otomatik olusturulur, ancak sorun yasarsaniz elle olusturun:

```bash
mkdir -p logs
```

---

## 6. Windows ve Linux Farkliliklari

| Ozellik | Linux | Windows |
|---------|-------|---------|
| USB / GPIB backend | pyvisa-py (NI-VISA gerekmez) | NI-VISA driver gerekli |
| Serial port ismi | `/dev/ttyUSB0`, `dialout` grubu gerekli | `COM3`, Device Manager'dan kontrol |
| Dosya yolu ayirici | `/` | `\` |
| Python komutu | `python3` veya `python` | `python` |
| Terminal karakter seti | UTF-8 | cp1252 (ozel karakter sorunlari olabilir) |

**Windows icin ek notlar:**

- NI-VISA driver yuklendikten sonra bilgisayari yeniden baslatin.
- Device Manager'da COM port numarasini "Ports (COM & LPT)" bolumunden kontrol edin.
- Bazi USB-Serial donusturuculer icin ek driver gerekebilir (FTDI, CH340 vb.).

**Linux icin ek notlar:**

- `dialout` grubuna eklendikten sonra oturumu kapatip tekrar acmayi unutmayin.
- USB cihaz izinleri icin udev kurali gerekebilir.
- `libusb` yuklu degilse USB cihazlar gorunmeyebilir.

---

## 7. Sik Sorulan Sorular

**S: Monitoring sekmesi "NULL" degerleri gosteriyor.**

C: Cihaz test modunda (BUSY durumunda) iken olcum degerleri okunamaz ve NULL olarak gosterilir. Test tamamlandiginda degerler tekrar gorunur hale gelir. Eger test bittikten sonra da NULL gorunuyorsa baglantinizi kontrol edin.

**S: "Power limit exceeded" hatasi aliyorum.**

C: Ayarladiginiz gerilim ve akim degerlerinin carpimi cihazin maksimum guc sinirini asiyor. Gerilim veya akim degerini dusurerek guc sinirinin altinda kalin. Ornegin Sorensen SGX400-12D icin maksimum guc 400V x 12A = 4800W'tir, ancak belirli gerilim-akim kombinasyonlarinda daha dusuk limitler gecerli olabilir.

**S: "Mode switch failed" hatasi aliyorum.**

C: Cihazi resetleyin ve tekrar baglanin:

1. GUI'de baglantinizi kesin.
2. Cihaza manuel olarak `*RST` komutu gonderin veya cihazi kapatip acin.
3. GUI'den tekrar baglanti kurun.

**S: Profil dosyasi yuklenmiyor.**

C: Asagidakileri kontrol edin:

- `pandas` paketi yuklu mu? (`pip install pandas`)
- Excel dosyasi kullaniyorsaniz `openpyxl` yuklu mu? (`pip install openpyxl`)
- Dosya formatinin dogru oldugunu dogrulayin (CSV icin virgul ayirici, dogru sutun basliklari).
- Ornek profil dosyasini referans olarak kullanin: `gui/examples/example_profile.csv`

**S: GUI aciliyor ama cihaz listede gorunmuyor.**

C: Baglanti sekmesinde dogru arayuz tipini (VISA, Serial, Ethernet) sectiginizden emin olun. VISA icin cihazlarin listelenip listelenmedigini terminal uzerinden kontrol edin:

```bash
python -c "import pyvisa; rm = pyvisa.ResourceManager(); print(rm.list_resources())"
```

---

## Hata Bildirimi

Bu belgede yer almayan bir sorunla karsilastiginizda asagidaki bilgileri hazirlayin:

- Isletim sistemi ve Python surumu (`python --version`)
- Hata mesajinin tam metni
- Hangi cihazla ve hangi baglanti tipiyle calistiginiz
- Sorunu olusturmak icin yaptiginiz adimlar

Bu bilgiler sorunun teshis edilmesini kolaylastirir.
