import csv
import datetime as dt
import time
from pathlib import Path

import pandas as pd
import pyvisa

# ----------------------------- CONFIG ------------------------------------
PROFILE_CSV = Path(__file__).with_name("current_profile_for_sourcing.csv")
RESOURCE_STRING = "USB0::1510::8833::4587429::0::INSTR"  # adjust if needed
VOLTAGE_PROTECTION = 4.2  # V – max cell voltage
OUTPUT_DIR = Path(__file__).with_name("results")
OUTPUT_DIR.mkdir(exist_ok=True)
# -------------------------------------------------------------------------

def read_profile(path: Path):
    df = pd.read_csv(path)
    if not {"time_s", "current_a"}.issubset(df.columns):
        raise ValueError("CSV must contain 'time_s' and 'current_a' columns")
    # Calculate dwell times (seconds) as diff between consecutive time points.
    times = df["time_s"].to_numpy()
    currents = df["current_a"].to_numpy()
    # Assume final dwell equals previous interval (or 1 s if single row)
    dwells = [max(0.01, times[i + 1] - times[i]) for i in range(len(times) - 1)]
    dwells.append(dwells[-1] if dwells else 1.0)
    return list(currents), dwells


def connect_instrument(resource: str):
    rm = pyvisa.ResourceManager("@py")  # use pyvisa-py backend
    instr = rm.open_resource(resource)
    instr.read_termination = "\n"
    instr.write_termination = "\n"
    print("Connected to:", instr.query("*IDN?"))
    return instr


def apply_profile(instr, currents, dwells):
    instr.write("*RST; *CLS")
    instr.write("SYST:REM")  # remote mode
    instr.write("SOUR:FUNC:MODE CURR")
    instr.write(f"SOUR:VOLT:PROT {VOLTAGE_PROTECTION}")
    instr.write("OUTP ON")

    log_rows = ["elapsed_s,step,current_set_a,current_meas_a,voltage_v"]
    t0 = time.time()

    try:
        for idx, (curr, dwell) in enumerate(zip(currents, dwells), 1):
            instr.write(f"SOUR:CURR {curr}")
            time.sleep(dwell)
            v_meas = float(instr.query("MEAS:VOLT?"))
            i_meas = float(instr.query("MEAS:CURR?"))
            elapsed = time.time() - t0
            log_rows.append(f"{elapsed:.2f},{idx},{curr},{i_meas},{v_meas}")
            print(f"Step {idx}/{len(currents)} | Set {curr} A | Meas {i_meas:.3f} A, {v_meas:.3f} V")
    finally:
        instr.write("OUTP OFF")
        instr.close()

    # Save log
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = OUTPUT_DIR / f"current_profile_log_{ts}.csv"
    with log_path.open("w", newline="") as f:
        f.write("\n".join(log_rows))
    print("Log saved to", log_path)


def main():
    currents, dwells = read_profile(PROFILE_CSV)
    instr = connect_instrument(RESOURCE_STRING)
    apply_profile(instr, currents, dwells)


if __name__ == "__main__":
    main() 