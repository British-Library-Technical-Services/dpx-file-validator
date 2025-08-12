 # DPX File Validation Service

CLI‑assisted validation workflow for film scan (DPX) image sequences and associated magnetic (WAV) audio files. Automates inventory capture, technical profile conformance checks, checksum verification, frame sequence integrity checks, and (optionally) structured reporting.

---
## Table of Contents
1. Overview
2. Core Workflows
3. Architecture
4. Environment & Dependencies
5. Setup
6. Usage
7. File & Naming Conventions
8. Inventory JSON Schema
9. Sequence Validation
10. Checksums
11. Technical Attribute Validation
12. Reporting
13. Logging
14. Configuration
15. Troubleshooting

---
## 1. Overview
The service supports preservation ingest quality control by ensuring:
* DPX frame ranges are numerically complete
* MD5 checksums either per‑file (WAV sidecars) or per‑sequence (manifest) verify successfully.
* Core technical attributes match an approved profile (DPX & WAV) via MediaInfo.
* A machine‑readable JSON inventory can be updated during the process.
* Summary metrics are logged and optionally written to a Markdown report.

---
## 2. Core Workflows
### 2.1 Standard Validation Run
1. Launch the service (interactive folder chooser).
2. Inventory pass: enumerate DPX + WAV files, update JSON inventory (mark found, accumulate size & count, track format presence).
3. Validation pass: for each directory
   * Technical attribute validation (MediaInfo JSON) for each file.
   * DPX sequence manifest vs file count comparison.
   * Frame number continuity check (gap detection).
   * Checksum verification (per‑file sidecars for WAV, manifest lines for DPX).
4. Aggregated results logged; optional report creation via `ReportGenerator` (call manually if desired).

---
## 3. Architecture
Module | Responsibility
-------|---------------
`dpx_validation_service.py` | Orchestrates full two‑phase run (inventory + validation)
`inventory_generator.py` | Parses filenames, updates JSON inventory records
`validators/file_attributes_validator.py` | MediaInfo JSON parsing & profile conformance
`validators/checksum_validator.py` | MD5 digest generation & comparison
`validators/dpx_sequence_validator.py` | Manifest count + frame numbering continuity
`data/file_attributes_model.py` | Expected attribute maps & MediaInfo switches
`data/billboard_text.py` | Console status banner helpers
`config.py` | Glob patterns / extensions configuration
`progress_loop.py` | Simple spinner feedback utility
`logging_config.py` | Timestamped file logging setup
`report_generator.py` | Markdown summary (optional post‑processing)

External Tooling:
* MediaInfo (CLI) – technical metadata extraction.

---
## 4. Environment & Dependencies
Python: 3.9+ recommended.

Python packages (install via requirements, see sample below):
* `python-dotenv`
* `tqdm`
* (Standard library: `logging`, `glob`, `json`, `tkinter`, etc.)

External executables on PATH:
* `mediainfo` (required) – provides JSON output used for profile checks.

Environment variables (via `.env`):
```
TEST_LOCATION=/absolute/path/for/automated/run   # Optional – skip GUI
JSON_FILE=/absolute/path/to/inventory.json       # Required for inventory pass
```

---
## 5. Setup
```bash
git clone https://github.com/British-Library-Technical-Services/dpx-file-validator.git
cd dpx-file-validator
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt  # (create one if not present, see below)
cp .env.example .env  # (create .env if no example supplied)
```
Install MediaInfo via your package manager (e.g. macOS: `apt install mediainfo`).

---
## 6. Usage
Interactive run (GUI folder chooser):
```bash
python dpx_validation_service.py
```
---
## 7. File & Naming Conventions
* DPX files: Expected to follow a pattern with underscore‑separated tokens and a frame number token at index 5 (0‑based) before `.dpx` (e.g. `BL_SHELFMARK_SIDE_FILE_VERSION_00001234.dpx`).
* WAV files: Arbitrary naming accepted; shelfmark extracted from full stem.
* WAV checksum sidecar: `<filename>.md5` in same directory.
* DPX checksum manifest: Glob pattern from `config.CONFIG['extensions']['CHECKSUM']` (default `*.md5`).

---
## 8. Inventory JSON Schema
The inventory file referenced by `JSON_FILE` must contain a root key `inventory` holding a list of objects. Each object uses ordered keys interpreted as: `[shelfmark, found, format, directory, size, count]`. Example minimal structure:
```json
{
  "inventory": [
    {"C1234": false, "found": false, "format": false, "directory": "", "size": 0, "count": 0}
  ]
}
```
The generator updates `found`, `directory`, `size`, `count`, and sets `format` true when matched type (film/mag) encountered.

---
## 9. Sequence Validation
Performed by `SequenceValidator`:
* Manifest line count (expected frames) vs actual DPX file count.
* Detection of numeric gaps between the first frame and subsequent frames.
Critical log entries are emitted for mismatches or missing frames; missing frame numbers accumulated for reporting.

---
## 10. Checksums
Two modes:
* Per‑file: WAV sidecar `<file>.md5` compared to freshly computed MD5.
* Per‑sequence: DPX manifest line MD5 (first 32 hex chars) vs each frame's digest.
Failures recorded and listed under checksum summary; missing sidecars logged as errors.

---
## 11. Technical Attribute Validation
`FileValidator` runs MediaInfo (`--Output=JSON`) then validates against maps in `data/file_attributes_model.py`:
* WAV: `Format=PCM`, `SamplingRate=48000`, `BitDepth=24`.
* DPX: Version, Compression=Raw, Endianness=Big, Packing=Filled A, 2048x1556, PixelAspectRatio 1.000, DisplayAspectRatio 1.316, ColorSpace RGB, BitDepth 10, Compression_Mode Lossless.
Failures produce critical log entries and mark the file as not verified.

---
## 12. Reporting
Optional Markdown report creation via `ReportGenerator` (not automatically invoked in `main()` by default; integrate as needed). Sections include:
* Summary timings & counts.
* File count vs manifest.
* Sequence integrity (missing frame list if any).
* Checksum results.
* Attribute validation results.
Report filename pattern: `<directory_basename>_<end_time>.md` inside the chosen root.

---
## 13. Logging
Configured by `logging_config.setup_logger()`:
* Location: `./logs/` (created if missing).
* Filename pattern: `YYYY-MM-DD_HH-MM-SS_dpx_data.log`.
* Level: INFO (errors/critical escalated automatically).
Enable console echo by uncommenting the `StreamHandler` in `logging_config.py`.

---
## 14. Configuration
`config.py` governs extensions:
```python
CONFIG = {
  "extensions": {
    "MAG": "*.wav",
    "FILM": "*.dpx",
    "CHECKSUM": "*.md5",
    "HASH_FORMAT": "md5"
  }
}
```
---
## 15. Troubleshooting
Issue | Cause | Action
----- | ----- | ------
No files detected | Wrong root chosen | Re-run and select correct parent folder
Missing JSON inventory | `JSON_FILE` path invalid | Point `.env` to correct JSON; ensure readable
MediaInfo errors | Tool not installed / not on PATH | Install MediaInfo and retry
Checksum mismatches | Corruption or wrong manifest | Recompute sidecars / manifest; verify storage medium
Sequence mismatch | Missing or extra DPX frames | Investigate source scan; recapture / rebuild manifest
Attribute validation failure | Non‑conformant profile | Confirm scanning settings; update validation map only if profile change is intentional
---
