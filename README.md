# Differential-drive robot motion prediction — RKS-1

Source scripts and reported results recovered from the project's existing supplementary package.

## Data and reproducibility

Download original measurement archive from https://doi.org/10.18419/DARUS-5799.

Install dependencies: `pip install -r requirements.txt`.

Set `STUTTGART_ZIP` to the full local path of the original source archive.

1. Execute Stage 18 script `src/stage18/stage18_blocked_timing.py`. This writes results next to the script.
2. Set `STAGE18_SELECTION` to the Stage 18 generated `stage18_selected_models.csv`.
3. Execute `src/stage19/stage19_prediction_intervals.py`.
4. Compare regenerated outputs with `results/stage18` and `results/stage19`.

### Important
This is an assembled **starter package**, NOT a verified public GitHub repository or an externally reproduced run. The original raw data are not included. Some helper scripts may rely on original folder layouts. Validate numeric output and complete repository metadata before public release.

## Interpretation
All folds derive from one physical recording. Fitted command-history offsets are not physical actuator delay estimates. Chronological coverage is empirical and not a guarantee.
