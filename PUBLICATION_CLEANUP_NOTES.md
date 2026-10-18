# Publication-facing cleanup notes

The scientific wording in README.md has been revised to replace internal stage-centric narrative.

Do NOT mass-rename the internal Python source filenames, protocol JSON files, result CSVs, or folder names without updating their file-path dependencies and rerunning the analyses. Their original names are kept deliberately for provenance.

Future verified refactoring could rename `stage18` to `prediction_accuracy` and `stage19` to `uncertainty_calibration`, while adjusting every dependent script and comparing all regenerated output files.

Remove any internal-stage terms from the journal manuscript and any public descriptions; retain the original raw outputs as an auditable artifact.
