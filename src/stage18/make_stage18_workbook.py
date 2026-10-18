#!/usr/bin/env python3
from artifact_tool import Workbook, SpreadsheetFile
from pathlib import Path
import csv,json
D=Path(__file__).resolve().parent
read=lambda n:list(csv.DictReader((D/n).open()))
summary=read('stage18_pooled_summary.csv');fold=read('stage18_fold_results.csv');strata=read('stage18_pooled_strata.csv');selected=read('stage18_selected_models.csv');boot=read('stage18_block_resampling.csv');counts=read('stage18_plateau_improvement_counts.csv');plateau=read('stage18_plateau_stats.csv');proto=json.loads((D/'stage18_protocol.json').read_text())
w=Workbook.create()
NAVY='#18344D';TEAL='#0E7482';LIGHT='#E7F2F5';PALE='#F4F7FA';WHITE='#FFFFFF'

def sheet(name,title,sub,headers,rows,widths=None,numcols=()):
 s=w.worksheets.add(name);n=len(headers)
 s.merge_cells(f'A1:{chr(64+n)}2');s.get_range('A1').values=[[title]]
 s.get_range(f'A1:{chr(64+n)}2').format={'fill':NAVY,'font':{'bold':True,'color':WHITE,'size':15},'row_height':25,'vertical_alignment':'center'}
 s.merge_cells(f'A3:{chr(64+n)}3');s.get_range('A3').values=[[sub]]
 s.get_range(f'A3:{chr(64+n)}3').format={'fill':PALE,'font':{'color':NAVY,'size':10},'wrap_text':True,'row_height':30}
 s.get_range_by_indexes(3,0,1,n).values=[headers]
 s.get_range_by_indexes(3,0,1,n).format={'fill':LIGHT,'font':{'bold':True,'color':NAVY},'row_height':32,'wrap_text':True}
 if rows:
  s.get_range_by_indexes(4,0,len(rows),n).values=rows
  s.get_range_by_indexes(4,0,len(rows),n).format.row_height=19
 for i in range(n):s.get_range_by_indexes(0,i,4+max(1,len(rows)),1).format.column_width=widths[i] if widths else 19
 for c in numcols:
  s.get_range_by_indexes(4,c,len(rows),1).set_number_format('0.000')
 s.freeze_panes.freeze_rows(4)
 return s

# Dashboard details include true computed gain from Horizon Summary values
ss=sheet('Dashboard','STAGE 18 | EVIDENCE DASHBOARD','Independent blocks within one measured recording. No docking, actuator-delay or multi-robot validation claim.',
 ['Evidence indicator','Observed evidence','Interpretation','Publication gate'],[
 ['Data source','Original Stuttgart DaRUS-5799 ZIP','119,590 raw pose-command observations, approximately 5 ms','Original source stored separately'],
 ['Evaluation','Five rolling-origin chronological tests','Disjoint test blocks from 50%-100% of one continuous recording','Not five independent physical experiments'],
 ['Quality check','Strict interval and timestamp filters','Reject nonpositive timestamps, jumps and excessive horizon-time drift','Coverage differs across test folds'],
 ['100 ms forecast',None,'Causal filter vs command-only','Improved in pooled 100 ms errors'],
 ['250 ms forecast',None,'Main motion-prediction comparison','Improves short-horizon errors, not a novel model'],
 ['500 ms forecast',None,'Forecast horizon more affected by unknown future commands','Small gain, limited generalization'],
 ['250 ms historical lag',None,'Offset chosen only on earlier validation block','No overall advantage over zero-offset filter'],
 ['250 ms timing ensemble',None,'Three historical offsets with equal weights','Not superior to simple causal filter'],
 ['Transition response','11.414 to 7.357 mm RMSE at 250 ms','Gain concentrated within 150 ms after logged command changes','No real actuator time-constant identification'],
 ['Settled commands','7.786 to 7.790 mm RMSE at 250 ms','No material improvement and slightly worse','Report negative effect'],
 ['250 ms plateaus','172/281 improved','Repeated rows from the same robot recording','Do not interpret as 281 independent experiments'],
 ['Generalization','No second robot or docking-stop measurements','Physical real-data motion analysis only','Additional evidence needed before submission'],
 ],[31,50,65,40]);ss.get_range('A5:D16').format.row_height=40;ss.get_range('A5:D16').format.wrap_text=True
# Cross-sheet formula references to summary sheet specific rows; constructed for numeric values only
mrows=[]
for h in (100,250,500):
 refs={x['model']:x for x in summary if int(x['horizon_ms'])==h}
 row=[h]+[float(refs[m]['position_rmse_mm']) for m in ('command_only','causal_zero_offset','lag_selection','timing_ensemble')]+[float(refs[m]['heading_rmse_deg']) for m in ('command_only','causal_zero_offset')]+[int(refs['command_only']['windows']),None,None,None]
 mrows.append(row)
s=sheet('Horizon Summary','OUT-OF-BLOCK FORECAST ACCURACY','All values calculated from nonoverlapping rolling-test blocks; position in mm and heading in degrees.',
 ['Horizon (ms)','Command-only RMSE','No-offset causal RMSE','Selected-offset RMSE','Ensemble RMSE','Command-only heading','Causal filter heading','Windows','Causal gain (mm)','Causal reduction','Offset vs causal'],mrows,[18,21,22,21,19,23,21,14,17,17,18],numcols=(1,2,3,4,5,6))
for k in (5,6,7):
 s.get_range(f'I{k}').formulas=[[f'=B{k}-C{k}']]
 s.get_range(f'J{k}').formulas=[[f'=(B{k}-C{k})/B{k}']]
 s.get_range(f'K{k}').formulas=[[f'=C{k}-D{k}']]
s.get_range('J5:J7').set_number_format('0.0%');s.get_range('I5:I7').set_number_format('0.000');s.get_range('K5:K7').set_number_format('0.000')
ss.get_range('B8').formulas=[['=\'Horizon Summary\'!J5']];ss.get_range('B9').formulas=[['=\'Horizon Summary\'!J6']];ss.get_range('B10').formulas=[['=\'Horizon Summary\'!J7']]
ss.get_range('B11').formulas=[['=\'Horizon Summary\'!D6-\'Horizon Summary\'!C6']];ss.get_range('B12').formulas=[['=\'Horizon Summary\'!E6-\'Horizon Summary\'!C6']]
ss.get_range('B8:B10').set_number_format('0.0%');ss.get_range('B11:B12').set_number_format('0.000')

fl=[[int(x['fold']),x['validation'],x['test'],x['model'],int(x['horizon_ms']),int(x['windows']),int(x['plateaus']),float(x['position_rmse_mm']),float(x['heading_rmse_deg'])] for x in fold]
sheet('Rolling Folds','CHRONOLOGICAL EVALUATION BLOCKS','Five disjoint test blocks, each selected from earlier validation only; same robot recording.',
 ['Fold','Validation segment','Test segment','Model','Horizon (ms)','N windows','Plateaus','Position RMSE (mm)','Heading RMSE (deg)'],fl,[11,19,19,27,18,17,14,22,22],numcols=(7,8))
cr=[[int(x['fold']),x['model'],x['validation_start_pct'],x['validation_end_pct'],x['test_end_pct'],x['tau_s'] if x['tau_s'] is not None else '',x['historical_offset_ms'] if x['historical_offset_ms'] is not None else '',float(x['validation_250mm_rmse']) if x['validation_250mm_rmse'] not in (None,'') else ''] for x in selected]
sheet('Selected Parameters','VALIDATION-ONLY SELECTION','τ and historical logged-command offset are effective prediction hyperparameters—not physically identified constants.',
 ['Fold','Model','Validation start %','Validation end %','Test end %','Effective tau (s)','Historical offset (ms)','Validation RMSE (mm)'],cr,[11,29,23,22,18,22,23,25],numcols=(5,7))
sr=[[int(x['horizon_ms']),x['model'],x['stratum'],int(x['windows']),float(x['position_rmse_mm']),float(x['heading_rmse_deg'])] for x in strata]
sheet('Transition Strata','COMMAND-CHANGE DIAGNOSTICS','Recent=within 150 ms after observed change. Future-change category uses hindsight ONLY, never a feature.',
 ['Horizon (ms)','Model','Retrospective stratum','Windows','Position RMSE (mm)','Heading RMSE (deg)'],sr,[18,27,24,15,23,23],numcols=(4,5))
br=[[int(x['horizon_ms']),x['model'],int(x['blocks']),int(x['windows']),float(x['baseline_rmse_mm']),float(x['model_rmse_mm']),float(x['gain_mm']),float(x['resample_2p5_mm']),float(x['resample_97p5_mm'])] for x in boot]
sheet('Block Resampling','CONTIGUOUS BLOCK ROBUSTNESS','Descriptive resampling of 15 time groups, not confidence intervals for independent robots or a new population.',
 ['Horizon (ms)','Model','Blocks','Windows','Baseline RMSE','Model RMSE','Gain (mm)','2.5% block gain','97.5% block gain'],br,[17,30,13,14,19,19,18,20,22],numcols=(4,5,6,7,8))
cnt=[[x['model'],int(x['horizon_ms']),int(x['plateaus']),int(x['plateaus_improved']),int(x['plateaus_worsened']),float(x['fraction_improved'])] for x in counts]
s=sheet('Plateau Summary','250 MS PLATEAU-LEVEL AUDIT','Plateau comparisons are descriptive within one continuous physical recording.',
 ['Model','Horizon (ms)','N plateaus','Improved plateaus','Worsened plateaus','Improved fraction'],cnt,[29,17,18,21,22,20]);s.get_range('F5:F7').set_number_format('0.0%')
pairs=[[x['model'],int(x['plateau_id']),int(x['fold']),int(x['windows']),float(x['position_rmse_mm']),float(x['mean_sq_error_mm2'])] for x in plateau]
sheet('Plateau Detail','PER-PLATEAU POSITION ERRORS','Auditable 250ms errors across 281 measured command plateaus, four models.',
 ['Model','Plateau ID','Fold','Prediction windows','RMSE (mm)','Mean square error (mm²)'],pairs,[28,19,12,22,20,25],numcols=(4,5))
quality=[
 ['Original source DOI','10.18419/DARUS-5799','Measured robot poses and logged commands'],
 ['Original ZIP SHA-256',proto['original_zip_sha256'],'User-supplied original archive, not redistributed'],
 ['Raw internal path',proto['original_raw'],'Raw measured data; model-generated derivative files excluded'],
 ['Total measured samples',proto['n_samples'],'Nominal 5ms data, measured nonuniform timestamps'],
 ['Logged command plateaus',proto['n_plateaus'],'Approximately 1-second command segments, one recording'],
 ['Nonpositive time increments',proto['bad_timestamp_nonpositive'],'These mark sample-time irregularity in source'],
 ['Severe acquisition gap/rewind intervals',proto['bad_time_intervals'],'Rejection mask prevents forecasts crossing severe logging discontinuities'],
 ['Sequence discontinuities',proto['bad_sequence_discontinuities'],'Large sequence counter discontinuities, included in rejection mask'],
 ['Prediction protocol','Command held at forecast issuance value','Unknown future commands NOT read during prediction'],
 ['Model fitting','Only historical validation block for each fold','Earlier test fold can become later validation in sequential walk-forward research'],
 ['Causal inputs','Measured pose at issuance + present/past logged commands','Never uses true future poses or future command inputs in prediction'],
 ['Model caveat','Historic lag not physically measured','Cannot estimate actuator delay without synchronized application timestamps'],
 ['Statistical caveat','All folds from one recording','Cross-fold consistency does not imply multi-robot generalization'],
 ['Study caveat','Same dataset was explored in Stages 11-17','These folds are retrospective robustness analyses, not pristine independent confirmation'],
 ['Docking performance','Not measured','Dataset does not validate final docking-stop reliability'],
 ['Next stage','Stage 19 uncertainty calibration','One-step coverage and interval width; handle temporal dependence'],
]
s=sheet('Provenance','PROVENANCE | VALIDITY & NEXT GATE','Research limitations explicitly stated; no author correspondence required.',
 ['Audit item','Recorded value','Interpretation'],quality,[35,72,84]);s.get_range('A5:C20').format.row_height=42;s.get_range('A5:C20').format.wrap_text=True
print(w.inspect({'kind':'table','range':'Horizon Summary!A4:K7','include':'values,formulas','table_max_rows':5,'table_max_cols':11}).ndjson[:2500]);print(w.inspect({'kind':'match','search_term':'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A','options':{'use_regex':True,'max_results':30}}).ndjson[:1300]);path=D/'AGV_Track2_Stage18_Rolling_Validation_Results.xlsx';SpreadsheetFile.export_xlsx(w).save(str(path));print('EXPORTED',path,path.stat().st_size)
