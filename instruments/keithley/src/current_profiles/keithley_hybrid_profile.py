#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keithley 2281S Hybrid Current Profile Application
Deşarj: Sabit 1A (cihaz limiti), Şarj: Programlanabilir akım
"""

import pyvisa
import pandas as pd
import time
import csv
import re
from pathlib import Path
from datetime import datetime
import warnings

# --- Konfigürasyon ---
warnings.filterwarnings("ignore")

# Cihaz adresi (Gerekirse değiştirin)
RESOURCE_ADDR = 'USB0::1510::8833::4587429::0::INSTR'
# Ethernet bağlantısı için:
# RESOURCE_ADDR = 'TCPIP0::169.254.31.79::inst0::INSTR'

# Profil ve Çıktı Dosyaları
PROFILE_CSV = Path(__file__).parent.parent.parent / 'current_profile_for_sourcing.csv'
OUTPUT_DIR = Path(__file__).parent.parent.parent / 'results'
OUTPUT_DIR.mkdir(exist_ok=True)

# Güvenlik ve Çalışma Parametreleri
VOLTAGE_LIMIT = 4.2       # V (Maksimum güvenlik ve şarj voltajı)
VOLTAGE_SINK = 0.0        # V (Deşarj/Sink modunu tetiklemek için hedef voltaj)
CURRENT_LIMIT_SINK = 1.2  # A (Sink modunda güvenlik için akım limiti)


def main():
    # --- Profil Yükle ---
    print(f"Profil yükleniyor: {PROFILE_CSV}")
    df = pd.read_csv(PROFILE_CSV)
    times = df['time_s'].to_numpy()
    currents = df['current_a'].to_numpy()
    dwells = [max(0.01, times[i+1] - times[i]) for i in range(len(times)-1)]
    dwells.append(dwells[-1] if dwells else 1.0)
    print(f"Profilde {len(df)} adım bulundu.")
    
    # --- Çıktı Dosyası Hazırla ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f'hybrid_test_results_{timestamp}.csv'
    results = []

    # --- Cihaza Bağlan ve Ayarla ---
    rm = pyvisa.ResourceManager('@py')
    inst = rm.open_resource(RESOURCE_ADDR)
    inst.read_termination = '\n'
    inst.write_termination = '\n'
    inst.timeout = 20000  # 20 saniye timeout
    
    print("Cihaz sıfırlanıyor ve ayarlanıyor...")
    inst.write('*RST')
    inst.write('*CLS')
    time.sleep(2)

    # Voltaj ve akım limitlerini ayarla
    inst.write(f':VOLT:PROT {VOLTAGE_LIMIT}')
    inst.write(':OUTP ON')
    print("Cihaz hazır. Test başlıyor...")

    start_time = time.time()
    
    try:
        # --- Profil Uygulama Döngüsü ---
        for idx, (prof_curr, dwell) in enumerate(zip(currents, dwells), 1):
            
            set_current_for_log = prof_curr
            
            # Değerlere göre Şarj, Deşarj veya Bekleme modunu seç
            if prof_curr > 0:
                # --- ŞARJ (SOURCE) MODU ---
                inst.write(':SOUR:FUNC CURR')
                inst.write(f':VOLT {VOLTAGE_LIMIT}')
                inst.write(f':CURR {prof_curr}')
                # Ekranın akımı göstermesi için I-Set tuşuna basma simülasyonu yap
                inst.write(':SYST:KEY 2') # 2, I-Set tuşunun kodudur
                print(f'Step {idx}: Şarj | Ayar: {prof_curr:.3f} A')

            elif prof_curr < 0:
                # --- DEŞARJ (SINK) MODU ---
                inst.write(':SOUR:FUNC VOLT')
                inst.write(f':VOLT {VOLTAGE_SINK}')
                inst.write(f':CURR {CURRENT_LIMIT_SINK}')
                # Ekranın akımı göstermesi için I-Set tuşuna basma simülasyonu yap
                inst.write(':SYST:KEY 2') # 2, I-Set tuşunun kodudur
                print(f'Step {idx}: Deşarj (Sink) | Hedef: ~1A')
                set_current_for_log = -1.0
                
            else: # prof_curr == 0
                # --- BEKLEME (IDLE) MODU ---
                inst.write(':SOUR:FUNC VOLT')
                inst.write(f':VOLT {3.7}')
                inst.write(':CURR 0.001')
                print(f'Step {idx}: Bekleme | Ayar: 0A')

            time.sleep(dwell)
            
            elapsed_time = time.time() - start_time
            
            # --- Ölçüm Yap (example_profile_application.py'deki çalışan mantık) ---
            try:
                meas_resp = inst.query(':MEAS:VOLT?')
                parts = meas_resp.split(',')
                
                if len(parts) >= 2:
                    # Cihaz Akım ve Voltajı birlikte döndürdü
                    i_val = re.sub(r'[AVWNR\s]', '', parts[0])
                    v_val = re.sub(r'[AVWNR\s]', '', parts[1])
                    v_meas = float(v_val)
                    i_meas = float(i_val)
                else:
                    # Sadece tek değer döndü, diğerini ayrıca sorgula
                    if 'A' in meas_resp.upper():
                        i_val = re.sub(r'[AVWNR\s]', '', meas_resp)
                        i_meas = float(i_val)
                        v_resp = inst.query(':MEAS:VOLT?')
                        v_val = re.sub(r'[AVWNR\s]', '', v_resp.split(',')[0])
                        v_meas = float(v_val)
                    else:
                        v_val = re.sub(r'[AVWNR\s]', '', meas_resp)
                        v_meas = float(v_val)
                        i_resp = inst.query(':MEAS:CURR?')
                        i_val = re.sub(r'[AVWNR\s]', '', i_resp.split(',')[0])
                        i_meas = float(i_val)

                # Ölçülen akımın işaretini operasyon moduna göre düzeltelim.
                # Cihaz sorgusu akım yönünü belirtmiyor gibi görünüyor, sadece büyüklüğü veriyor.
                # Bizim kuralımız: Şarj pozitif (+), Deşarj negatif (-).
                measured_current_magnitude = abs(i_meas)
                if prof_curr > 0:  # Şarj
                    log_i_meas = measured_current_magnitude
                elif prof_curr < 0: # Deşarj
                    log_i_meas = -measured_current_magnitude
                else: # Bekleme
                    log_i_meas = 0.0

                print(f'   -> Ölçülen: {v_meas:.3f} V, {log_i_meas:.3f} A')
                
                results.append({
                    'step': idx, 'elapsed_time_s': elapsed_time,
                    'profile_current_a': prof_curr, 'set_current_a': set_current_for_log,
                    'measured_voltage_v': v_meas, 'measured_current_a': log_i_meas,
                    'power_w': v_meas * log_i_meas, 'status': 'OK'
                })
                
            except Exception as e:
                print(f'   -> Step {idx}: ÖLÇÜM HATASI: {e}')
                results.append({
                    'step': idx, 'elapsed_time_s': elapsed_time,
                    'profile_current_a': prof_curr, 'set_current_a': set_current_for_log,
                    'measured_voltage_v': 'ERROR', 'measured_current_a': 'ERROR',
                    'power_w': 'ERROR', 'status': f'ERROR: {e}'
                })
    
    finally:
        # --- Testi Bitir ve Kaydet ---
        if inst:
            inst.write(':OUTP OFF')
            inst.close()
        if rm:
            rm.close()
        
        print("\nTest sonlandırıldı.")

        if results:
            try:
                with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['step', 'elapsed_time_s', 'profile_current_a', 'set_current_a', 
                                 'measured_voltage_v', 'measured_current_a', 'power_w', 'status']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(results)
                
                print(f'\n✅ Sonuçlar CSV dosyasına kaydedildi: {output_file}')
            except Exception as e:
                print(f'❌ CSV kaydetme hatası: {e}')
        
        print('İşlem tamamlandı.')

if __name__ == '__main__':
    main() 