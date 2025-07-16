#!/usr/bin/env python3
"""
Keithley 2281S – 4 × (5 dk @ 0.4 A darbe → 5 dk bekleme) dinamik deşarj testi.

• Battery-Test >> DIScharge modunda çalışır.
• Her 1 s'de :MEAS:VOLT? ve :MEAS:CURR? sorgulanır.
• Sonuçlar terminalde akarken listeye eklenir ve test bitince CSV'ye yazılır.
"""
import time, csv, pyvisa
from pyvisa.errors import VisaIOError

ID          = 'USB0::1510::8833::4587429::0::INSTR'
CSV_NAME    = 'dynamic_pulse_test.csv'
V_STOP      = 3.0      # deşarj alt gerilimi
I_PULSE     = 0.4      # darbe akımı (A)
PULSE_SEC   = 1*60
REST_SEC    = 1*60
SAMPLE_INT  = 1        # loglama aralığı
TIMEOUT_MS  = 5000

def setup(inst):
    inst.write('*CLS'); inst.write('SYST:REM')
    # Hız optimizasyonu
    inst.write('SYST:AZER OFF')                    # auto-zero kapat
    inst.write(':SENS:CURR:NPLC 0.01')             # 0.01 PLC
    inst.write(':SENS:VOLT:NPLC 0.01')
    inst.timeout = TIMEOUT_MS

    # Battery-Test deşarj parametreleri
    inst.write(':BATT:TEST:MODE DIS')
    inst.write(f':BATT:TEST:VOLT {V_STOP}')
    inst.write(f':BATT:TEST:CURR:END {I_PULSE}')

def meas(inst):
    """Tek örnek (V, A) döndürür; timeout'u üst katman yakalar."""
    v  = float(inst.query(':MEAS:VOLT?'))   # :contentReference[oaicite:3]{index=3}
    i  = float(inst.query(':MEAS:CURR?'))   # :contentReference[oaicite:4]{index=4}
    return v, i

def run_cycle(inst, phase, duration, log):
    t0 = time.time()
    while time.time() - t0 < duration:
        try:
            v, i = meas(inst)
            ts = time.time()
            print(f"{phase:9}  {ts:.0f} s  {v:6.3f} V  {i:6.3f} A")
            log.append((ts, phase, v, i))
        except (VisaIOError, ValueError) as e:
            print(f"[warn] ölçüm atlandı: {e}")
        time.sleep(max(0, SAMPLE_INT - (time.time() - ts)))

def main():
    rm = pyvisa.ResourceManager('@py')
    inst = rm.open_resource(ID)
    log  = []
    try:
        setup(inst)
        for n in range(1, 5):
            print(f"\n=== Cycle {n}/4 – Darbe ===")
            inst.write(':BATT:OUTP ON')            # :contentReference[oaicite:5]{index=5}
            run_cycle(inst, 'discharge', PULSE_SEC, log)

            print(f"=== Cycle {n}/4 – Dinlenme ===")
            inst.write(':BATT:OUTP OFF')
            run_cycle(inst, 'rest', REST_SEC, log)

        with open(CSV_NAME, 'w', newline='') as f:
            csv.writer(f).writerows(
                [('Epoch s', 'Phase', 'Volt (V)', 'Curr (A)')] + log)
        print(f"\nVeriler '{CSV_NAME}' dosyasına kaydedildi.")
    finally:
        try: inst.write(':BATT:OUTP OFF')
        except: pass
        inst.write('SYST:LOC'); inst.close(); rm.close()

if __name__ == '__main__':
    main()
