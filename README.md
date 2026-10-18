# Causal command-history filtering for differential-drive robot motion prediction

This repository accompanies the manuscript **Causal Command-History Filtering for Differential-Drive Robot Motion Prediction: Chronological Evaluation of Horizon-Dependent Accuracy and Uncertainty Calibration**.

## Scientific analyses

- **Chronological prediction accuracy:** `src/stage18/stage18_blocked_timing.py`; archived CSVs in `results/stage18/`.
- **Chronological prediction-uncertainty calibration:** `src/stage19/stage19_prediction_intervals.py`; archived CSVs in `results/stage19/`.

The directory names `stage18` and `stage19` are **legacy filenames** kept for script compatibility. They are not scientific method names or manuscript section numbers.

## Data source

The original measured robot dataset is provided by [DaRUS, DOI 10.18419/DARUS-5799](https://doi.org/10.18419/DARUS-5799). The source ZIP is **not redistributed** in this repository. See `data/README.md` and `data/source_sha256.txt`. Keep the downloaded ZIP outside the Git repository.

## Reproduction on Windows (Command Prompt)

From the repository root, install Python 3.13 and run:

```cmd
py -3.13 -m pip install -r requirements.txt
py -3.13 tools\check_repository.py
set "STUTTGART_ZIP=D:\YOUR_PATH\doi-10.18419-darus-5799.zip"
py -3.13 src\stage18\stage18_blocked_timing.py
set "STAGE18_SELECTION=%CD%\src\stage18\stage18_selected_models.csv"
py -3.13 src\stage19\stage19_prediction_intervals.py
```

Replace `D:\YOUR_PATH\` with the local directory containing the unmodified DaRUS ZIP. Run these commands in the **same** Command Prompt session. The main scripts write generated outputs beside the source scripts; compare those against archived CSVs under `results/` before replacing any reference outputs.

The separate `src/stage18/verify_stage18.py` contains a legacy `/mnt/data/` dataset path and did **not** complete on Windows as-is. It requires a portability fix before it can be treated as an additional independent check; the main numerical analysis scripts do not require that verifier.

## Local reproduction evidence (18 October 2026)

In a Windows Python 3.13.16 environment, the repository structural check passed; the scientific dependency install, `pip check`, and imports passed. The two primary analysis scripts executed successfully on the locally downloaded DaRUS ZIP. Console outputs showed:

| Horizon | Command-only position RMSE (mm) | Causal filter position RMSE (mm) | Causal filter pooled 90% position coverage |
|---|---:|---:|---:|
| 100 ms | 4.562 | 3.009 | 85.6% |
| 250 ms | 8.619 | 7.707 | 83.4% |
| 500 ms | 25.238 | 24.825 | 87.3% |

These values match the manuscript's reported headline figures at the displayed precision. The first script ended with `DONE 27004 records` and the second with `records 20200 done`. Verification is based on observed local terminal outputs; **a clean-environment independent rerun, comprehensive per-file CSV comparison, and additional verifier completion have not been established**. See `REPRODUCTION_STATUS.json`.

## Scientific scope and limitations

- Measurements originate from one continuous physical robot recording; rolling folds are not independent robot experiments.
- Predictions use issue-time measured pose and commanded velocities.
- Causal history-filter parameters do not identify physical actuator delay.
- Empirical interval coverage under chronology-preserving evaluation does not imply guaranteed coverage under drift.
- Do not infer autonomous safety guarantees or algorithmic novelty from these results.

## Reuse and citation

The repository has **no explicit software license** at present. Obtain contributor approval before choosing one. Cite the original DaRUS data source and, once assigned, the verified article DOI. A repository DOI has not yet been minted.
