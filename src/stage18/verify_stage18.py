#!/usr/bin/env python3
import csv,json,zipfile,collections,math
from pathlib import Path
D=Path(__file__).resolve().parent
load=lambda x:list(csv.DictReader((D/x).open()))
s=load('stage18_pooled_summary.csv');r=load('stage18_cases.csv');f=load('stage18_fold_results.csv');q=load('stage18_selected_models.csv');p=json.loads((D/'stage18_protocol.json').read_text())
assert len(r)==27004,len(r)
assert len(s)==12 and len(f)==60 and len(q)==20
assert set(x['model'] for x in s)=={'command_only','causal_zero_offset','lag_selection','timing_ensemble'}
assert len(set((x['fold'],x['row'],x['horizon_ms'],x['model']) for x in r))==len(r)
for v in s:
 a=[float(z['position_error_mm'])**2 for z in r if z['model']==v['model'] and z['horizon_ms']==v['horizon_ms']]
 assert len(a)==int(v['windows']) and abs(math.sqrt(sum(a)/len(a))-float(v['position_rmse_mm']))<1e-9,v
for k in ('original_zip_sha256','bad_time_intervals','bad_timestamp_nonpositive','caveats'):assert k in p
for x in r:
 fold=int(x['fold']);pl=int(x['plateau_id']);nseg=p['n_plateaus']; teststart=(50+(fold-1)*10)/100;testend=(60+(fold-1)*10)/100
 assert pl>=int(nseg*teststart) and pl<min(nseg,int(nseg*testend)) if testend<1.0 else pl>=int(nseg*teststart)
with zipfile.ZipFile('/mnt/data/doi-10.18419-darus-5799.zip') as z:assert 'sampled_data/arbitrary_inputs/raw_data.txt' in z.namelist()
print('PASS: 27,004 unique evaluations; 5 disjoint chronological test folds; 12 pooled summaries, 60 fold rows, 20 selections, source present, exact aggregate RMSE reconciliation')
