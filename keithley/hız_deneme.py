import pyvisa
import time

RESOURCE = 'USB0::1510::8833::4587429::0::INSTR'  # Kendi cihazının VISA adresini yaz
N_STEPS = 20
CURRENT_START = 0.0
CURRENT_END = 1.0

# Kaç ms arayla komut göndereceğini test etmek için
INTERVALS = [1.0, 0.5, 0.2, 0.1, 0.05]  # saniye cinsinden (1s, 0.5s, 0.2s, 0.1s, 0.05s)

rm = pyvisa.ResourceManager('@py')
inst = rm.open_resource(RESOURCE)
inst.read_termination = inst.write_termination = '\n'
inst.timeout = 5000

try:
    inst.write('*CLS')
    inst.write('SYST:REM')
    inst.write(':SOUR:FUNC CURR')
    inst.write(':SOUR:CURR:RANG:AUTO ON')
    inst.write(':SOUR:VOLT:ILIM 5.0')
    inst.write(':OUTP ON')

    for interval in INTERVALS:
        print(f"\n--- {interval:.3f} s aralık ile komut gönderiliyor ---")
        currents = [CURRENT_START + (CURRENT_END - CURRENT_START) * i / (N_STEPS - 1) for i in range(N_STEPS)]
        times = []
        for i, curr in enumerate(currents):
            t0 = time.time()
            inst.write(f':SOUR:CURR {curr:.5f}')
            t1 = time.time()
            times.append(t1 - t0)
            print(f"{i+1:2d}. komut: {curr:.3f} A, komut süresi: {(t1-t0)*1000:.1f} ms")
            time.sleep(interval)
        print(f"Ortalama komut süresi: {sum(times)/len(times)*1000:.1f} ms")

finally:
    inst.write(':OUTP OFF')
    inst.write('SYST:LOC')
    inst.close()
    rm.close()
    print("Test tamamlandı, cihaz kapatıldı.")
