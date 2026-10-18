import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).parent

def load(name):return list(csv.DictReader(open(P/name)))
rows=load('stage19_pooled_summary.csv')
co=[r for r in rows if r['model']=='causal_zero_offset']
horiz=[100,250,500]
fig,ax=plt.subplots(figsize=(10,6))
x=np.arange(3);width=.32
for off,method,label in [(-width/2,'pooled','Pooled calibration'),(width/2,'regime_stratified','Command-regime calibration')]:
 vals=[100*float(next(r for r in co if int(r['horizon_ms'])==h and r['method']==method)['position_90_coverage']) for h in horiz]
 bars=ax.bar(x+off,vals,width,label=label)
 for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v+1,f'{v:.1f}%',ha='center',fontsize=10)
ax.axhline(90,color='black',linestyle='--',label='Nominal 90% target')
ax.set_xticks(x,[f'{h} ms' for h in horiz]);ax.set_ylabel('Out-of-time position coverage (%)');ax.set_ylim(0,108)
ax.set_title('Stage 19: empirical calibration coverage on later time blocks');ax.legend(loc='lower right')
fig.tight_layout();fig.savefig(P/'stage19_position_coverage.png',dpi=200);plt.close(fig)

fig,ax=plt.subplots(figsize=(10,6));ff=load('stage19_fold_results.csv')
for mode,mark in [('pooled','o'),('regime_stratified','s')]:
 z=sorted([r for r in ff if r['model']=='causal_zero_offset' and r['horizon_ms']=='250' and r['method']==mode],key=lambda r:int(r['fold']))
 ax.plot([int(r['fold']) for r in z],[100*float(r['position_90_coverage']) for r in z],marker=mark,linewidth=2,label=mode.replace('_',' ').title())
ax.axhline(90,color='black',linestyle='--',label='Nominal 90% target')
ax.set_xticks([1,2,3,4],['60–70%','70–80%','80–90%','90–100%']);ax.set_ylim(0,110)
ax.set_xlabel('Chronological evaluation block of robot recording');ax.set_ylabel('Position coverage (%)')
ax.set_title('Stage 19: coverage instability across chronological blocks (250 ms)')
ax.legend();fig.tight_layout();fig.savefig(P/'stage19_fold_drift.png',dpi=200);plt.close(fig)

fig,ax=plt.subplots(figsize=(10,6));sst=load('stage19_pooled_strata.csv')
items=['recent_change','settled','future_change_posthoc','no_future_change_posthoc']
vals=[100*float(next(r for r in sst if r['model']=='causal_zero_offset' and r['horizon_ms']=='250' and r['method']=='pooled' and r['stratum']==g)['position_coverage']) for g in items]
labels=['Recent logged change','Settled commands','Future change (audit only)','No future change']
bars=ax.barh(labels,vals)
for b,v in zip(bars,vals):ax.text(min(v+1,98),b.get_y()+b.get_height()/2,f'{v:.1f}%',va='center',fontsize=10)
ax.axvline(90,color='black',linestyle='--',label='Nominal 90% target')
ax.set_xlim(0,110);ax.set_xlabel('Position coverage (%)');ax.set_title('Stage 19: condition-dependent calibration failures (250 ms)');ax.invert_yaxis();ax.legend(loc='lower right');fig.tight_layout();fig.savefig(P/'stage19_transition_coverage.png',dpi=200);plt.close(fig)
print('created charts')
