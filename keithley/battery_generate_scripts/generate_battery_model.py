#discharge + model csv + model kaydetme

#!/usr/bin/env python3
import time, csv, pyvisa

# ============================================================================ #
#  Yardımcı fonksiyonlar
# ============================================================================ #
def w(inst, cmd):
    inst.write(cmd)
    print("[W] ", cmd)

def q(inst, cmd):
    r = inst.query(cmd).strip()
    print("[Q] ", cmd, "=>", r)
    return r

def wait_opc(inst, t_ms=300000):
    inst.timeout = t_ms
    q(inst, '*OPC?')
    inst.timeout = 5000

def wait_ready(inst, t_max=8*3600, poll=3):
    """
    Ölçüm sırasında :STAT:OPER:INST:ISUM:COND? sorgusunda
    bit-4 (16) 'Measurement running' aktif olur.
    Bu bit temizlenince (cond & 0x10 == 0) fonksiyondan çık.
    """
    t0 = time.time()
    while True:
        cond = int(q(inst, ':STAT:OPER:INST:ISUM:COND?'))
        if cond & 0x10 == 0:                # Measurement biti sıfırlandı → bitti
            return
        if time.time() - t0 > t_max:        # güvenlik zaman aşımı
            raise TimeoutError("Battery test bitmedi (>%d s)." % t_max)
        time.sleep(poll)

# ============================================================================ #
#  Ana akış
# ============================================================================ #
rm   = pyvisa.ResourceManager('@py')
inst = rm.open_resource('USB0::1510::8833::4587429::0::INSTR')
inst.read_termination  = '\n'
inst.write_termination = '\n'
inst.timeout           = 5000        # SCPI satırı için 5 s

try:
    # --- 0) Temiz başlangıç ---------------------------------------------------
    w(inst, '*CLS');  w(inst, 'SYST:REM')
    w(inst, ':BATT1:DATA:CLE')            # eski logları temizle

# --- 1) Deşarj (V1 / A1) --------------------------------------------------
    w(inst, ':BATT:TEST:MODE DIS')
    w(inst, ':BATT:TEST:VOLT 3.0')        # V1  = 3.0 V
    w(inst, ':BATT:TEST:CURR:END 0.4')  # A1  = 150 mA
    w(inst, ':BATT:OUTP ON')
    wait_ready(inst)                      # Measurement biti sıfırlanana dek
    w(inst, ':BATT:OUTP OFF')

    # --- 2) Karakterizasyon parametreleri -------------------------------------
    w(inst, ':BATT:TEST:SENS:AH:VFUL 4.20')   # V2  = 4.2 V
    w(inst, ':BATT:TEST:SENS:AH:ILIM 1.00')  # A2  = 1 A  (I-Limit ≥ END)
    w(inst, ':BATT:TEST:SENS:AH:ESRT S30')    # örnekleme 30 s

    # --- 3) Ölçüm + Model oluştur --------------------------------------------
    w(inst, ':BATT:TEST:SENS:AH:EXEC STAR')
    wait_ready(inst)                          # bit-4 temizlenene dek bekle

    # --- 4) Model aralığı + kaydet -------------------------------------------
    w(inst, ':BATT:TEST:SENS:AH:GMOD:RANG 2.5,4.2')
    w(inst, ':BATT:TEST:SENS:AH:GMOD:SAVE:INTE 4')
    wait_opc(inst)                # tamamlanana kadar bekle
    slots = q(inst, ':BATT:TEST:SENS:AH:GMOD:CAT?')
    print(">>> Kayıtlı model slotları:", slots)

    # --- 5) Deşarj verisini CSV’e aktar ---------------------------------------
    raw = q(
        inst,
        ':BATT1:DATA:DATA:SEL? 1,9999,"VOLT,CURR,AH,RES,UNIT,REL"'
    )
    rows = [r.split(',') for r in raw.split(';') if r]
    if rows:
        with open('battery_discharge_log.csv', 'w', newline='') as f:
            csv.writer(f).writerows([[
                'Voltage (V)', 'Current (A)',
                'Amp-Hours (Ah)', 'ESR (Ω)',
                'Unit', 'Elapsed s'
            ]] + rows)
        print(f">>> {len(rows)} satır battery_discharge_log.csv dosyasına yazıldı.")
    else:
        print(">>> DATA buffer boş; log dosyası oluşmadı.")

finally:
    w(inst, ':BATT:OUTP OFF');  w(inst, 'SYST:LOC')
    inst.close();  rm.close()
    print("Cihaz yerel moda alındı, oturum kapatıldı.")
