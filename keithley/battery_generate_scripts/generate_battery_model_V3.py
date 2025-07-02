#model oluşturma + model csv(discharge yok)

#!/usr/bin/env python3
import time, csv, pyvisa

MODEL_SLOT = 4                    # kaydettiğiniz slot
CSV_NAME   = f"battery_model_{MODEL_SLOT}.csv"

# ── Yardımcı I/O ────────────────────────────────────────────────────────────
def w(inst, cmd):
    inst.write(cmd);  print("[W]", cmd)

def q(inst, cmd):
    r = inst.query(cmd).strip();  print("[Q]", cmd, "=>", r);  return r

def wait_opc(inst, t_ms=300000):  # max 5 dk
    inst.timeout = t_ms
    q(inst, '*OPC?')              # 1 dönene kadar bloklar
    inst.timeout = 5000

def wait_ready(inst, t_max=8*3600, poll=3):
    t0 = time.time()
    while True:
        cond = int(q(inst, ':STAT:OPER:INST:ISUM:COND?'))
        if cond & 0x10 == 0:      # bit-4 sıfırsa ölçüm bitti
            return
        if time.time() - t0 > t_max:
            raise TimeoutError("Battery test bitmedi (>%d s)." % t_max)
        time.sleep(poll)

def export_model(inst, slot, csv_path):
    w(inst, f':BATT:MOD:RCL {slot}')        # modeli recall et
    rows = []
    for i in range(101):
        resp = q(inst, f':BATT:MOD{slot}:ROW{i}?')  # “Voc,Res”
        if resp:
            voc, esr = map(float, resp.split(','))
            rows.append([i, voc, esr])
    if rows:
        with open(csv_path, 'w', newline='') as f:
            csv.writer(f).writerows([['Step', 'Voc (V)', 'ESR (Ω)']] + rows)
        print(f">>> {len(rows)} satır {csv_path} dosyasına yazıldı.")
    else:
        print(">>> Model verisi bulunamadı!")

# ── Ana akış ────────────────────────────────────────────────────────────────
rm   = pyvisa.ResourceManager('@py')
inst = rm.open_resource('USB0::1510::8833::4587429::0::INSTR')
inst.read_termination = inst.write_termination = '\n'
inst.timeout = 5000

try:
    # 0) temiz başlangıç
    w(inst, '*CLS'); w(inst, 'SYST:REM')
    w(inst, ':BATT1:DATA:CLE')

    # 1) deşarj testi
    w(inst, ':BATT:TEST:MODE DIS')
    w(inst, ':BATT:TEST:VOLT 3.0')
    w(inst, ':BATT:TEST:CURR:END 0.4')
    w(inst, ':BATT:OUTP ON'); wait_ready(inst); w(inst, ':BATT:OUTP OFF')

    # 2) AH-ESR karakterizasyon ayarları
    w(inst, ':BATT:TEST:SENS:AH:VFUL 4.20')
    w(inst, ':BATT:TEST:SENS:AH:ILIM 1.00')
    w(inst, ':BATT:TEST:SENS:AH:ESRT S30')

    # 3) Ölçüm + modelleme
    w(inst, ':BATT:TEST:SENS:AH:EXEC STAR'); wait_ready(inst)

    # 4) Modeli kaydet
    w(inst, ':BATT:TEST:SENS:AH:GMOD:RANG 2.5,4.2')
    w(inst, f':BATT:TEST:SENS:AH:GMOD:SAVE:INTernal {MODEL_SLOT}')
    wait_opc(inst)                               # kaydetme tamam mı?
    inst.timeout = 60000
    slots = q(inst, ':BATT:TEST:SENS:AH:GMOD:CAT?')
    inst.timeout = 5000
    print(">>> Dolular:", slots)

    # 5) MODELi CSV’ye dışa aktar
    export_model(inst, MODEL_SLOT, CSV_NAME)

finally:
    w(inst, ':BATT:OUTP OFF'); w(inst, 'SYST:LOC')
    inst.close(); rm.close()
    print("Cihaz yerel moda alındı, oturum kapatıldı.")
