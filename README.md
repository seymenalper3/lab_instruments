<img width="1600" height="867" alt="image" src="https://github.com/user-attachments/assets/5965a530-67a7-4cd1-af26-339ce8b91a73" />

# Lab Instruments Control System

Python-based control and monitoring suite for laboratory battery test 
equipment, developed during TÜBİTAK STAR research at ITU Power 
Electronics Lab (Jan 2025 – Jan 2026).

Supports Keithley 2281S, Prodigit 34205A, and Sorensen SGX400-12 — 
replacing ~$1,000 commercial instrument control software with a 
custom Python GUI.

![Main Interface](docs/screenshots/main_gui.png)

---

## What It Does

- **Multi-device control** — Keithley, Prodigit, and Sorensen from a 
  single interface via USB, Ethernet, or Serial (SCPI protocol)
- **Battery characterization** — charge/discharge cycles, pulse tests, 
  aging assessment, battery model generation
- **Current profile playback** — load CSV/Excel profiles, execute 
  automatically with real-time validation (P ≈ V×I, ±5% tolerance)
- **Real-time monitoring** — decoupled sampling rate (0.2s–60s) and 
  GUI update rate (0.1s–60s) for high-frequency data collection
- **Automated logging** — timestamped CSV/Excel output with 
  structured log files
- **Emergency Stop** — single button cuts all device outputs instantly

---

## Architecture

Refactored from a monolithic structure to a modular delegation pattern 
(Dec 2025). Each test type is an independent, testable module:
```
gui/
  controllers/
    base_controller.py       # Abstract base (ABC)
    keithley_controller.py   # Keithley 2281S
    keithley/
      tests/
        pulse_test.py        # KeithleyPulseTest (267 lines)
        battery_model.py     # KeithleyBatteryModel (337 lines)
        profile_runner.py    # KeithleyProfileRunner (220 lines)
    prodigit_controller.py   # Prodigit 34205A
    sorensen_controller.py   # Sorensen SGX400
instruments/
  keithley/src/              # Standalone test scripts
  sgx400/
docs/
  screenshots/               # UI screenshots
  MIMARI.md                  # Architecture & design patterns (30 KB)
  KULLANIM_KILAVUZU.md       # User guide (19 KB)
  GELISTIRICI_REHBERI.md     # Developer guide (28 KB)
  SORUN_GIDERME.md           # Troubleshooting (9 KB)
```

## Screenshots

### Profile Test Running
![Profile Test Running](docs/screenshots/profile_running.png)

### Real-time Monitoring
![Monitoring](docs/screenshots/monitoring.png)

### Debug Console
![Debug Console](docs/screenshots/debug_console.png)

---

## Key Features in Detail

**Prodigit 34205A** — supports CC, CV, CP, and CR modes. CC mode 
includes full profile playback with abort mechanism and profile caching.

**Dual-rate monitoring** — data sampling and GUI refresh run 
independently. Presets: Slow (5s), Standard (1s), Fast (0.5s), 
Maximum (0.2s). Busy devices are automatically skipped with a 
[BUSY] indicator.

**VISA auto-detection** — "Detect" button lists all connected VISA 
devices; double-click to select. Connection settings persist across 
sessions via `~/.lab_instruments/connection_settings.json`.

**Windows build** — standalone `.exe` via PyInstaller. No Python 
installation required on the lab machine.

---

## Getting Started

**Requirements:** Python 3.8+, NI-VISA or Keysight IO Libraries
```bash
git clone <repo-url>
cd lab_instruments/gui
pip install -r requirements.txt
python main.py
```

For Windows: download the pre-built `.exe` from Releases (no Python needed).  
For device manuals and connection setup, see `docs/`.

---

## Context

Built for daily lab operations — used to run battery characterization 
tests, execute custom current profiles, and monitor multiple instruments 
simultaneously. Handed off with full Turkish-language documentation 
(architecture, user guide, developer guide, troubleshooting) for the 
next research assistant.
