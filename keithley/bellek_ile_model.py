#!/usr/bin/env python3
"""
Keithley 2281S – resume / complete AH-ESR test and export the battery model.
• Works whether the test is actively running, paused, or already finished.
• After completion, saves the model to an internal slot and writes it to CSV.

SCPI references:
  - STAT:OPER:INST:ISUM:COND?   → bit-4 = 16  (Measurement running/paused)
  - OUTP?                       → 0 / 1
  - BATT:TEST:SENS:AH:EXEC CONT → resume paused test
  - BATT:TEST:SENS:AH:GMOD      → range & save
  - BATT:MOD<RCL>, :ROW<i>?     → read model rows
"""

import time, csv, pyvisa, sys

RESOURCE   = 'USB0::1510::8833::4587429::0::INSTR'
MODEL_SLOT = 4                # 1-9 internal memory
CSV_FILE   = f"battery_model_{MODEL_SLOT}.csv"
RANGE_LOW, RANGE_HIGH = 2.5, 4.2   # model voltage range
POLL_SEC   = 10                # poll interval while waiting
TIMEOUT_S  = 8 * 3600          # max wait 8 h (adjust as needed)

# ── Helper I/O ────────────────────────────────────────────────────────────────
def w(inst, cmd):  inst.write(cmd);  print("[W]", cmd)
def q(inst, cmd):  r = inst.query(cmd).strip(); print("[Q]", cmd, "→", r); return r

def measurement_running(cond):      # bit-4 set?
    return (cond & 0x10) != 0

# ── Export model to CSV ───────────────────────────────────────────────────────
def export_model(inst, slot, csv_path):
    w(inst, f':BATT:MOD:RCL {slot}')
    rows = []
    for i in range(101):
        resp = q(inst, f':BATT:MOD{slot}:ROW{i}?')
        if resp:
            voc, esr = map(float, resp.split(','))
            rows.append([i, voc, esr])
    if not rows:
        print(">>> Model empty -- nothing exported.")
        return
    with open(csv_path, 'w', newline='') as f:
        csv.writer(f).writerows([['Step', 'Voc (V)', 'ESR (Ω)']] + rows)
    print(f">>> {len(rows)} rows written to {csv_path}")

# ── Main procedure ───────────────────────────────────────────────────────────
rm   = pyvisa.ResourceManager('@py')
inst = rm.open_resource(RESOURCE)
inst.read_termination = inst.write_termination = '\n'
inst.timeout          = 5000     # per-command timeout

try:
    w(inst, 'SYST:REM')                       # remote control
    cond = int(q(inst, ':STAT:OPER:INST:ISUM:COND?'))
    outp = q(inst, ':OUTP?')

    # ------------------------------------------------------------------------
    # 1) Decide what to do with the measurement
    # ------------------------------------------------------------------------
    if measurement_running(cond):
        if outp == '0':                       # paused – resume
            print(">>> Measurement PAUSED – resuming.")
            w(inst, ':BATT:OUTP ON')
            w(inst, ':BATT:TEST:SENS:AH:EXEC CONT')
        else:
            print(">>> Measurement already RUNNING – waiting.")

        # Wait until bit-4 clears
        t0 = time.time()
        while measurement_running(int(q(inst, ':STAT:OPER:INST:ISUM:COND?'))):
            if time.time() - t0 > TIMEOUT_S:
                raise TimeoutError("Measurement did not finish within limit.")
            time.sleep(POLL_SEC)
        print(">>> Measurement finished.")

    else:
        print(">>> Measurement already complete – proceeding to model step.")

    # ------------------------------------------------------------------------
    # 2) Save / generate the model
    # ------------------------------------------------------------------------
    w(inst, f':BATT:TEST:SENS:AH:GMOD:RANG {RANGE_LOW},{RANGE_HIGH}')
    w(inst, f':BATT:TEST:SENS:AH:GMOD:SAVE:INT {MODEL_SLOT}')
    print(f">>> Model saved to internal slot {MODEL_SLOT}.")

    # ------------------------------------------------------------------------
    # 3) Export to CSV
    # ------------------------------------------------------------------------
    export_model(inst, MODEL_SLOT, CSV_FILE)

except Exception as e:
    print("ERROR:", e, file=sys.stderr)

finally:
    try:
        w(inst, ':BATT:OUTP OFF')
    except pyvisa.VisaIOError:
        pass                                   # ignore if already off/closed
    w(inst, 'SYST:LOC')
    inst.close(); rm.close()
    print(">>> Instrument returned to LOCAL, session closed.")
