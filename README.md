# Causal command-history filtering for differential-drive robot motion prediction

## Overview
This repository accompanies the manuscript *Causal Command-History Filtering for Differential-Drive Robot Motion Prediction: Chronological Evaluation of Horizon-Dependent Accuracy and Uncertainty Calibration*.

The study compares command-only kinematic forecasting with causal command-history filtering and historical-command variants using a measured differential-drive robot record. Point-prediction accuracy and prediction-error calibration are evaluated separately using chronology-preserving splits.

## Data
The original measurements are available from [DaRUS](https://doi.org/10.18419/DARUS-5799). They are **not redistributed here**. See `data/README.md` for the required source archive and checksum information.

## Repository contents
- `src/stage18/`: chronological point-prediction accuracy analysis, model selection, and associated checks.
- `src/stage19/`: subsequent chronological residual-calibration and prediction-bound analysis.
- `results/stage18/`: reference output tables for accuracy comparisons.
- `results/stage19/`: reference output tables for coverage and calibration.
- `requirements.txt`: Python dependencies.

**Archival names:** The directory names `stage18` and `stage19` and corresponding filenames are retained from the research workflow solely to preserve consistency with the executable scripts and existing reference outputs. They refer, respectively, to **point-prediction accuracy** and **prediction-error calibration**; they are not scientific method names or publication-stage claims.

## Reproducing the analysis
Use a Python environment with the packages in `requirements.txt`. Set `STUTTGART_ZIP` to the full path of the original DaRUS ZIP archive.

On Windows PowerShell, for example:

```powershell
python -m pip install -r requirements.txt
$env:STUTTGART_ZIP = 'D:\path\to\doi-10.18419-darus-5799.zip'
python src/stage18/stage18_blocked_timing.py
$env:STAGE18_SELECTION = (Resolve-Path 'src/stage18/stage18_selected_models.csv').Path
python src/stage19/stage19_prediction_intervals.py
```

The point-prediction script writes its outputs beside the source script. Compare the regenerated CSV files with the archived reference outputs in `results/stage18/` and `results/stage19/`. **These instructions and the full numerical reproduction have not yet been verified in a clean external environment.** Follow the original source scripts and protocol JSON files if the output paths differ. Do not claim an independent reproduction until it is completed.

## Scope and limitations
The observations belong to one continuously recorded physical robot experiment, not multiple independent robot trials. The models predict from measured issue-time pose and logged commanded velocities. Filter parameters are not independently identified physical actuator delays. Residual threshold coverage reported for later time blocks is empirical and carries no guaranteed coverage under temporal drift.

## Manuscript summary
For 100, 250, and 500 ms prediction horizons, causal filtering reduced pooled position RMSE from 4.562 to 3.009 mm, from 8.619 to 7.707 mm, and from 25.238 to 24.825 mm, respectively. Nominal 90% position-bound coverage on separate chronological evaluations was 85.6%, 83.4%, and 87.3%.

## Software and content reuse
The repository currently carries no explicit code license. A license should be selected only after all contributors approve applicable permissions. The original DaRUS data are subject to their own license and attribution requirements.

## Citation
Please cite the DaRUS source dataset. Once the manuscript has a DOI, add its verified citation here. Do not invent a publication DOI.
