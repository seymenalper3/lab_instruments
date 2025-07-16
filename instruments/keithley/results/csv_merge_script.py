#!/usr/bin/env python3
"""
CSV Merge Script - Pulse ve EVOC verilerini birleştir
demo_pulse_evoc_60s scripti tarafından üretilen iki CSV dosyasını birleştirir:
- pulse_bt_*.csv (darbe fazı verileri)
- rest_evoc_*.csv (dinlenme fazı EVOC verileri)
"""

import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

def merge_pulse_evoc_data(pulse_file, evoc_file, output_file=None):
    """
    Pulse ve EVOC CSV dosyalarını zaman bazlı birleştir
    
    Args:
        pulse_file: pulse_bt_*.csv dosya yolu
        evoc_file: rest_evoc_*.csv dosya yolu
        output_file: çıktı dosyası (None ise otomatik isim)
    """
    
    try:
        # CSV dosyalarını oku
        print(f"Pulse dosyası okunuyor: {pulse_file}")
        df_pulse = pd.read_csv(pulse_file)
        
        print(f"EVOC dosyası okunuyor: {evoc_file}")
        df_evoc = pd.read_csv(evoc_file)
        
        # Kolon isimlerini kontrol et
        print(f"Pulse kolonları: {list(df_pulse.columns)}")
        print(f"EVOC kolonları: {list(df_evoc.columns)}")
        
        # Pulse verisini işle
        df_pulse['phase'] = 'discharge'
        df_pulse['voc_v'] = np.nan
        df_pulse['esr_ohm'] = np.nan
        df_pulse = df_pulse[['t_rel_s', 'volt_v', 'curr_a', 'phase', 'voc_v', 'esr_ohm']]
        
        # EVOC verisini işle
        df_evoc['phase'] = 'rest'
        df_evoc['volt_v'] = df_evoc['voc_v']  # EVOC sırasında terminal gerilimi = VOC
        df_evoc['curr_a'] = 0.0001  # Rest akımı (scriptteki I_REST değeri)
        df_evoc = df_evoc[['t_rel_s', 'volt_v', 'curr_a', 'phase', 'voc_v', 'esr_ohm']]
        
        # Birleştir ve zaman sırasına göre sırala
        df_merged = pd.concat([df_pulse, df_evoc], ignore_index=True)
        df_merged = df_merged.sort_values('t_rel_s').reset_index(drop=True)
        
        # Çıktı dosyası ismi
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'merged_pulse_evoc_{timestamp}.csv'
        
        # Kaydet
        df_merged.to_csv(output_file, index=False, float_format='%.6f')
        
        # Özet bilgiler
        print(f"\n✓ Birleştirme tamamlandı!")
        print(f"✓ Çıktı dosyası: {output_file}")
        print(f"✓ Toplam kayıt sayısı: {len(df_merged)}")
        print(f"✓ Darbe kayıtları: {len(df_merged[df_merged['phase'] == 'discharge'])}")
        print(f"✓ Dinlenme kayıtları: {len(df_merged[df_merged['phase'] == 'rest'])}")
        print(f"✓ Zaman aralığı: {df_merged['t_rel_s'].min():.1f} - {df_merged['t_rel_s'].max():.1f} s")
        
        # İlk birkaç satırı göster
        print(f"\nİlk 5 satır:")
        print(df_merged.head().to_string(index=False))
        
        return df_merged
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return None

def auto_find_files(directory='.'):
    """
    Dizinde pulse_bt_* ve rest_evoc_* dosyalarını otomatik bulur
    """
    pulse_files = []
    evoc_files = []
    
    for file in os.listdir(directory):
        if file.startswith('pulse_bt_') and file.endswith('.csv'):
            pulse_files.append(file)
        elif file.startswith('rest_evoc_') and file.endswith('.csv'):
            evoc_files.append(file)
    
    return pulse_files, evoc_files

def main():
    """Ana fonksiyon"""
    
    # Komut satırı argümanları kontrolü
    if len(sys.argv) == 3:
        pulse_file = sys.argv[1]
        evoc_file = sys.argv[2]
        output_file = None
    elif len(sys.argv) == 4:
        pulse_file = sys.argv[1]
        evoc_file = sys.argv[2] 
        output_file = sys.argv[3]
    else:
        # Otomatik dosya bulma
        print("Otomatik dosya arama yapılıyor...")
        pulse_files, evoc_files = auto_find_files()
        
        if not pulse_files or not evoc_files:
            print("❌ Uygun CSV dosyaları bulunamadı!")
            print("Kullanım:")
            print("  python merge_csv.py pulse_bt_file.csv rest_evoc_file.csv [output_file.csv]")
            sys.exit(1)
        
        # En son dosyaları seç (timestamp'e göre)
        pulse_file = sorted(pulse_files)[-1]
        evoc_file = sorted(evoc_files)[-1]
        output_file = None
        
        print(f"Seçilen dosyalar:")
        print(f"  Pulse: {pulse_file}")
        print(f"  EVOC:  {evoc_file}")
    
    # Dosya varlığını kontrol et
    if not os.path.exists(pulse_file):
        print(f"❌ Pulse dosyası bulunamadı: {pulse_file}")
        sys.exit(1)
    
    if not os.path.exists(evoc_file):
        print(f"❌ EVOC dosyası bulunamadı: {evoc_file}")
        sys.exit(1)
    
    # Birleştirme işlemini yap
    result = merge_pulse_evoc_data(pulse_file, evoc_file, output_file)
    
    if result is not None:
        print("\n🎉 İşlem başarıyla tamamlandı!")
    else:
        print("\n❌ İşlem başarısız!")
        sys.exit(1)

if __name__ == '__main__':
    main()
