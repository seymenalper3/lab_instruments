#!/usr/bin/env python3
# demo_pulse_softrest_ramp.py
# Keithley 2281S – FUNC POW, 2 × (30 s pulse + 30 s soft-rest) + kademeli ramp

import pyvisa, time, csv, datetime, re, sys

# ——— PARAMETRELER ———
PULSES        = 2            # 2 çevrim ≈ 2 dk
PULSE_ON      = 30           # s
PULSE_OFF     = 30           # s
STEP          = 0.5          # s – ölçüm aralığı
AUTO_I_LIM    = 1.0          # A
SOFT_I_LIM    = 0.0001       # A (100 µA)
RAMP_SEQ_DN   = [(0.2, 2), (0.05, 2)]   # (A, s) – pulse→rest
RAMP_SEQ_UP   = [(0.05, 2), (0.2, 2)]   # rest→pulse
VOC_TOL       = 0.0002       # V (0,2 mV)
TRACE_PTS     = 4000         # Trace tampon kapasitesi

# ——— VISA ———
rm   = pyvisa.ResourceManager('@py')
inst = rm.open_resource('USB0::1510::8833::4587429::0::INSTR')   # adresinizi girin
inst.read_termination = inst.write_termination = '\n'
inst.timeout = 5000

def w(cmd): print('[W]', cmd); inst.write(cmd)
def q(cmd): r = inst.query(cmd).strip(); print('[Q]', cmd, '⇒', r); return r

num_re = re.compile(r'([-+0-9.]+E[+-]\d+|[-+0-9.]+)')
to_f   = lambda t: float(num_re.match(t).group(0)) if num_re.match(t) else float('nan')

# ——— CİHAZ HAZIRLIĞI ———
w('*CLS'); w('SYST:REM')
w(':FUNC POW')
w(':SOUR:VOLT 0')
w(f':CURR {AUTO_I_LIM}')
w(':SYST:AZER OFF')
w(':FORM:ELEM CURR,VOLT,REL')
# — Trace (isteğe bağlı) —
w(':TRAC:CLE'); w(f':TRAC:POIN {TRACE_PTS}'); w(':TRAC:FEED SENS'); w(':TRAC:FEED:CONT ALW')

w(':OUTP ON')

# ——— CSV ———
fname = f'demo_softrest_ramp_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv'
t0 = time.time()
last_voc = 0.0

def log_row(wr, mode, volt, curr):
    wr.writerow([f'{time.time()-t0:.2f}', mode, f'{volt:.6f}', f'{curr:.6f}'])

try:
    with open(fname, 'w', newline='') as fcsv:
        wr = csv.writer(fcsv)
        wr.writerow(['elapsed_s', 'mode', 'volt_v', 'curr_a'])

        for n in range(1, PULSES+1):

            # ===== RAMP-UP (REST → PULSE) =====
            for lim, dur in RAMP_SEQ_UP:
                print(f'>>> Ramp-UP {lim} A — {dur}s')
                w(f':CURR {lim}'); w(':SOUR:VOLT 0')
                t_end = time.time() + dur
                while time.time() < t_end:
                    i,v,_ = q(':READ?').split(',')[:3]
                    log_row(wr, 'RAMP-UP', to_f(v), to_f(i)); fcsv.flush()
                    time.sleep(STEP)

            # ===== PULSE =====
            print(f'\n>>> {n}. DARBE — {PULSE_ON}s @ 1 A')
            w(f':CURR {AUTO_I_LIM}'); w(':SOUR:VOLT 0')
            t_end = time.time() + PULSE_ON
            while time.time() < t_end:
                i,v,_ = q(':READ?').split(',')[:3]
                last_voc = to_f(v)
                log_row(wr, 'PULSE', last_voc, to_f(i)); fcsv.flush()
                time.sleep(STEP)

            # ===== RAMP-DOWN (PULSE → REST) =====
            for lim, dur in RAMP_SEQ_DN:
                print(f'>>> Ramp-DOWN {lim} A — {dur}s')
                w(f':CURR {lim}');  # Volt hâlâ 0 V
                t_end = time.time() + dur
                while time.time() < t_end:
                    i,v,_ = q(':READ?').split(',')[:3]
                    last_voc = to_f(v)
                    log_row(wr, 'RAMP-DN', last_voc, to_f(i)); fcsv.flush()
                    time.sleep(STEP)

            # ===== SOFT-REST =====
            print(f'>>> Dinlenme — {PULSE_OFF}s (adaptive)')
            w(f':CURR {SOFT_I_LIM}'); w(f':SOUR:VOLT {last_voc:.4f}')
            t_end = time.time() + PULSE_OFF
            while time.time() < t_end:
                i,v,_ = q(':READ?').split(',')[:3]
                curr = to_f(i);  volt = to_f(v)
                # Voc güncelle
                if abs(volt - last_voc) > VOC_TOL:
                    last_voc = volt
                    w(f':SOUR:VOLT {last_voc:.4f}')
                log_row(wr, 'REST', volt, curr); fcsv.flush()
                time.sleep(STEP)

    print(f'\n✔ Ölçümler kaydedildi → {fname}')

finally:
    try:
        w(':OUTP OFF'); w('SYST:LOC')
    except Exception as e:
        print('Kapatırken uyarı:', e, file=sys.stderr)
    inst.close(); rm.close()
