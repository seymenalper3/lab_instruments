#!/usr/bin/env python3
# demo_pulse_test_60s_fix.py
import pyvisa, time, csv, datetime, re, sys

PULSES, PULSE_ON, PULSE_OFF, STEP = 6, 5, 5, 1
OCP_LEVEL = 1.0

### — VISA — ###
rm   = pyvisa.ResourceManager('@py')
inst = rm.open_resource('USB0::1510::8833::4587429::0::INSTR')
inst.read_termination = inst.write_termination = '\n'
inst.timeout = 5000

def w(cmd): print('[W]', cmd); inst.write(cmd)
def q(cmd): r = inst.query(cmd).strip(); print('[Q]', cmd, '⇒', r); return r

# — ÖN AYAR —
w('*CLS'); w('SYST:REM')
w(':FUNC POW'); w(':SOUR:VOLT 0'); w(f':CURR:PROT {OCP_LEVEL}')
w(':OUTP:PROT:CLE'); w(':SYST:AZER OFF')
w(':SENS:FUNC "VOLT","CURR"'); w(':SENS:VOLT:NPLC 0.01'); w(':SENS:CURR:NPLC 0.01')
w(':FORM:ELEM READ,REL')   # I, V, t  (birimli)

num = re.compile(r'([-+0-9.E]+)')          # yalnızca sayıları seç

def to_float(tok:str)->float:
    m = num.match(tok)
    if not m: raise ValueError(f"Sayı bulunamadı: {tok}")
    return float(m.group(1))

fname = f'demo_pulse_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv'
t0 = time.time()

try:
    with open(fname, 'w', newline='') as f:
        wr = csv.writer(f); wr.writerow(['elapsed_s', 'volt_v', 'curr_a'])

        for n in range(1, PULSES+1):
            print(f'\n>>> {n}. DARBE — {PULSE_ON}s');  w(':OUTP ON')
            t_end = time.time() + PULSE_ON
            while time.time() < t_end:
                tok_i, tok_v, tok_t = q(':READ?').split(',')[:3]
                curr = to_float(tok_i); volt = to_float(tok_v)
                elapsed = time.time() - t0
                wr.writerow([f'{elapsed:.1f}', f'{volt:.6f}', f'{curr:.6f}']); f.flush()
                time.sleep(STEP)

            w(':OUTP OFF')
            if n < PULSES:
                print(f'>>> Dinlenme — {PULSE_OFF}s'); time.sleep(PULSE_OFF)

    print(f'\n✔ Veri kaydedildi → {fname}')

finally:
    try: w(':OUTP OFF'); w('SYST:LOC')
    except Exception as e: print("Kapatırken uyarı:", e, file=sys.stderr)
    inst.close(); rm.close()
