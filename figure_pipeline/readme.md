# Figure Pipeline: Local Execution Guide

This guide explains exactly how to run and iterate the article figures on your local machine.

## What this pipeline produces
The script generates three storyline-aligned figures:
1. **BAU baseline**: waste generation, leakage, and GHG over time.
2. **Intervention effects**: CDS/RES/RSS/SCS changes in leakage and GHG vs BAU.
3. **Cost-effectiveness + co-abatement**: PV cost per ton avoided and cumulative GHG/leakage co-abatement.

Output folder:
- `figure_pipeline/output/`

---

## 1) Prerequisites
Install the following on your computer:
- Python **3.10+**
- `pip`

Verify:
```bash
python --version
pip --version
```

---

## 2) Clone/open the repository
```bash
git clone <your-repo-url>
cd P2O_Results
```

---

## 3) Create and activate a virtual environment (recommended)
### macOS/Linux
```bash
python -m venv .venv
source .venv/bin/activate
```

### Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

## 4) Install dependencies
```bash
python -m pip install --upgrade pip
python -m pip install matplotlib
```

Optional verification:
```bash
python - <<'PY'
import matplotlib
print('matplotlib version:', matplotlib.__version__)
PY
```

---

## 5) Run the figure generator
From repo root:
```bash
python figure_pipeline/scripts/generate_storyline_figures.py --data-dir . --out-dir figure_pipeline/output
```

You should see:
- `figure_pipeline/output/Fig1_BAU_baseline.png`
- `figure_pipeline/output/Fig2_Intervention_impacts.png`
- `figure_pipeline/output/Fig3_Cost_effectiveness_and_coabatement.png`

---

## 6) Alternative run options
### Using shell wrapper
```bash
bash figure_pipeline/run_figures.sh . figure_pipeline/output
```

### Using Makefile
```bash
cd figure_pipeline
make figures
```

Clean generated files:
```bash
make clean
```

---

## 7) Iteration workflow (recommended)
1. Edit plotting logic in: `figure_pipeline/scripts/generate_storyline_figures.py`
2. Adjust style settings in: `figure_pipeline/config/style.yaml`
3. Re-run generation command.
4. Inspect output PNGs.
5. Repeat until visually final.

---

## 8) Common troubleshooting
### `ModuleNotFoundError: No module named 'matplotlib'`
Reinstall in active environment:
```bash
python -m pip install matplotlib
```

### Figures not updating
- Ensure you are running from repo root.
- Confirm `--out-dir` path.
- Delete old files and regenerate:
```bash
rm -f figure_pipeline/output/*.png
python figure_pipeline/scripts/generate_storyline_figures.py --data-dir . --out-dir figure_pipeline/output
```

### Font differences across systems
Arial/Helvetica may render differently by OS. Keep font families installed locally for consistent results.

---

## 9) Reproducibility checklist
Before final export, confirm:
- Same Python + matplotlib versions across machines.
- Same scenario ordering (BAU, CDS, RES, RSS, SCS).
- Same input CSV files from repo root.
- Freshly regenerated outputs in `figure_pipeline/output/`.
