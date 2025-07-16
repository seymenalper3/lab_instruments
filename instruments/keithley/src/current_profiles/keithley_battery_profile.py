#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keithley 2281S Battery Current Profile Application using LIST Mode

Bu script CSV dosyasından okunan akım profilini Keithley 2281S'in LIST modunu
kullanarak bataryaya uygular. Pozitif akımlar deşarj, negatif akımlar şarj işlemidir.
"""

import pyvisa
import pandas as pd
import time
import csv
import logging
import warnings
from datetime import datetime
from pathlib import Path

# PyVISA uyarılarını bastır
warnings.filterwarnings("ignore")

# Konfigürasyon
RESOURCE_ADDR = 'USB0::1510::8833::4587429::0::INSTR'
PROFILE_CSV = 'current_profile_for_sourcing.csv'
VOLTAGE_PROTECTION = 4.2  # V - Maksimum batarya voltajı
VOLTAGE_NOMINAL = 3.7     # V - Nominal batarya voltajı
CURRENT_PROTECTION = 1.5  # A - Maksimum akım limiti

# Çıktı dizinleri
LOG_DIR = Path('logs')
DATA_DIR = Path('data')
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


class BatteryProfileTester:
    """LIST modunu kullanarak batarya akım profili test sistemi"""
    
    def __init__(self, resource_addr, csv_file):
        self.resource_addr = resource_addr
        self.csv_file = csv_file
        self.test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.inst = None
        self.rm = None
        
        # Loglama ayarları
        self._setup_logging()
        
        # Çıktı dosyası
        self.output_file = DATA_DIR / f'battery_test_{self.test_id}.csv'
        
    def _setup_logging(self):
        """Loglama yapılandırması"""
        log_file = LOG_DIR / f"battery_test_{self.test_id}.log"
        
        # Logger yapılandırması
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Mevcut handler'ları temizle
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
    def connect(self):
        """Cihaza bağlan"""
        try:
            self.logger.info("Keithley 2281S'e bağlanılıyor...")
            self.rm = pyvisa.ResourceManager('@py')
            self.inst = self.rm.open_resource(self.resource_addr)
            self.inst.read_termination = '\n'
            self.inst.write_termination = '\n'
            self.inst.timeout = 60000  # 60 saniye timeout
            
            # Clear any errors
            self.inst.write('*CLS')
            time.sleep(0.5)
            
            # Cihazı tanımla
            idn = self.inst.query('*IDN?').strip()
            self.logger.info(f"Bağlandı: {idn}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Bağlantı hatası: {e}")
            return False
            
    def _safe_query(self, command, description=""):
        """Güvenli sorgu fonksiyonu"""
        try:
            result = self.inst.query(command).strip()
            if description:
                self.logger.debug(f"{description}: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Sorgu hatası [{command}]: {e}")
            return None
            
    def load_profile(self):
        """CSV dosyasından akım profilini yükle"""
        try:
            df = pd.read_csv(self.csv_file)
            
            if 'time_s' not in df.columns or 'current_a' not in df.columns:
                raise ValueError("CSV dosyasında 'time_s' ve 'current_a' sütunları bulunmalı")
            
            self.logger.info(f"Profil yüklendi: {len(df)} nokta")
            
            # İşaret dönüşümü: Kullanıcı mantığı -> Cihaz mantığı
            # Pozitif = Deşarj (cihaz için negatif)
            # Negatif = Şarj (cihaz için pozitif)
            df['device_current'] = -df['current_a']
            
            # Akım değerleri özeti
            self.logger.info(f"Orijinal akım aralığı: {df['current_a'].min():.3f} A ile {df['current_a'].max():.3f} A")
            self.logger.info(f"Cihaz akım aralığı: {df['device_current'].min():.3f} A ile {df['device_current'].max():.3f} A")
            
            # Sabit dwell süresi kontrolü (1 saniye)
            time_diffs = df['time_s'].diff().dropna()
            if all(abs(d - 1.0) < 0.001 for d in time_diffs):
                dwell_time = 1.0
                self.logger.info("Sabit dwell süresi: 1 saniye")
            else:
                self.logger.warning("Değişken dwell süreleri tespit edildi!")
                dwell_time = 1.0  # Varsayılan olarak 1 saniye kullan
                
            return df, dwell_time
            
        except Exception as e:
            self.logger.error(f"Profil yükleme hatası: {e}")
            return None, None
            
    def measure_initial_voltage(self):
        """Başlangıç batarya voltajını ölç"""
        try:
            self.logger.info("Başlangıç voltajı ölçülüyor...")
            
            # Çıkışın kapalı olduğundan emin ol
            self.inst.write(':OUTP OFF')
            time.sleep(1)
            
            # Voltajı ölç - daha uzun timeout ile
            self.inst.timeout = 10000  # 10 saniye
            voltage_str = self._safe_query(':MEAS:VOLT?', "Voltaj ölçümü")
            
            if voltage_str:
                voltage = float(voltage_str)
                self.logger.info(f"Başlangıç batarya voltajı: {voltage:.3f} V")
                
                if voltage < 2.0:
                    self.logger.warning("DİKKAT: Voltaj çok düşük! Batarya bağlı olmayabilir.")
                    return None
                    
                return voltage
            else:
                self.logger.error("Voltaj okunamadı")
                return None
                
        except Exception as e:
            self.logger.error(f"Voltaj ölçüm hatası: {e}")
            return None
            
    def setup_instrument(self, num_points):
        """Cihazı LIST modu için yapılandır"""
        try:
            self.logger.info("Cihaz yapılandırılıyor...")
            
            # Reset ve temizleme
            self.inst.write('*RST')
            time.sleep(3)  # Reset için daha uzun bekleme
            self.inst.write('*CLS')
            
            # LIST moduna geç - direkt olarak
            self.inst.write(':SOUR:CURR:MODE LIST')
            time.sleep(0.5)
            self.logger.info("Akım modu: LIST")
            
            # Modu kontrol et
            mode = self._safe_query(':SOUR:CURR:MODE?', "Akım modu kontrolü")
            
            # Voltaj ve akım koruma limitlerini ayarla
            self.inst.write(f':SOUR:VOLT {VOLTAGE_NOMINAL}')
            self.inst.write(f':SOUR:VOLT:PROT {VOLTAGE_PROTECTION}')
            self.inst.write(f':CURR:PROT {CURRENT_PROTECTION}')
            self.logger.info(f"Koruma limitleri: V<={VOLTAGE_PROTECTION}V, I<={CURRENT_PROTECTION}A")
            
            # TRACE belleğini yapılandır
            self.inst.write(':TRAC:CLE')  # Belleği temizle
            time.sleep(0.5)
            self.inst.write(f':TRAC:POIN {num_points}')  # Nokta sayısı
            time.sleep(0.5)
            self.inst.write(':TRAC:FEED SENS')  # Veri kaynağı
            self.inst.write(':TRAC:FEED:CONT NEXT')  # Tetikleme modu
            self.logger.info(f"TRACE belleği {num_points} nokta için yapılandırıldı")
            
            # TRACE ayarlarını kontrol et
            trace_points = self._safe_query(':TRAC:POIN?', "TRACE nokta sayısı")
            
            # Sistem hatalarını kontrol et
            error = self._safe_query(':SYST:ERR?', "Sistem hatası")
            if error and not error.startswith('+0,'):
                self.logger.warning(f"Sistem hatası: {error}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Cihaz yapılandırma hatası: {e}")
            return False
            
    def apply_profile(self, df, dwell_time):
        """LIST modunu kullanarak profili uygula"""
        try:
            num_points = len(df)
            
            # Akım listesini oluştur
            current_values = df['device_current'].tolist()
            current_list = ','.join([f"{val:.6f}" for val in current_values])
            
            self.logger.info(f"{num_points} akım değeri yükleniyor...")
            
            # LIST parametrelerini ayarla
            self.inst.write(f':SOUR:LIST:CURR {current_list}')
            time.sleep(0.5)
            
            # Listeyi doğrula
            list_check = self._safe_query(':SOUR:LIST:CURR?', "Akım listesi doğrulama")
            if list_check:
                loaded_values = list_check.split(',')
                self.logger.info(f"Yüklenen değer sayısı: {len(loaded_values)}")
            
            # Dwell süresini ayarla
            self.inst.write(f':SOUR:LIST:DWEL {dwell_time}')
            time.sleep(0.5)
            
            # Liste tekrar sayısı
            self.inst.write(':SOUR:LIST:COUN 1')  # Bir kez çalıştır
            
            # Tetikleme ayarları
            self.inst.write(':TRIG:SOUR IMM')  # Anında tetikleme
            self.inst.write(f':TRIG:COUN {num_points}')  # Tetikleme sayısı
            
            # Sistem hatalarını kontrol et
            error = self._safe_query(':SYST:ERR?', "Sistem hatası")
            if error and not error.startswith('+0,'):
                self.logger.warning(f"Setup hatası: {error}")
            
            # Testi başlat
            self.logger.info("Test başlatılıyor...")
            self.inst.write(':OUTP ON')
            time.sleep(1)
            self.inst.write(':INIT')
            
            # İlerlemeyi takip et
            self.logger.info("Profil uygulanıyor...")
            start_time = time.time()
            last_points = 0
            error_count = 0
            
            while True:
                try:
                    # Tamamlanan nokta sayısını kontrol et
                    points_str = self._safe_query(':TRAC:POIN:ACTU?')
                    
                    if points_str:
                        points_done = int(points_str)
                        error_count = 0  # Başarılı okuma, hata sayacını sıfırla
                        
                        if points_done != last_points:
                            elapsed = time.time() - start_time
                            progress = (points_done / num_points) * 100
                            self.logger.info(f"İlerleme: {points_done}/{num_points} "
                                           f"({progress:.1f}%) - Geçen süre: {elapsed:.1f}s")
                            last_points = points_done
                        
                        if points_done >= num_points:
                            self.logger.info("Profil uygulaması tamamlandı!")
                            break
                    else:
                        error_count += 1
                        if error_count > 5:
                            self.logger.error("Çok fazla okuma hatası, test durduruluyor")
                            break
                    
                    time.sleep(2)  # 2 saniye bekle
                    
                except KeyboardInterrupt:
                    self.logger.warning("Test kullanıcı tarafından durduruldu")
                    break
                except Exception as e:
                    self.logger.error(f"İlerleme takip hatası: {e}")
                    error_count += 1
                    if error_count > 5:
                        break
                    
            # Biraz bekle
            time.sleep(2)
            
            # Çıkışı kapat
            self.inst.write(':OUTP OFF')
            
            # Test süresi
            total_time = time.time() - start_time
            self.logger.info(f"Toplam test süresi: {total_time:.1f} saniye")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Profil uygulama hatası: {e}")
            self.inst.write(':OUTP OFF')
            return False
            
    def save_results(self, df):
        """TRACE belleğindeki verileri kaydet"""
        try:
            self.logger.info("Test sonuçları kaydediliyor...")
            
            # Gerçek nokta sayısını al
            actual_str = self._safe_query(':TRAC:POIN:ACTU?')
            if not actual_str:
                self.logger.warning("TRACE nokta sayısı okunamadı")
                return False
                
            actual_points = int(actual_str)
            if actual_points == 0:
                self.logger.warning("TRACE belleğinde veri bulunamadı")
                return False
                
            self.logger.info(f"TRACE belleğinde {actual_points} nokta bulundu")
            
            # Veriyi çek (Voltaj, Akım, Zaman)
            self.logger.info("Veriler çekiliyor...")
            data_str = self._safe_query(f':TRAC:DATA? 1, {actual_points}, "VOLT", "CURR", "REL"')
            
            if not data_str:
                self.logger.error("TRACE verileri okunamadı")
                return False
                
            values = data_str.strip().split(',')
            self.logger.info(f"Toplam {len(values)} değer okundu")
            
            # CSV dosyasına kaydet
            with open(self.output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['time_s', 'set_current_a', 'measured_voltage_v', 
                               'measured_current_a', 'power_w'])
                
                # Veri 3'lü gruplar halinde: volt, curr, time
                saved_count = 0
                for i in range(0, len(values), 3):
                    try:
                        if i+2 < len(values):
                            voltage = float(values[i])
                            current = float(values[i+1])  # Cihaz akımı
                            rel_time = float(values[i+2])
                            
                            # Kullanıcı mantığına geri dönüştür
                            user_current = -current  # İşareti tersine çevir
                            
                            # Güç hesapla
                            power = abs(voltage * user_current)
                            
                            # İlgili set değerini bul
                            idx = min(int(rel_time / dwell_time), len(df) - 1)
                            set_current = df.iloc[idx]['current_a']
                            
                            writer.writerow([f"{rel_time:.1f}", f"{set_current:.3f}", 
                                           f"{voltage:.3f}", f"{user_current:.3f}", 
                                           f"{power:.3f}"])
                            saved_count += 1
                    except Exception as e:
                        self.logger.debug(f"Satır işleme hatası: {e}")
                        continue
                        
            self.logger.info(f"{saved_count} satır kaydedildi: {self.output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Veri kaydetme hatası: {e}")
            return False
            
    def run_test(self):
        """Komple test döngüsü"""
        try:
            # Profili yükle
            df, dwell_time = self.load_profile()
            if df is None:
                return False
                
            # Başlangıç voltajını ölç
            initial_v = self.measure_initial_voltage()
            if initial_v is None:
                response = input("\nBaşlangıç voltajı okunamadı. Yine de devam etmek istiyor musunuz? (e/h): ")
                if response.lower() != 'e':
                    return False
                    
            # Cihazı yapılandır
            if not self.setup_instrument(len(df)):
                return False
                
            # Profili uygula
            if not self.apply_profile(df, dwell_time):
                return False
                
            # Sonuçları kaydet
            if not self.save_results(df):
                self.logger.warning("Sonuçlar kaydedilemedi ama test tamamlandı")
                
            self.logger.info("Test başarıyla tamamlandı!")
            return True
            
        except Exception as e:
            self.logger.error(f"Test hatası: {e}")
            return False
            
    def disconnect(self):
        """Cihaz bağlantısını kapat"""
        if self.inst:
            try:
                self.inst.write(':OUTP OFF')
                self.inst.write(':ABOR')
                self.inst.write('SYST:LOC')
                self.inst.close()
            except:
                pass
                
        if self.rm:
            self.rm.close()
            
        self.logger.info("Bağlantı kapatıldı")


def main():
    """Ana fonksiyon"""
    print("Keithley 2281S Battery Current Profile Test")
    print("=" * 50)
    
    tester = BatteryProfileTester(RESOURCE_ADDR, PROFILE_CSV)
    
    try:
        # Bağlan
        if not tester.connect():
            print("Cihaza bağlanılamadı!")
            return
            
        # Kullanıcı onayı
        print("\nTest Parametreleri:")
        print(f"- CSV Dosyası: {PROFILE_CSV}")
        print(f"- Voltaj Limiti: {VOLTAGE_PROTECTION} V")
        print(f"- Akım Limiti: {CURRENT_PROTECTION} A")
        print("\nPozitif akım = Deşarj, Negatif akım = Şarj")
        
        input("\nBataryayı bağlayın ve Enter'a basın...")
        
        # Testi çalıştır
        if tester.run_test():
            print("\nTest başarıyla tamamlandı!")
            print(f"Sonuçlar: {tester.output_file}")
        else:
            print("\nTest başarısız!")
            
    except KeyboardInterrupt:
        print("\nTest iptal edildi")
        
    finally:
        tester.disconnect()


if __name__ == "__main__":
    main()
