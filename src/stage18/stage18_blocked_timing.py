#!/usr/bin/env python3
"""Stage18 rolling-origin within-one-recording timing sensitivity.
Measured input: DOI 10.18419/DARUS-5799. No physical actuator latency claimed.
Each fold uses validation block immediately preceding chronologically later evaluation;
no model is selected using that fold's test errors. Historical command only.
"""
import numpy as np,zipfile,csv,json,hashlib,os
from pathlib import Path
from scipy.signal import lfilter
ROOT=Path(__file__).resolve().parent
ZIP=Path(os.environ.get('STUTTGART_ZIP','/mnt/data/doi-10.18419-darus-5799.zip'))
with zipfile.ZipFile(ZIP) as z:raw=np.loadtxt(z.open('sampled_data/arbitrary_inputs/raw_data.txt'),skiprows=2)
t=raw[:,0];seq=raw[:,1];pose=raw[:,2:5];cmd=raw[:,5:7];n=len(raw)
DT=.005;HS=(.1,.25,.5)
change=np.r_[False,np.any(np.abs(np.diff(cmd,axis=0))>1e-4,axis=1)]
seg=np.cumsum(change);NSEG=int(seg[-1])+1
# bad interval: nonmonotonic timestamp, anomalous outlying interval, dropped/rewound acquisition chunk.
dt=np.diff(t);dq=np.diff(seq)
bad=(dt<=0)|(dt>.02)|(dq>20)|(dq<-20)
prefix=np.r_[0,np.cumsum(bad,dtype=int)]
lastchange=np.maximum.accumulate(np.where(change,np.arange(n),-100000))
TAUS=[.025,.05,.08,.12,.18,.28];LAGS=[0,5,10,15]
# rolling splits test disjoint 50-60,60-70,...90-100% of plateau ids
FOLDS=[(x-10,x,x+10) for x in (50,60,70,80,90)]

def wrap(a):return (a+np.pi)%(2*np.pi)-np.pi

def ids_between(lo_pct,hi_pct):
    lo=int(np.searchsorted(seg,int(NSEG*lo_pct/100)))
    hi=(n if hi_pct==100 else int(np.searchsorted(seg,int(NSEG*hi_pct/100))))
    # >1-second embargo around both boundaries, >=0.5s target inside partition
    lo+=200;hi-=201
    ix=np.arange(lo,max(lo,hi),20,dtype=int)
    return {h: ix[(ix+int(h/DT)<n)&(prefix[ix+int(h/DT)]==prefix[ix]) &
                   (np.abs(t[np.minimum(ix+int(h/DT),n-1)]-t[ix]-h)<max(.014,.06*h)) &
                   (np.abs(pose[np.minimum(ix+int(h/DT),n-1),2]-pose[ix,2])<30)] for h in HS}

def latent(tau,lag):
    a=np.exp(-DT/tau)
    x=cmd[np.maximum(np.arange(n)-lag,0)]
    # Initialize with prehistory at first recorded command; zero warm-start edge negligible after 40% timeline
    s=lfilter([1-a],[1,-a],x,axis=0,zi=np.tile(x[0][None,:],(1,1))*a)[0]
    return s,a

CACHE={(tau,d):latent(tau,d) for tau in TAUS for d in LAGS}

def predict(ix,h,variant,par=None):
    if len(ix)==0:return np.zeros((0,3))
    theta=pose[ix,2].copy()
    if variant=='command_only':
        v,w=cmd[ix].T; q=w*h; distance=v*h*np.sinc(q/(2*np.pi))
        return np.column_stack([pose[ix,0]+distance*np.cos(theta+q/2),pose[ix,1]+distance*np.sin(theta+q/2),theta+q])
    tau,d=par;latent_arr,a=CACHE[par]
    cur=pose[ix].copy();s=latent_arr[ix].copy()
    for j in range(round(h/DT)):
        # Delayed logged command is retrieved only from <=forecast issue index.
        ref=cmd[np.minimum(ix+j-d,ix).clip(min=0)]
        sn=a*s+(1-a)*ref
        v,w=((s+sn)*0.5).T
        q=w*DT;distance=v*DT*np.sinc(q/(2*np.pi))
        cur[:,0]+=distance*np.cos(theta+q/2)
        cur[:,1]+=distance*np.sin(theta+q/2)
        theta+=q;s=sn
    cur[:,2]=theta
    return cur

def errs(pred,ix,h):
    actual=pose[ix+round(h/DT)]
    return (np.hypot(pred[:,0]-actual[:,0],pred[:,1]-actual[:,1])*1000,
        np.abs(wrap(pred[:,2]-actual[:,2]))*180/np.pi)

def evaluation(ix,h,kind,param):
    if kind=='ensemble':
        # Precommitted three-lag average; no learned test weights or future commands
        pred=sum(predict(ix,h,'filter',(param,lag)) for lag in (0,5,10))/3
        # Heading angles in these trajectories are near each other; wrapped angular average check
    elif kind=='command_only':pred=predict(ix,h,'command_only')
    else:pred=predict(ix,h,'filter',param)
    return errs(pred,ix,h)

def rmse(x):return float(np.sqrt(np.mean(x*x))) if len(x) else float('nan')

def writer(name,rows):
    if not rows:return
    with (ROOT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

fold_rows=[];case_rows=[];selection=[];strata=[]
for fold,(valbegin,valend,testend) in enumerate(FOLDS,1):
    valids=ids_between(valbegin,valend)
    tests=ids_between(valend,testend)
    vix=valids[.25]
    # rank all 24 only on preceding validation block at 250ms
    grid=[]
    for tau in TAUS:
      for lag in LAGS:
        p,h=evaluation(vix,.25,'filter',(tau,lag));grid.append((rmse(p),tau,lag))
    grid.sort()
    nooffset=min((z for z in grid if z[2]==0),key=lambda z:z[0])
    anyoffset=grid[0]
    # simple timing ensemble uses same tau as no-offset, lag support fixed ex ante
    params={'command_only':None,'causal_zero_offset':(nooffset[1],0),'lag_selection':(anyoffset[1],anyoffset[2]),'timing_ensemble':nooffset[1]}
    print(f'fold {fold} validation={valbegin}-{valend}% test={valend}-{testend}% counts={[len(tests[h]) for h in HS]} zero={nooffset} any={anyoffset}',flush=True)
    for kind,param in params.items():
      selection.append(dict(fold=fold,model=kind,validation_start_pct=valbegin,validation_end_pct=valend,test_end_pct=testend,tau_s=(param[0] if isinstance(param,tuple) else param),historical_offset_ms=(param[1]*5 if isinstance(param,tuple) else None),validation_250mm_rmse=(nooffset[0] if kind in ('causal_zero_offset','timing_ensemble') else anyoffset[0] if kind=='lag_selection' else None)))
      for h in HS:
        ix=tests[h];pe,he=evaluation(ix,h,'command_only' if kind=='command_only' else 'ensemble' if kind=='timing_ensemble' else 'filter',param)
        fold_rows.append(dict(fold=fold,validation=f'{valbegin}-{valend}%',test=f'{valend}-{testend}%',model=kind,horizon_ms=int(h*1000),windows=len(ix),plateaus=len(np.unique(seg[ix])),position_rmse_mm=rmse(pe),heading_rmse_deg=rmse(he),position_p90_mm=float(np.quantile(pe,.9))))
        changed_after=(ix-lastchange[ix])*DT<=.15
        future_change=seg[ix]!=seg[ix+round(h/DT)]
        for label,condition in [('recent_change',changed_after),('settled',~changed_after),('future_change',future_change),('future_constant',~future_change)]:
          x=pe[condition];y=he[condition]
          if len(x):strata.append(dict(fold=fold,model=kind,horizon_ms=int(h*1000),stratum=label,windows=len(x),position_rmse_mm=rmse(x),heading_rmse_deg=rmse(y)))
        for j,k in enumerate(ix):case_rows.append(dict(fold=fold,model=kind,horizon_ms=int(h*1000),row=int(k),plateau_id=int(seg[k]),time_s=float(t[k]),recent_change=int(changed_after[j]),future_change=int(future_change[j]),position_error_mm=float(pe[j]),heading_error_deg=float(he[j])))

writer('stage18_fold_results.csv',fold_rows)
writer('stage18_cases.csv',case_rows)
writer('stage18_strata.csv',strata)
writer('stage18_selected_models.csv',selection)
# Complete fold-case pooled, summaries, plateau bootstrap (description only, not independent replicate CI)
summary=[];plateau=[]
for model in ('command_only','causal_zero_offset','lag_selection','timing_ensemble'):
 for h in (100,250,500):
  rs=[x for x in case_rows if x['model']==model and x['horizon_ms']==h]
  pe=np.array([x['position_error_mm'] for x in rs]);he=np.array([x['heading_error_deg'] for x in rs])
  summary.append(dict(model=model,horizon_ms=h,windows=len(rs),plateaus=len(set(x['plateau_id'] for x in rs)),position_rmse_mm=rmse(pe),heading_rmse_deg=rmse(he),position_p90_mm=float(np.quantile(pe,.9))))
  if h==250:
    for z in sorted(set(x['plateau_id'] for x in rs)):
      pr=[x for x in rs if x['plateau_id']==z]
      pp=np.array([x['position_error_mm'] for x in pr]);
      plateau.append(dict(model=model,plateau_id=z,fold=pr[0]['fold'],windows=len(pr),position_rmse_mm=rmse(pp),mean_sq_error_mm2=float(np.mean(pp*pp))))
writer('stage18_pooled_summary.csv',summary)
writer('stage18_plateau_stats.csv',plateau)
# Paired pointwise differences and description in contiguous (20-plateau) time blocks
blocks=[]
for h in (100,250,500):
 baseline={(r['fold'],r['row']):r['position_error_mm'] for r in case_rows if r['model']=='command_only' and r['horizon_ms']==h}
 for model in ('causal_zero_offset','lag_selection','timing_ensemble'):
  subset=[r for r in case_rows if r['model']==model and r['horizon_ms']==h]
  bb=np.array([baseline[r['fold'],r['row']] for r in subset]);mm=np.array([r['position_error_mm'] for r in subset]);groups=np.array([r['plateau_id']//20 for r in subset]);
  for group in sorted(set(groups)):
    mask=groups==group
    blocks.append(dict(horizon_ms=h,model=model,time_block_id=int(group),windows=int(sum(mask)),command_only_rmse_mm=rmse(bb[mask]),model_rmse_mm=rmse(mm[mask]),gain_mm=rmse(bb[mask])-rmse(mm[mask])))
writer('stage18_time_blocks.csv',blocks)
meta=dict(original_zip_sha256=hashlib.sha256(ZIP.read_bytes()).hexdigest(),original_raw='sampled_data/arbitrary_inputs/raw_data.txt',n_samples=n,n_plateaus=NSEG,bad_time_intervals=int(sum(bad)),bad_timestamp_nonpositive=int(sum(dt<=0)),bad_sequence_discontinuities=int(sum((dq>20)|(dq<-20))),method='rolling-origin validation and disjoint chronological tests from one recording; 1 s embargo each boundary; future commands held at issue-time command; nominal 5-ms integrator',validation_test_pct=FOLDS,horizon_s=HS,taus=TAUS,logged_offsets_ms=[int(x*5) for x in LAGS],models=['command_only','causal_zero_offset','lag_selection','timing_ensemble'],caveats=['single physical recording, not independent run replicates','command application timestamps unknown','lag parameter is a logged-command history offset only','timestamp anomalies and nominal 5ms integration','no real docking-policy validation','retroactive exploration of previously analyzed source dataset'])
(ROOT/'stage18_protocol.json').write_text(json.dumps(meta,indent=2))
print('POOLED:');[print(x) for x in summary];print('DONE',len(case_rows),'records',flush=True)
