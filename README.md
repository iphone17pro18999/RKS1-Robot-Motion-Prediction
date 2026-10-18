# Causal command-history filtering for differential-drive motion prediction

This repository contains original source scripts and derived reference CSV files accompanying the manuscript **Causal Command-History Filtering for Differential-Drive Robot Motion Prediction: Chronological Evaluation of Horizon-Dependent Accuracy and Uncertainty Calibration**.

## Scientific analyses
- **Chronological prediction accuracy** — `src/stage18/stage18_blocked_timing.py`; reference tables in `results/stage18/`.
- **Chronological uncertainty calibration** — `src/stage19/stage19_prediction_intervals.py`; reference tables in `results/stage19/`.

The `stage18`/`stage19` filenames are archival code identifiers from the original analysis, **not paper sections, novel methods, or publication stages**. Keeping these original paths prevents breaking their existing CSV and protocol dependencies. The public-facing scientific descriptions above should be used in manuscripts and repository descriptions.

## Original data
Download the measured arbitrary-input recording from [DaRUS DOI 10.18419/DARUS-5799](https://doi.org/10.18419/DARUS-5799). The original ZIP is not redistributed here. Verify its checksum against `data/source_sha256.txt`; inspect `data/README.md` for its expected internal path. Do not place privately held or unrelated files into this repository.

## Reproduction (Windows PowerShell)
From the repository root, with Python installed:

```powershell
python -m pip install -r requirements.txt
$env:STUTTGART_ZIP = 'D:\YOUR_PATH\doi-10.18419-darus-5799.zip'
python src/stage18/stage18_blocked_timing.py
python src/stage18/stage18_audit_charts.py
$env:STAGE18_SELECTION = (Resolve-Path 'src/stage18/stage18_selected_models.csv').Path
python src/stage19/stage19_prediction_intervals.py
python src/stage19/plot_stage19.py
```

**Important:** The scripts generate new CSVs beside their source files, while published reference CSVs are under `results/`. The Stage 19 script must receive the Stage 18 parameter-selection CSV explicitly via `STAGE18_SELECTION`. Verify outputs manually/with the provided verifier; the full rerun has **not yet been independently verified** against original DaRUS data in a clean environment. Pinned dependency versions and cross-platform results are not yet guaranteed.

Run a source-only readiness audit, which does **not** require the dataset:

```powershell
python tools/check_repository.py
```

## Verified scope and limitations
- One continuous recorded physical robot experiment; neither individual forecast windows nor chronological folds constitute independently replicated robot studies.
- Compared command-only prediction, a causal exponential command-history filter, historical offsets and offset averaging at 100, 250 and 500 ms.
- Nominal 90% residual coverage is empirical and may fail under temporal shift.
- No assertion of identified actuator dead time, docking safety, algorithmic novelty or guaranteed conformal coverage.

## Reuse and citation
The original measurement dataset has separate licensing and attribution conditions. This repository currently has **no explicit code license**; confirm permission with all contributors before adopting one. Reference the DaRUS dataset DOI and, when published, the verified article DOI. No repository DOI is claimed before archival deposition.
