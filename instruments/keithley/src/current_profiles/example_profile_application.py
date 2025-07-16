import pyvisa
import pandas as pd
import time
import csv
from pathlib import Path
from datetime import datetime

# Konfigürasyon
# USB bağlantısı için örnek (yorum satırında):
RESOURCE_ADDR = 'USB0::1510::8833::4587429::0::INSTR'
# Ethernet bağlantısı için:
# RESOURCE_ADDR = 'TCPIP0::169.254.31.79::inst0::INSTR'  # Ethernet VISA resource string
PROFILE_CSV = Path(__file__).parent.parent.parent / 'current_profile_for_sourcing.csv'
VOLTAGE_LIMIT = 4.2  # V
VOLTAGE_SAFE = 3.7   # V (nominal, güvenli voltaj)


def main():
    # Profil yükle
    df = pd.read_csv(PROFILE_CSV)
    times = df['time_s'].to_numpy()
    currents = df['current_a'].to_numpy()
    dwells = [max(0.01, times[i+1] - times[i]) for i in range(len(times)-1)]
    dwells.append(dwells[-1] if dwells else 1.0)
    
    # CSV çıktı dosyası hazırla
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(__file__).parent.parent.parent / f'profile_test_results_{timestamp}.csv'
    results = []

    # Cihaza bağlan
    rm = pyvisa.ResourceManager('@py')
    inst = rm.open_resource(RESOURCE_ADDR)
    inst.read_termination = '\n'
    inst.write_termination = '\n'
    inst.timeout = 10000  # 10 saniye timeout
    inst.write('*RST')
    inst.write('*CLS')
    time.sleep(2)

    def print_error():
        try:
            err = inst.query('SYST:ERR?').strip()
            print(f'Cihaz hata durumu: {err}')
        except Exception as e:
            print(f'Hata sorgulanamadı: {e}')

    # Voltaj ve akım limitlerini ayarla
    inst.write(f':VOLT {VOLTAGE_SAFE}')
    inst.write(f':VOLT:PROT {VOLTAGE_LIMIT}')
    print_error()
    inst.write(':OUTP ON')
    print_error()

    start_time = time.time()
    
    try:
        for idx, (curr, dwell) in enumerate(zip(currents, dwells), 1):
            # Negatif akım kontrolü - Keithley 2281S sadece pozitif akım uygulayabilir
            if curr < 0:
                print(f'Step {idx}: UYARI - Negatif akım ({curr} A) uygulanamaz, 0A ayarlanıyor')
                curr = 0
            
            inst.write(f':CURR {curr}')
            time.sleep(dwell)
            
            # Geçen süreyi hesapla
            elapsed_time = time.time() - start_time
            
            try:
                # Tek sorguda hem akım hem voltaj al
                meas_resp = inst.query(':MEAS:VOLT?')
                print(f'Raw response: {meas_resp}')  # Debug için
                
                # Virgülle ayrılmış değerleri parse et
                parts = meas_resp.split(',')
                if len(parts) >= 2:
                    import re
                    # DÜZELTİLDİ: İlk değer akım, ikinci değer voltaj (cihaz böyle döndürüyor)
                    i_val = re.sub(r'[AVW]', '', parts[0].strip())  # İlk değer akım
                    v_val = re.sub(r'[AVW]', '', parts[1].strip())  # İkinci değer voltaj
                    v_meas = float(v_val)
                    i_meas = float(i_val)
                else:
                    # Tek değer varsa ayrı ayrı sorgula
                    # İlk sorgu akım içinse
                    if 'A' in meas_resp:
                        i_val = re.sub(r'[AVW]', '', meas_resp.strip())
                        i_meas = float(i_val)
                        v_resp = inst.query(':MEAS:VOLT?')
                        v_val = re.sub(r'[AVW]', '', v_resp.split(',')[0].strip())
                        v_meas = float(v_val)
                    else:
                        # İlk sorgu voltaj içinse
                        v_val = re.sub(r'[AVW]', '', meas_resp.strip())
                        v_meas = float(v_val)
                        i_resp = inst.query(':MEAS:CURR?')
                        i_val = re.sub(r'[AVW]', '', i_resp.split(',')[0].strip())
                        i_meas = float(i_val)
                
                # DÜZELTİLDİ: Doğru birimlerle göster
                print(f'Step {idx}: Set {curr} A, {dwell} s | Measured: {v_meas:.3f} V, {i_meas:.3f} A')
                
                # Sonuçları kaydet
                results.append({
                    'step': idx,
                    'elapsed_time_s': elapsed_time,
                    'set_current_a': curr,
                    'dwell_time_s': dwell,
                    'measured_voltage_v': v_meas,
                    'measured_current_a': i_meas,
                    'power_w': v_meas * i_meas,
                    'status': 'OK'
                })
                
            except Exception as e:
                print(f'Step {idx}: Ölçüm hatası: {e}')
                print_error()
                
                # Hata durumunu kaydet
                results.append({
                    'step': idx,
                    'elapsed_time_s': elapsed_time,
                    'set_current_a': curr,
                    'dwell_time_s': dwell,
                    'measured_voltage_v': 'ERROR',
                    'measured_current_a': 'ERROR',
                    'power_w': 'ERROR',
                    'status': f'ERROR: {e}'
                })
    finally:
        inst.write(':OUTP OFF')
        print_error()
        inst.close()
        rm.close()
        
        # CSV dosyasına sonuçları yaz
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['step', 'elapsed_time_s', 'set_current_a', 'dwell_time_s', 
                             'measured_voltage_v', 'measured_current_a', 'power_w', 'status']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in results:
                    writer.writerow(result)
            
            print(f'\n✅ Sonuçlar CSV dosyasına kaydedildi: {output_file}')
            print(f'📊 Toplam {len(results)} adım işlendi')
            
            # Özet istatistikler
            success_count = sum(1 for r in results if r['status'] == 'OK')
            error_count = len(results) - success_count
            print(f'✅ Başarılı: {success_count} adım')
            print(f'❌ Hatalı: {error_count} adım')
            
        except Exception as e:
            print(f'❌ CSV kaydetme hatası: {e}')
        
        print('Profil uygulama tamamlandı.')

if __name__ == '__main__':
    main() 