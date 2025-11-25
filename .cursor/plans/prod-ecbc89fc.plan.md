<!-- ecbc89fc-9f64-498a-a17b-870a8bc6547f 2c810e01-091b-4b30-93ed-17c44cc11fc7 -->
# Prodigit CSV Profile Implementation

## 1. Sync & Baseline Review

- Verify repo is up to date (`git status`, `git pull`) and note existing Prodigit GUI state.
- Inspect `gui/controllers/keithley_controller.py` (`load_current_profile`, `run_current_profile`) plus shared logging utilities to understand CSV parsing, timing, and busy handling.

## 2. Map Prodigit CC Capabilities

- From `docs/90034000A5_34000A-505_34000A series Operation Manual-rD.pdf`, confirm CC command set (`STAT:MODE CC`, `CURR:HIGH`, `STAT:LOAD ON/OFF`), safe ranges, and timing considerations for continuous 1 Hz operation.
- Define guardrails (max current per range, min dwell) for ~1 hour profiles.

## 3. Extend `ProdigitController`

- Implement `load_current_profile` mirroring the Keithley parser (expects `time_s`, `current_a`, derives `duration_s`, validates limits).
- Add `run_cc_profile(profile_path: str, sample_period=1.0)` that marks the device busy, steps through CSV rows, enforces CC mode, applies current setpoints, sleeps per duration, optionally samples measurements each second, and handles abort/error cleanup.

## 4. Update GUI Prodigit Tab

- Add CSV selector, profile summary (segment count, current range, estimated duration), and start/stop controls.
- Run the profile on a worker thread so the GUI stays responsive during ~1 hour tests; display live measurements/log status.
- Surface log path/results after completion.

## 5. Verification, Logging & Docs

- Extend logging utilities to store Prodigit runs under `logs/` with per-second entries (set current + measured V/I/P + timestamp).
- Provide a CLI/helper test (mock controller) to simulate CSV execution, plus GUI-level checks for button enable/disable.
- Document the workflow in `gui/README.md` (CSV format reuse, safety notes referencing the Prodigit manual).

### To-dos

- [ ] Review Keithley profile implementation
- [ ] Confirm Prodigit CC commands & limits
- [ ] Implement Prodigit profile parser/runner
- [ ] Add GUI controls for Prodigit profile
- [ ] Add logging + tests/docs