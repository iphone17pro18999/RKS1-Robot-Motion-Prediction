#!/usr/bin/env python3
"""Build Stage 19 workbook using artifact_tool (only spreadsheet editing library)."""
import csv, json
from pathlib import Path
from artifact_tool import Workbook, SpreadsheetFile
P=Path(__file__).resolve().parent
O=P/'AGV_Track2_Stage19_Prediction_Uncertainty.xlsx'

def read(name):return list(csv.DictReader((P/name).open()))
summary=read('stage19_pooled_summary.csv');folds=read('stage19_fold_results.csv')
strata=read('stage19_pooled_strata.csv');qrows=read('stage19_quantiles.csv');reg=read('stage19_strata.csv');cases=read('stage19_case_records.csv')
wb=Workbook.create()
NAVY='#17324D';TEAL='#007F86';WHITE='#FFFFFF';LIGHT='#F3F6FA';MUTED='#536271'
def xl_col(num):
 s=''
 while num>0:num,r=divmod(num-1,26);s=chr(65+r)+s
 return s

def base_sheet(name,title,headers,records,widths=None):
 s=wb.worksheets.add(name);cols=len(headers);last=xl_col(cols)
 s.merge_cells(f'A1:{last}1')
 s.get_range('A1').values=[[title]]
 s.get_range(f'A1:{last}1').format={'fill':NAVY,'font':{'bold':True,'color':WHITE,'size':14},'row_height':31,'vertical_alignment':'center'}
 s.get_range(f'A3:{last}3').values=[headers]
 s.get_range(f'A3:{last}3').format={'fill':TEAL,'font':{'bold':True,'color':WHITE,'size':10},'row_height':26,'wrap_text':True,'vertical_alignment':'center'}
 if records:
  s.get_range_by_indexes(3,0,len(records),cols).values=records
  s.get_range_by_indexes(3,0,len(records),cols).format.row_height=19
 for i in range(cols):s.get_range(f'{xl_col(i+1)}:{xl_col(i+1)}').format.column_width=(widths[i] if widths else 17)
 s.freeze_panes.freeze_rows(3)
 return s

def val(x,typ='f'):
 if typ=='i':return int(x)
 if typ=='f':return float(x)
 return x

# Scorecard formula driven: denominator/numerators in input cells, computed coverage and gaps via spreadsheet formulas.
s=wb.worksheets.add('Dashboard')
s.merge_cells('A1:N1');s.get_range('A1').values=[['Stage 19 — Chronological Prediction-Interval Reliability']]
s.get_range('A1:N1').format={'fill':NAVY,'font':{'bold':True,'color':WHITE,'size':15},'row_height':33}
s.get_range('A2:D2').values=[['Target marginal coverage',.9,'Target joint coverage',.9]]
s.get_range('B2').set_number_format('0.0%');s.get_range('D2').set_number_format('0.0%')
s.get_range('A2:D2').format.row_height=23
headers=['Model','Horizon ms','Method','Test windows','Position covered','Position coverage','Heading covered','Heading coverage','Joint covered','Joint coverage','Mean pos. q90 (mm)','Mean heading q90 (°)','Mean pos. q95 (mm)','Pos. gap (pp)']
s.get_range('A4:N4').values=[headers]
s.get_range('A4:N4').format={'fill':TEAL,'font':{'bold':True,'color':WHITE,'size':10},'row_height':32,'wrap_text':True,'vertical_alignment':'center'}
data=[]
for r in summary:
 n=int(r['n']);cp=round(n*float(r['position_90_coverage']));ch=round(n*float(r['heading_90_coverage']));cj=round(n*float(r['joint_95_95_coverage']))
 data.append([r['model'].replace('_',' '),int(r['horizon_ms']),r['method'].replace('_',' '),n,cp,None,ch,None,cj,None,float(r['mean_position_q90_mm']),float(r['mean_heading_q90_deg']),float(r['mean_position_q95_mm']),None])
s.get_range('A5:N16').values=data
for idx in range(5,17):
 s.get_range(f'F{idx}').formulas=[[f'=E{idx}/D{idx}']]
 s.get_range(f'H{idx}').formulas=[[f'=G{idx}/D{idx}']]
 s.get_range(f'J{idx}').formulas=[[f'=I{idx}/D{idx}']]
 s.get_range(f'N{idx}').formulas=[[f'=(F{idx}-$B$2)*100']]
s.get_range('F5:F16').set_number_format('0.0%');s.get_range('H5:H16').set_number_format('0.0%');s.get_range('J5:J16').set_number_format('0.0%')
s.get_range('K5:N16').set_number_format('0.00')
for i,wi in enumerate([24,13,21,16,18,17,17,17,15,17,20,20,19,16],1):s.get_range(f'{xl_col(i)}:{xl_col(i)}').format.column_width=wi
s.get_range('A19:N19').values=[['Interpretation','Marginal 90% target','Observed coverage from later blocks','Not an exchangeable-time conformal guarantee','Two marginal 95% bounds provide a nominal joint 90% benchmark','','','','','','','','','']]
s.get_range('A19:N19').format={'fill':LIGHT,'wrap_text':True,'row_height':36}
s.get_range('A21:N21').values=[['Important caveat','One physical recording; temporally correlated windows','Fold-2 thresholds are oversized after a difficult previous block','Retrospective study using a dataset examined in earlier stages','No AGV docking safety claim','','','','','','','','','']]
s.get_range('A21:N21').format={'fill':LIGHT,'wrap_text':True,'row_height':40}
s.freeze_panes.freeze_rows(4)

fold_headers=['Fold','Model','Horizon (ms)','Calibration method','Calibration period','Evaluation period','Calibration windows','Test windows','Pos. RMSE mm','Head. RMSE °','Pos. coverage 90','Heading coverage 90','Joint coverage 95/95','Pos q90 mm','Head q90 °','Pos q95 mm','Head q95 °','Recent windows','Future-change audit windows']
fr=[]
for r in folds:
 fr.append([int(r['fold']),r['model'],int(r['horizon_ms']),r['method'],r['calibration_block'],r['evaluation_block'],int(r['n_cal']),int(r['n_test']),float(r['test_position_rmse_mm']),float(r['test_heading_rmse_deg']),float(r['position_90_coverage']),float(r['heading_90_coverage']),float(r['joint_95_95_coverage']),float(r['mean_position_q90_mm']),float(r['mean_heading_q90_deg']),float(r['mean_position_q95_mm']),float(r['mean_heading_q95_deg']),int(r['recent_windows']),int(r['future_change_windows'])])
f=base_sheet('Rolling Folds','Chronological calibration → later evaluation',fold_headers,fr,[10,24,14,22,21,21,18,14,17,17,17,17,20,17,17,17,17,16,21]);f.get_range(f'K4:M{len(fr)+3}').set_number_format('0.0%')

strh=['Model','Horizon ms','Method','Condition','Test windows','Position coverage','Heading coverage','Joint coverage','Mean q90 pos (mm)','Mean q95 pos (mm)']
sr=[[r['model'],int(r['horizon_ms']),r['method'],r['stratum'],int(r['n']),float(r['position_coverage']),float(r['heading_coverage']),float(r['joint_coverage']),float(r['mean_position_q90_mm']),float(r['mean_position_q95_mm'])] for r in strata]
s2=base_sheet('Condition Summary','Condition-specific coverage (future changes audit-only)',strh,sr,[24,15,23,30,16,19,19,19,21,21]);s2.get_range(f'F4:H{len(sr)+3}').set_number_format('0.0%')

qh=['Fold','Model','Horizon ms','Method','Group','Raw calibration n','Bound calibration n','Pooled fallback','Evaluation n','Position q90 mm','Heading q90 °','Position q95 mm','Heading q95 °','Tau s']
qr=[[int(r['fold']),r['model'],int(r['horizon_ms']),r['method'],r['stratum'],int(r['calibration_windows']),int(r['bound_calibration_windows']),int(r['pooled_fallback']),int(r['evaluation_windows']),float(r['position_q90_mm']),float(r['heading_q90_deg']),float(r['position_q95_mm']),float(r['heading_q95_deg']),float(r['tau_s']) if r['tau_s'] else None] for r in qrows]
base_sheet('Calibration Thresholds','Frozen calibration radii and sparse-stratum fallbacks',qh,qr,[10,23,15,22,21,19,22,18,18,20,20,20,20,12])

rrh=['Fold','Model','Horizon ms','Method','Evaluation condition','Windows','Position coverage','Heading coverage','Joint coverage','Mean q90 (mm)','Mean q95 (mm)','Observed pos RMSE mm']
rr=[[int(r['fold']),r['model'],int(r['horizon_ms']),r['method'],r['stratum'],int(r['n']),float(r['position_coverage']),float(r['heading_coverage']),float(r['joint_coverage']),float(r['mean_position_q90_mm']),float(r['mean_position_q95_mm']),float(r['position_rmse_mm'])] for r in reg]
s3=base_sheet('Condition by Fold','Coverage within each later evaluation block',rrh,rr,[10,24,15,24,31,14,19,19,19,19,19,24]);s3.get_range(f'G4:I{len(rr)+3}').set_number_format('0.0%')

# The full 20,200 case records are preserved in the accompanying CSV and ZIP.
# Here sample systematically by source row order, retaining both models, all horizons and methods.
caseh=['Fold','Model','Horizon ms','Method','Source row','Plateau ID','Elapsed s','Recent command change','Future change (audit)','Position error mm','Heading error °','Position q90 mm','Heading q90 °','Position covered','Heading covered','Joint covered']
sample=cases[::40]
cr=[[int(r['fold']),r['model'],int(r['horizon_ms']),r['method'],int(r['row']),int(r['plateau_id']),float(r['time_s']),int(r['recent_change']),int(r['future_change_posthoc']),float(r['position_error_mm']),float(r['heading_error_deg']),float(r['position_q90_mm']),float(r['heading_q90_deg']),int(r['position_covered']),int(r['heading_covered']),int(r['joint_covered'])] for r in sample]
base_sheet('Case Audit Sample','Systematic sample of full prediction-case audit (full CSV in ZIP)',caseh,cr,[10,23,15,22,16,15,17,20,21,19,17,19,17,19,19,17])

protocol=[
 ['Input provenance','University of Stuttgart DaRUS dataset, DOI 10.18419/DARUS-5799'],
 ['Data file','sampled_data/arbitrary_inputs/raw_data.txt from original ZIP'],
 ['Source size','Measured robot samples, one physical recording'],
 ['Model comparison','Command-only kinematics versus causal zero-offset exponential command-history filter'],
 ['Pre-selected tau','Stage 18 validation-selected tau for each fold, selected before Stage 19 calibration block'],
 ['Fold 1','fit 40–50% / calibrate 50–60% / evaluate 60–70% of command plateaus'],
 ['Fold 2','fit 50–60% / calibrate 60–70% / evaluate 70–80% of command plateaus'],
 ['Fold 3','fit 60–70% / calibrate 70–80% / evaluate 80–90% of command plateaus'],
 ['Fold 4','fit 70–80% / calibrate 80–90% / evaluate 90–100% of command plateaus'],
 ['Embargo','1-second exclusion at partition boundaries; tests check timestamp/sequence continuity'],
 ['Forecast policy','Only current/past logged commands; unobserved future commands held at issue-time command'],
 ['Quantile rank','ceil((n+1)*(1-alpha)) empirical error order statistic'],
 ['Marginal score','Absolute heading error in degrees; radial position error in millimeters'],
 ['Marginal alpha','0.10 each, nominal 90% position and 90% heading coverage'],
 ['Joint alpha','0.05 for each component, nominal 90% position AND heading, by union bound under required assumptions'],
 ['Conditional groups','Command changed within preceding 150 ms versus settled commands'],
 ['Sparse stratum','If <30 calibration windows, use pooled calibration threshold (flag in threshold sheet)'],
 ['Future change','Recorded for post-hoc diagnostic only; never used to select bounds or forecast values'],
 ['Inference constraint','Chronological blocks from a dependent drifting recording do not satisfy exchangeability; finite-sample conformal guarantee cannot be claimed'],
 ['Research conduct','Earlier stages already examined source recording; evaluation is retrospective, not an untouched independent dataset'],
 ['Interpretation','Pose-prediction error bounds only; not experimentally validated docking or collision safety']]
ps=base_sheet('Protocol','Research design and operational definitions',['Item','Protocol specification'],protocol,[28,115]);ps.get_range(f'B4:B{len(protocol)+3}').format.wrap_text=True;ps.get_range(f'A4:B{len(protocol)+3}').format.row_height=30

limits=[
 ['Single robot and single continuous recording','Data from one physical device and trajectory sequence, not a multi-robot external replication.'],
 ['Strong temporal dependence','Overlapping forecast windows and nearby command plateaus are autocorrelated.'],
 ['Operating-regime shift','Error and required bound width changed considerably between consecutive evaluation blocks.'],
 ['Coverage not guaranteed','The conformal quantile formula is used diagnostically; classical finite-sample coverage assumptions are unmet.'],
 ['Unknown physical timing','Command application and motion-capture synchronization cannot be verified from the published records.'],
 ['Future commands unavailable','Unexpected later command changes worsen accuracy and cannot be used by online prediction.'],
 ['Retrospective protocol design','The same physical dataset has been studied in earlier stages; test is temporal, not pristine independent external.'],
 ['Sparse conditional samples','Some command-change groups have fewer than 30 calibration cases; fallback to pooled threshold.'],
 ['Prediction does not establish safety','A 90% prediction region would permit misses; neither collisions nor docking final-stop reliability were measured.'],
 ['No novel method established','Split residual calibration and exponential filtering are known techniques; research novelty needs stronger external evidence.']]
base_sheet('Limitations','Scientific limitations and interpretation safeguards',['Limitation','Impact on research claim'],limits,[37,107])

print('BUILT',len(summary),'dashboard rows',len(folds),'folds',len(qrows),'quantile groups',len(cases),'full cases')
print('inspect',wb.inspect({'kind':'table','range':'Dashboard!A4:J8','include':'values,formulas','table_max_rows':6,'table_max_cols':10}).ndjson[:1800])
try:
 chk=wb.inspect({'kind':'match','search_term':'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A','options':{'use_regex':True,'max_results':100}})
 print('error_scan',chk.ndjson[:900])
except Exception as e:print('error_scan_unavailable',e)
SpreadsheetFile.export_xlsx(wb).save(str(O))
print('saved',O,O.stat().st_size)
