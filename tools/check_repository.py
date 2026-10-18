#!/usr/bin/env python3
"""Offline, dataset-free code/package readiness checks; NOT a scientific reproduction."""
from pathlib import Path
import ast,csv,json,sys
root=Path(__file__).resolve().parent.parent
scripts=list((root/'src').rglob('*.py'))
assert scripts, 'Missing Python scripts'
for path in scripts: ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
for folder in ('stage18','stage19'):
    csvs=list((root/'results'/folder).glob('*.csv'))
    assert csvs, f'No archived CSVs for {folder}'
    for file in csvs:
        with file.open(newline='',encoding='utf-8-sig') as f:
            rd=csv.DictReader(f); assert rd.fieldnames, f'No CSV header: {file}'
for filename in ['README.md','requirements.txt','data/README.md','data/source_sha256.txt','src/stage18/stage18_blocked_timing.py','src/stage19/stage19_prediction_intervals.py']:
    assert (root/filename).is_file(),filename
print(f'PASS: {len(scripts)} Python files parsed; archived CSV headers valid. Data-driven reproducibility NOT tested.')
