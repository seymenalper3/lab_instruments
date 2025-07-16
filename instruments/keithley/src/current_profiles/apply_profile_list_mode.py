#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keithley 2281S ile Donanım Tabanlı Akım Profili Uygulama (LIST Modu)

Bu betik, bir CSV dosyasından okunan zaman-akım profilini Keithley 2281S
cihazının dahili "LIST" (liste tarama) özelliğini kullanarak uygular. Bu yöntem,
Python döngülerine göre çok daha hassas zamanlama ve verimlilik sağlar.
Tüm profil cihaza yüklenir ve donanım tarafından adımlar tetiklenir.
Test sonuçları, cihazın dahili TRACE belleğinden toplu olarak okunur.
"""

import pyvisa
import pandas as pd
import time
import csv
import logging
from datetime import datetime
from pathlib import Path

# --- Betiğin kendi konumuna göre Proje Kök Dizinini bul ---
# Bu, betiğin herhangi bir yerden çalıştırılabilmesini sağlar.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# --- 1. KONFİGÜRASYON ---
# Cihazınızın pyvisa tarafından tanınan adresi.
# 'python -m pyvisa list_resources' komutu ile bulabilirsiniz.
RESOURCE_ADDR = 'USB0::1510::8833::4587429::0::INSTR'

# Cihaza uygulanacak akım profilini içeren CSV dosyasının yolu.
PROFILE_CSV_FILE = PROJECT_ROOT / 'keithley' / 'current_profile_for_sourcing.csv'

# --- 2. GÜVENLİK PARAMETRELERİ ---
# !!! DİKKAT: BU DEĞERLERİ KENDİ DEVRENİZE GÖRE DÜZENLEYİN !!!
VOLTAGE_PROTECTION_V = 4.2  # V (Cihazın çıkış voltajı bu değeri aşmayacak)
CURRENT_PROTECTION_A = 1.2  # A (Donanımsal aşırı akım koruması)

# --- 3. DEBUG VE TIMEOUT AYARLARI ---
DEBUG_MODE = True  # Detaylı debug bilgilerini göster
INSTRUMENT_TIMEOUT_MS = 60000  # 60 saniye timeout
TRACE_CHECK_INTERVAL_S = 1  # TRACE kontrolü için bekleme süresi
MAX_RETRY_COUNT = 3  # Komut tekrar deneme sayısı

# --- Çıktı Dosyaları için Dizinler ---
LOG_DIR = PROJECT_ROOT / 'keithley' / 'logs'
DATA_DIR = PROJECT_ROOT / 'keithley' / 'data'


class ListProfileApplicator:
    """
    LIST modunu kullanarak akım profilini yöneten ve uygulayan sınıf.
    """

    def __init__(self, resource_addr, profile_path):
        self.resource_addr = resource_addr
        self.profile_path = profile_path
        self.test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.inst = None
        self.rm = None

        LOG_DIR.mkdir(exist_ok=True)
        DATA_DIR.mkdir(exist_ok=True)
        self._setup_logging()

        self.output_csv_path = DATA_DIR / f'list_mode_results_{self.test_id}.csv'

    def _setup_logging(self):
        """Loglama ayarlarını yapılandırır."""
        log_file = LOG_DIR / f"list_mode_test_{self.test_id}.log"
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Dosyaya loglama
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        # Konsola loglama
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def connect(self):
        """Cihaza bağlanır."""
        try:
            self.logger.info("Cihaz aranıyor...")
            self.rm = pyvisa.ResourceManager('@py')
            self.inst = self.rm.open_resource(self.resource_addr)
            self.inst.read_termination = '\n'
            self.inst.write_termination = '\n'
            self.inst.timeout = INSTRUMENT_TIMEOUT_MS  # Liste operasyonları için daha uzun zaman aşımı

            idn = self.inst.query('*IDN?').strip()
            self.logger.info(f"Bağlandı: {idn}")
            return True
        except pyvisa.errors.VisaIOError as e:
            self.logger.error(f"Bağlantı hatası: Cihaz bulunamadı veya yanıt vermiyor. Adresi kontrol edin: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Beklenmedik bir bağlantı hatası: {e}")
            return False

    def _measure_initial_voltage(self):
        """Cihaz çıkışı kapalıyken başlangıçtaki batarya voltajını ölçer."""
        try:
            self.logger.info("Başlangıçtaki batarya voltajı ölçülüyor...")
            self.inst.write(':OUTP OFF') # Ölçümden önce çıkışın kapalı olduğundan emin ol
            time.sleep(0.5)
            
            # Voltajı ölç
            voltage_str = self.inst.query(':MEAS:VOLT?')
            voltage = float(voltage_str)
            
            self.logger.info(f"Ölçülen başlangıç voltajı: {voltage:.4f} V")
            
            # Güvenlik Kontrolü
            if voltage < 2.0:
                self.logger.warning("DİKKAT: Ölçülen voltaj çok düşük. Batarya bağlı olmayabilir veya derin deşarj olmuş olabilir.")
            
            return voltage
        except Exception as e:
            self.logger.error(f"Başlangıç voltajı ölçülürken hata oluştu: {e}")
            return None

    def _debug_query(self, command, description=""):
        """Debug amaçlı güvenli sorgu fonksiyonu."""
        try:
            result = self.inst.query(command)
            if DEBUG_MODE:
                self.logger.info(f"DEBUG - {description} | Komut: {command} | Sonuç: {result.strip()}")
            return result
        except Exception as e:
            self.logger.error(f"DEBUG - {description} | Komut: {command} | HATA: {e}")
            return None

    def _debug_write(self, command, description=""):
        """Debug amaçlı güvenli yazma fonksiyonu."""
        try:
            self.inst.write(command)
            if DEBUG_MODE:
                self.logger.info(f"DEBUG - {description} | Komut gönderildi: {command}")
            return True
        except Exception as e:
            self.logger.error(f"DEBUG - {description} | Komut: {command} | HATA: {e}")
            return False

    def _check_instrument_status(self):
        """Cihazın durumunu kontrol eder."""
        if DEBUG_MODE:
            self.logger.info("DEBUG - Cihaz durumu kontrol ediliyor...")
            # Hata durumunu kontrol et
            error_status = self._debug_query(':SYST:ERR?', "Sistem hatası kontrolü")
            # Operasyon durumunu kontrol et
            operation_status = self._debug_query(':STAT:OPER?', "Operasyon durumu")
            # Çıkış durumunu kontrol et
            output_status = self._debug_query(':OUTP?', "Çıkış durumu")
            
            return error_status, operation_status, output_status
        return None, None, None

    def _setup_instrument(self, num_points):
        """Cihazı LIST modu için ayarlar ve TRACE belleğini yapılandırır."""
        self.logger.info("Cihaz LIST modu için ayarlanıyor...")
        
        # Reset ve clear
        self._debug_write('*RST', "Sistem reset")
        time.sleep(2)  # Reset sonrası daha uzun bekleme
        self._debug_write('*CLS', "Hata temizleme")
        
        # Başlangıç durumunu kontrol et
        self._check_instrument_status()

        # Güç kaynağı (Source) moduna geç ve akım kaynağı olarak ayarla
        self._debug_write(':SOUR:FUNC CURR', "Akım kaynağı modu")
        
        # Mevcut modu kontrol et
        current_mode = self._debug_query(':SOUR:FUNC?', "Mevcut kaynak modu")
        
        # LIST modu destekleniyor mu kontrol et
        list_support = self._debug_query(':SOUR:CURR:MODE?', "Mevcut akım modu")
        
        # Akım listesi moduna geç
        self.inst.write(':SOUR:CURR:MODE LIST')
        self.logger.info("Mod: LIST (Akım Listesi)")

        # Ana voltaj seviyesini (uyumluluk/compliance) ve koruma limitlerini ayarla
        self.inst.write(f':SOUR:VOLT {VOLTAGE_PROTECTION_V}')
        self.inst.write(f':SOUR:VOLT:PROT {VOLTAGE_PROTECTION_V}')
        self.inst.write(f':CURR:PROT {CURRENT_PROTECTION_A}')
        self.logger.info(f"Güvenlik limitleri ayarlandı: Voltaj <= {VOLTAGE_PROTECTION_V}V, Akım <= {CURRENT_PROTECTION_A}A")

        # Ölçüm (Trace) belleğini yapılandır
        self.logger.info(f"TRACE belleği {num_points} nokta için hazırlanıyor...")
        self.inst.write(':TRAC:CLE')  # Belleği temizle
        time.sleep(0.5)
        self.inst.write(f':TRAC:POIN {num_points}', "TRACE bellek boyutu")
        self.inst.write(':TRAC:FEED SENS', "TRACE veri kaynağı")
        self.inst.write(':TRAC:FEED:CONT NEXT', "TRACE tetikleme modu")
        
        # TRACE ayarlarını doğrula
        trace_points = self._debug_query(':TRAC:POIN?', "TRACE nokta sayısı doğrulama")
        trace_feed = self._debug_query(':TRAC:FEED?', "TRACE veri kaynağı doğrulama")
        
        self.logger.info("Cihaz ayarları tamamlandı.")
        self._check_instrument_status()
        return True

    def load_profile(self):
        """CSV dosyasından akım profilini yükler ve analiz eder."""
        try:
            df = pd.read_csv(self.profile_path)
            if 'time_s' not in df.columns or 'current_a' not in df.columns:
                self.logger.error("Profil dosyasında 'time_s' ve 'current_a' sütunları bulunmalıdır.")
                return None, None
            
            self.logger.info(f"Profil yüklendi: {self.profile_path} ({len(df)} nokta)")
            
            # Adımlar arasındaki bekleme süresini (dwell) hesapla
            dwells = df['time_s'].diff().dropna()
            if len(dwells) > 0 and (dwells.std() < 1e-6):
                dwell_time = dwells.iloc[0]
                self.logger.info(f"Tüm adımlar için sabit bekleme süresi tespit edildi: {dwell_time} s")
            else:
                dwell_time = None # Değişken dwell süreleri kullanılacak (bu scriptte şimdilik desteklenmiyor)
                self.logger.warning("Değişken bekleme süreleri tespit edildi. Bu script yalnızca sabit süreleri destekler.")

            return df, dwell_time
        except FileNotFoundError:
            self.logger.error(f"Profil dosyası bulunamadı: {self.profile_path}")
            return None, None
        except Exception as e:
            self.logger.error(f"Profil yüklenirken hata oluştu: {e}")
            return None, None

    def _fetch_and_save_trace_data(self, num_points):
        """Test sonrası TRACE belleğindeki verileri çeker ve CSV dosyasına kaydeder."""
        self.logger.info(f"{num_points} noktalık ölçüm verisi TRACE belleğinden çekiliyor...")
        try:
            # Bellekteki gerçek nokta sayısını al
            actual_points = int(self.inst.query(':TRAC:POIN:ACTU?'))
            if actual_points == 0:
                self.logger.warning("TRACE belleğinde hiç veri bulunamadı!")
                return
            self.logger.info(f"Bellekte {actual_points} nokta bulundu.")

            # Veriyi sorgula (Voltaj, Akım ve Zaman damgası)
            data_str = self.inst.query(':TRAC:DATA? 1, {}, "VOLT", "CURR", "REL"'.format(actual_points))
            
            # Gelen veriyi işle
            values = data_str.strip().split(',')
            
            with open(self.output_csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['relative_time_s', 'measured_voltage_v', 'measured_current_a'])
                
                # Veri 3'lü gruplar halinde gelir (volt, curr, time)
                for i in range(0, len(values), 3):
                    try:
                        voltage = float(values[i])
                        current = float(values[i+1])
                        rel_time = float(values[i+2])
                        writer.writerow([f"{rel_time:.6f}", f"{voltage:.6f}", f"{current:.6f}"])
                    except (IndexError, ValueError):
                        continue # Hatalı satırı atla
            self.logger.info(f"Tüm ölçüm sonuçları başarıyla '{self.output_csv_path}' dosyasına kaydedildi.")

        except Exception as e:
            self.logger.error(f"TRACE verileri okunurken veya kaydedilirken bir hata oluştu: {e}")

    def run(self):
        """Testi başlatır, profili uygular ve sonuçları kaydeder."""
        # Testten önce başlangıçtaki açık devre voltajını ölç
        initial_voltage = self._measure_initial_voltage()
        if initial_voltage is None:
            self.logger.error("Başlangıç voltajı ölçülemediği için teste devam edilemiyor.")
            self.disconnect()
            return
            
        profile_df, dwell_time = self.load_profile()
        if profile_df is None:
            return
        
        num_points = len(profile_df)
        if not self._setup_instrument(num_points):
            self.logger.error("Cihaz ayarları başarısız. Test sonlandırılıyor.")
            return

        try:
            # KULLANICI MANTIĞI -> CİHAZ MANTIĞI ÇEVİRİMİ
            # CSV'deki pozitif akım DEŞARJ (cihaz için negatif akım),
            # CSV'deki negatif akım ŞARJ (cihaz için pozitif akım) anlamına gelir.
            # Bu nedenle cihaza göndermeden önce tüm akım değerlerinin işareti tersine çevrilir.
            self.logger.info("Kullanıcı mantığı (Pozitif=Deşarj) cihaz mantığına (Negatif=Deşarj) çevriliyor...")
            inverted_currents = profile_df['current_a'] * -1
            
            # Akım listesini oluştur ve cihaza gönder
            current_list_str = ",".join(inverted_currents.astype(str))
            if DEBUG_MODE:
                self.logger.info(f"DEBUG - Gönderilecek akım listesi: {current_list_str[:100]}...")
            
            success = self._debug_write(f':SOUR:LIST:CURR {current_list_str}', "Akım listesi yükleme")
            if not success:
                self.logger.error("Akım listesi yüklenemedi!")
                return
            
            # Liste yükleme doğrulama
            list_verify = self._debug_query(':SOUR:LIST:CURR?', "Akım listesi doğrulama")
            self.logger.info(f"{num_points} adımlık akım listesi cihaza yüklendi.")

            # Bekleme süresini ayarla
            if dwell_time is not None:
                self._debug_write(f':SOUR:LIST:DWEL {dwell_time}', "Bekleme süresi ayarı")
                dwell_verify = self._debug_query(':SOUR:LIST:DWEL?', "Bekleme süresi doğrulama")
            
            # Liste sadece bir kez çalışacak
            self._debug_write(':SOUR:LIST:COUN 1', "Liste tekrar sayısı")
            count_verify = self._debug_query(':SOUR:LIST:COUN?', "Liste tekrar sayısı doğrulama")
            
            # Tetikleme kaynağını "anında" olarak ayarla ve tetikleme sayısını belirle
            self._debug_write(':TRIG:SOUR IMM', "Tetikleme kaynağı")
            self._debug_write(f':TRIG:COUN {num_points}', "Tetikleme sayısı")
            
            # Tetikleme ayarlarını doğrula
            trig_source = self._debug_query(':TRIG:SOUR?', "Tetikleme kaynağı doğrulama")
            trig_count = self._debug_query(':TRIG:COUN?', "Tetikleme sayısı doğrulama")

            # Testi başlat
            self.logger.info("Profil uygulaması başlatılıyor. Çıkış açılıyor...")
            self._debug_write(':OUTP ON', "Çıkış açma")
            
            # Çıkış durumunu kontrol et
            output_status = self._debug_query(':OUTP?', "Çıkış durumu kontrol")
            
            self._debug_write(':INIT', "Profil başlatma")
            
            # Başlatma sonrası durum kontrol
            self._check_instrument_status()

            self.logger.info("Profil çalışıyor... Tamamlanması bekleniyor. Bu işlem uzun sürebilir.")
            
            # *OPC? komutu bu senaryoda anında döndüğü için, testin tamamlandığını
            # TRACE belleğindeki nokta sayısını kontrol ederek anlıyoruz.
            self.logger.info("İlerleme takip ediliyor...")
            retry_count = 0
            consecutive_errors = 0
            
            while True:
                try:
                    # Bellekteki güncel nokta sayısını sorgula
                    points_query = self._debug_query(':TRAC:POIN:ACTU?', "Aktüel nokta sayısı")
                    
                    if points_query is None:
                        consecutive_errors += 1
                        if consecutive_errors >= 3:
                            self.logger.error("Çok fazla ardışık hata. TRACE komutu desteklenmeyebilir.")
                            break
                        time.sleep(TRACE_CHECK_INTERVAL_S)
                        continue
                    
                    consecutive_errors = 0  # Başarılı sorguda hata sayacını sıfırla
                    points_done = int(points_query)
                    
                    if points_done >= num_points:
                        self.logger.info(f"Tüm {points_done}/{num_points} nokta başarıyla toplandı.")
                        break
                    
                    self.logger.info(f"İlerleme: {points_done}/{num_points} nokta tamamlandı...")
                    
                    # Cihaz durumunu periyodik olarak kontrol et
                    if points_done % 5 == 0:  # Her 5 noktada bir
                        self._check_instrument_status()
                    
                    time.sleep(TRACE_CHECK_INTERVAL_S)

                except pyvisa.errors.VisaIOError as e:
                    self.logger.warning(f"İlerleme kontrolü sırasında VISA hatası: {e}")
                    retry_count += 1
                    if retry_count > MAX_RETRY_COUNT:
                        self.logger.error("Çok fazla timeout hatası. İşlem sonlandırılıyor.")
                        break
                    time.sleep(TRACE_CHECK_INTERVAL_S * 2)  # Hata durumunda daha uzun bekle
                except Exception as e:
                    self.logger.error(f"İlerleme takibi sırasında beklenmedik hata: {e}")
                    break
            
            # Verilerin belleğe tam olarak yazıldığından emin olmak için kısa bir ek bekleme.
            time.sleep(1)
            
            self.logger.info("Profil uygulaması tamamlandı.")

            # Verileri çek ve kaydet
            self._fetch_and_save_trace_data(num_points)

        except KeyboardInterrupt:
            self.logger.warning("Test kullanıcı tarafından durduruldu.")
        except Exception as e:
            self.logger.error(f"Test sırasında kritik bir hata oluştu: {e}", exc_info=True)
        finally:
            self.disconnect()
    
    def disconnect(self):
        """Cihazı güvenli duruma getirir ve bağlantıyı kapatır."""
        self.logger.info("Test sonlandırılıyor. Cihaz güvenli duruma getiriliyor.")
        try:
            if self.inst:
                self.inst.write(':OUTP OFF')
                # Abort komutu olası bir takılmayı önler
                self.inst.write(':ABOR')
                self.inst.write('SYST:LOC') # Cihazı lokal kontrol moduna al
                self.inst.close()
                self.logger.info("Cihaz bağlantısı kapatıldı.")
        except Exception as e:
            self.logger.error(f"Cihaz kapatılırken hata: {e}")
        finally:
            if self.rm:
                self.rm.close()

def main():
    """Ana fonksiyon."""
    applicator = ListProfileApplicator(RESOURCE_ADDR, PROFILE_CSV_FILE)
    if applicator.connect():
        applicator.run()

if __name__ == "__main__":
    main()
