#!/usr/bin/env python3
import numpy as np,csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent

def get(name):
 with (D/name).open() as f:return list(csv.DictReader(f))
rows=get('stage18_cases.csv');summary=get('stage18_pooled_summary.csv');f=get('stage18_fold_results.csv')
models=['command_only','causal_zero_offset','lag_selection','timing_ensemble']
# pooled strata with consistent exact case-level aggregation
sub=[]
for h in (100,250,500):
 for mod in models:
  for label,key,target in [('recent_change','recent_change','1'),('settled','recent_change','0'),('future_change','future_change','1'),('future_constant','future_change','0')]:
   q=[x for x in rows if x['model']==mod and int(x['horizon_ms'])==h and x[key]==target]
   pe=np.array([float(x['position_error_mm']) for x in q]);he=np.array([float(x['heading_error_deg']) for x in q]);
   sub.append(dict(model=mod,horizon_ms=h,stratum=label,windows=len(q),position_rmse_mm=float(np.sqrt(np.mean(pe**2))),heading_rmse_deg=float(np.sqrt(np.mean(he**2)))))
with (D/'stage18_pooled_strata.csv').open('w',newline='') as o:
 w=csv.DictWriter(o,fieldnames=list(sub[0]));w.writeheader();w.writerows(sub)
# blocked descriptive bootstrap 20 sequential plateaus per group, raw sum of squared residuals
rng=np.random.default_rng(18017)
boot=[]
for h in (100,250,500):
 a=[x for x in rows if x['horizon_ms']==str(h) and x['model']=='command_only']
 base={(int(x['fold']),int(x['row'])):float(x['position_error_mm'])**2 for x in a}
 for mod in models[1:]:
  b=[x for x in rows if x['horizon_ms']==str(h) and x['model']==mod]
  blocks={}
  for x in b:
   k=(int(x['fold']),int(x['row']));g=int(x['plateau_id'])//20
   if g not in blocks:blocks[g]=[0.,0.,0]
   blocks[g][0]+=base[k];blocks[g][1]+=float(x['position_error_mm'])**2;blocks[g][2]+=1
  block=np.array(list(blocks.values()),float)
  estimates=[]
  for i in range(4000):
   s=block[rng.integers(0,len(block),len(block))].sum(axis=0)
   estimates.append(np.sqrt(s[0]/s[2])-np.sqrt(s[1]/s[2]))
  actual=block.sum(axis=0)
  boot.append(dict(horizon_ms=h,model=mod,blocks=len(block),windows=int(actual[2]),baseline_rmse_mm=float(np.sqrt(actual[0]/actual[2])),model_rmse_mm=float(np.sqrt(actual[1]/actual[2])),gain_mm=float(np.sqrt(actual[0]/actual[2])-np.sqrt(actual[1]/actual[2])),resample_2p5_mm=float(np.quantile(estimates,.025)),resample_97p5_mm=float(np.quantile(estimates,.975)),fraction_positive=float(np.mean(np.array(estimates)>0)),note='descriptive resampling of contiguous ~20-command-plateau blocks from one robot recording; NOT a confidence interval for new robots'))
with (D/'stage18_block_resampling.csv').open('w',newline='') as o:
 w=csv.DictWriter(o,fieldnames=list(boot[0]));w.writeheader();w.writerows(boot)

# Count plateaus improved 250ms and fold improvement percentages
p=[]
for mod in models[1:]:
 base={ (int(x['fold']),int(x['row'])):float(x['position_error_mm'])**2 for x in rows if x['model']=='command_only' and x['horizon_ms']=='250'}
 groups={}
 for x in rows:
  if x['model']==mod and x['horizon_ms']=='250':
   g=int(x['plateau_id']);key=(int(x['fold']),int(x['row']));
   if g not in groups:groups[g]=[0,0,0]
   groups[g][0]+=base[key];groups[g][1]+=float(x['position_error_mm'])**2;groups[g][2]+=1
 better=sum(v[1]<v[0] for v in groups.values());p.append(dict(model=mod,horizon_ms=250,plateaus=len(groups),plateaus_improved=better,plateaus_worsened=len(groups)-better,fraction_improved=better/len(groups)))
with (D/'stage18_plateau_improvement_counts.csv').open('w',newline='') as o:
 w=csv.DictWriter(o,fieldnames=list(p[0]));w.writeheader();w.writerows(p)

font={'size':12};plt.rcParams.update({'font.size':12,'axes.titlesize':15,'axes.labelsize':12,'xtick.labelsize':10,'ytick.labelsize':11,'legend.fontsize':10})
fig,ax=plt.subplots(figsize=(10.5,6))
hs=np.array([100,250,500]);offsets=np.arange(4)*.17-.255
for j,m in enumerate(models):
 vals=[next(float(x['position_rmse_mm']) for x in summary if x['model']==m and int(x['horizon_ms'])==h) for h in hs]
 ax.bar(np.arange(3)+offsets[j],vals,width=.17,label={'command_only':'Command-only','causal_zero_offset':'Causal filter (0 ms)','lag_selection':'Validation-selected lag','timing_ensemble':'Timing ensemble'}[m]);
ax.set_xticks(np.arange(3));ax.set_xticklabels([f'{h} ms' for h in hs]);ax.set_xlabel('Forecast horizon');ax.set_ylabel('Position RMSE (mm)');ax.set_title('Measured motion prediction: rolling chronological evaluation');ax.grid(axis='y',alpha=.2);ax.legend(ncol=2,loc='upper left',frameon=False);fig.tight_layout();fig.savefig(D/'stage18_horizon_comparison.png',dpi=200);plt.close(fig)
fig,ax=plt.subplots(figsize=(10.5,5.5))
for m in ('command_only','causal_zero_offset','lag_selection','timing_ensemble'):
 vals=[float(next(x['position_rmse_mm'] for x in f if x['model']==m and int(x['horizon_ms'])==250 and int(x['fold'])==i)) for i in range(1,6)]
 ax.plot(range(1,6),vals,'o-',linewidth=2,label={'command_only':'Command-only','causal_zero_offset':'Causal filter (0 ms)','lag_selection':'Validation-selected lag','timing_ensemble':'Timing ensemble'}[m])
ax.set_xticks(range(1,6));ax.set_xlabel('Rolling-origin test block');ax.set_ylabel('Position RMSE at 250 ms (mm)');ax.set_title('Five chronologically ordered evaluation blocks');ax.grid(alpha=.2);ax.legend(frameon=False);fig.tight_layout();fig.savefig(D/'stage18_fold_consistency.png',dpi=200);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5.5))
labels=['Recent change','Settled','Future command change','No future change'];keys=['recent_change','settled','future_change','future_constant']
x=np.arange(len(labels));width=.22
for j,m in enumerate(('command_only','causal_zero_offset','lag_selection')):
 vals=[next(float(t['position_rmse_mm']) for t in sub if t['model']==m and t['horizon_ms']==250 and t['stratum']==k) for k in keys]
 ax.bar(x+(j-1)*width,vals,width=width,label={'command_only':'Command-only','causal_zero_offset':'Causal filter','lag_selection':'Selected history lag'}[m])
ax.set_xticks(x);ax.set_xticklabels(labels,rotation=8);ax.set_ylabel('Position RMSE at 250 ms (mm)');ax.set_title('Retrospective command-transition stress assessment');ax.grid(axis='y',alpha=.2);ax.legend(frameon=False);fig.tight_layout();fig.savefig(D/'stage18_transition_dependence.png',dpi=200);plt.close(fig)
print('BOOT');[print(x) for x in boot if x['model']=='causal_zero_offset'];print('PLATEAU',p);print('STRATA');[print(x) for x in sub if x['horizon_ms']==250 and x['model'] in ('command_only','causal_zero_offset')]
