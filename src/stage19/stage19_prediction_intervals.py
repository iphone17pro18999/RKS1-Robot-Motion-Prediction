#!/usr/bin/env python3
"""Stage 19: chronological residual calibration on one physically measured robot recording.
Commands at forecast issue-time or earlier only; no future command use in predictor.
Nominal 90% marginal / >=90% simultaneous thresholds, NOT guaranteed under dependence/drift.
Dataset: DOI 10.18419/DARUS-5799; Stage18 parameter-selection source used unchanged.
"""
import os, csv, json, math, zipfile, hashlib
from pathlib import Path
import numpy as np
from scipy.signal import lfilter

ROOT=Path(__file__).resolve().parent
ZIP=Path(os.environ.get('STUTTGART_ZIP','/mnt/data/doi-10.18419-darus-5799.zip'))
SEL=Path(os.environ.get('STAGE18_SELECTION',str(ROOT/'stage18_selected_models.csv' if (ROOT/'stage18_selected_models.csv').exists() else '/mnt/data/agv_stuttgart_stage18/stage18_selected_models.csv')))
with zipfile.ZipFile(ZIP) as z:
    raw=np.loadtxt(z.open('sampled_data/arbitrary_inputs/raw_data.txt'),skiprows=2)
t=raw[:,0]; seq=raw[:,1]; pose=raw[:,2:5]; cmd=raw[:,5:7]; n=len(raw)
dt_ref=.005; hs=(.10,.25,.50)
change=np.r_[False,np.any(np.abs(np.diff(cmd,axis=0))>1e-4,axis=1)]
seg=np.cumsum(change); nseg=int(seg[-1])+1
bad=(np.diff(t)<=0)|(np.diff(t)>.02)|(np.diff(seq)>20)|(np.diff(seq)<-20)
prefix=np.r_[0,np.cumsum(bad,dtype=int)]
lastchange=np.maximum.accumulate(np.where(change,np.arange(n),-100000))

rows=list(csv.DictReader(SEL.open()))
param_by_fold={int(r['fold']):float(r['tau_s']) for r in rows if r['model']=='causal_zero_offset'}
assert set(param_by_fold)>=set(range(1,5))

def ids_between(lo_pct,hi_pct,h):
    lo=int(np.searchsorted(seg,int(nseg*lo_pct/100)))+200
    hi=(n if hi_pct==100 else int(np.searchsorted(seg,int(nseg*hi_pct/100))))-201
    ix=np.arange(lo,max(lo,hi),20,dtype=int)
    k=int(round(h/dt_ref)); iy=ix+k
    valid=(iy<n)
    ix=ix[valid];iy=iy[valid]
    valid=(prefix[iy]==prefix[ix])&(np.abs(t[iy]-t[ix]-h)<max(.014,.06*h))&(np.abs(pose[iy,2]-pose[ix,2])<30)
    return ix[valid]

def wrap(x):return (x+np.pi)%(2*np.pi)-np.pi

def predict_command(ix,h):
    theta=pose[ix,2];v,w=cmd[ix].T;q=w*h;dist=v*h*np.sinc(q/(2*np.pi))
    return np.column_stack([pose[ix,0]+dist*np.cos(theta+q/2),pose[ix,1]+dist*np.sin(theta+q/2),theta+q])

cache={}
def predict_filter(ix,h,tau):
    if tau not in cache:
        a=np.exp(-dt_ref/tau)
        x=cmd
        state=lfilter([1-a],[1,-a],x,axis=0,zi=x[0][None,:]*a)[0]
        cache[tau]=(a,state)
    a,state=cache[tau]
    theta=pose[ix,2].copy();cur=pose[ix].copy();s=state[ix].copy()
    for j in range(round(h/dt_ref)):
        # Strictly causal: future commands replaced with command at issue time.
        ref=cmd[np.minimum(ix+j,ix)]
        sn=a*s+(1-a)*ref
        v,w=((s+sn)*.5).T
        q=w*dt_ref;dist=v*dt_ref*np.sinc(q/(2*np.pi))
        cur[:,0]+=dist*np.cos(theta+q/2)
        cur[:,1]+=dist*np.sin(theta+q/2)
        theta+=q;s=sn
    cur[:,2]=theta
    return cur

def errors(ix,h,model,tau):
    p=predict_command(ix,h) if model=='command_only' else predict_filter(ix,h,tau)
    actual=pose[ix+int(round(h/dt_ref))]
    return (1000*np.hypot(p[:,0]-actual[:,0],p[:,1]-actual[:,1]),
            (180/np.pi)*np.abs(wrap(p[:,2]-actual[:,2])))

def finite_sample_q(scores,alpha):
    a=np.sort(np.asarray(scores,dtype=float)); m=len(a)
    if m==0:return float('nan')
    rank=math.ceil((m+1)*(1-alpha))
    return float(a[rank-1]) if rank<=m else float('inf')

def wcsv(fname,lines):
    if not lines:return
    with (ROOT/fname).open('w',newline='') as f:
        w=csv.DictWriter(f,list(lines[0]));w.writeheader();w.writerows(lines)

cases=[];fresults=[]; strata=[];qrows=[]
for fold in (1,2,3,4):
    c_lo,c_hi=40+10*fold,50+10*fold
    e_lo,e_hi=c_hi,c_hi+10
    tau=param_by_fold[fold]
    for h in hs:
        calix=ids_between(c_lo,c_hi,h)
        testix=ids_between(e_lo,e_hi,h)
        assert len(calix)>100 and len(testix)>100 and calix.max()<testix.min()
        calmask=(calix-lastchange[calix])*dt_ref<=.15
        testmask=(testix-lastchange[testix])*dt_ref<=.15
        future_changes=(seg[testix]!=seg[testix+int(round(h/dt_ref))])
        for model in ('command_only','causal_zero_offset'):
            cp,ch=errors(calix,h,model,tau)
            tp,th=errors(testix,h,model,tau)
            for mode in ('pooled','regime_stratified'):
                radp=np.empty(len(testix));radh=np.empty(len(testix))
                radp95=np.empty(len(testix));radh95=np.empty(len(testix))
                for label,cm,tm in ([('all',np.ones(len(calix),bool),np.ones(len(testix),bool))] if mode=='pooled' else [('recent_change',calmask,testmask),('settled',~calmask,~testmask)]):
                    # Sparse stratum protection: use pooled residuals rather than unstable within-group q.
                    bound_cal_mask=cm if sum(cm)>=30 else np.ones(len(calix),dtype=bool)
                    fallback=int(sum(cm)<30)
                    qqp=finite_sample_q(cp[bound_cal_mask],.1);qqh=finite_sample_q(ch[bound_cal_mask],.1)
                    qp95=finite_sample_q(cp[bound_cal_mask],.05);qh95=finite_sample_q(ch[bound_cal_mask],.05)
                    radp[tm]=qqp;radh[tm]=qqh;radp95[tm]=qp95;radh95[tm]=qh95
                    qrows.append(dict(fold=fold,model=model,horizon_ms=int(h*1000),calibration=f'{c_lo}-{c_hi}%',evaluation=f'{e_lo}-{e_hi}%',method=mode,stratum=label,calibration_windows=int(sum(cm)),bound_calibration_windows=int(sum(bound_cal_mask)),pooled_fallback=fallback,evaluation_windows=int(sum(tm)),position_q90_mm=qqp,heading_q90_deg=qqh,position_q95_mm=qp95,heading_q95_deg=qh95,tau_s=(tau if model!='command_only' else '')))
                poscov=tp<=radp;hcov=th<=radh
                joint=(tp<=radp95)&(th<=radh95)
                # Each reported joint interval has calibrated marginal 95% radii.
                fresults.append(dict(fold=fold,model=model,horizon_ms=int(h*1000),method=mode,calibration_block=f'{c_lo}-{c_hi}%',evaluation_block=f'{e_lo}-{e_hi}%',n_cal=len(calix),n_test=len(testix),test_position_rmse_mm=float(np.sqrt(np.mean(tp*tp))),test_heading_rmse_deg=float(np.sqrt(np.mean(th*th))),position_90_coverage=float(np.mean(poscov)),heading_90_coverage=float(np.mean(hcov)),joint_95_95_coverage=float(np.mean(joint)),mean_position_q90_mm=float(np.mean(radp)),mean_heading_q90_deg=float(np.mean(radh)),mean_position_q95_mm=float(np.mean(radp95)),mean_heading_q95_deg=float(np.mean(radh95)),recent_windows=int(sum(testmask)),future_change_windows=int(sum(future_changes))))
                for label,mask in [('recent_change',testmask),('settled',~testmask),('future_change_posthoc',future_changes),('no_future_change_posthoc',~future_changes)]:
                    if mask.sum():
                        strata.append(dict(fold=fold,model=model,horizon_ms=int(h*1000),method=mode,stratum=label,n=int(mask.sum()),position_coverage=float(np.mean(poscov[mask])),heading_coverage=float(np.mean(hcov[mask])),joint_coverage=float(np.mean(joint[mask])),mean_position_q90_mm=float(np.mean(radp[mask])),mean_position_q95_mm=float(np.mean(radp95[mask])),position_rmse_mm=float(np.sqrt(np.mean(tp[mask]**2)))))
                for j,ix in enumerate(testix):
                    cases.append(dict(fold=fold,model=model,horizon_ms=int(h*1000),method=mode,row=int(ix),plateau_id=int(seg[ix]),time_s=float(t[ix]),recent_change=int(testmask[j]),future_change_posthoc=int(future_changes[j]),position_error_mm=float(tp[j]),heading_error_deg=float(th[j]),position_q90_mm=float(radp[j]),heading_q90_deg=float(radh[j]),position_q95_mm=float(radp95[j]),heading_q95_deg=float(radh95[j]),position_covered=int(poscov[j]),heading_covered=int(hcov[j]),joint_covered=int(joint[j])))
    print('stage19 finished fold',fold,'cal',c_lo,c_hi,'test',e_lo,e_hi,flush=True)
wcsv('stage19_fold_results.csv',fresults)
wcsv('stage19_strata.csv',strata)
wcsv('stage19_quantiles.csv',qrows)
wcsv('stage19_case_records.csv',cases)
# Pooled across 4 disjoint test blocks per method/model/horizon; records correlated within contiguous time.
summary=[];poolstr=[]
for model in ('command_only','causal_zero_offset'):
  for h in (100,250,500):
    for mode in ('pooled','regime_stratified'):
      r=[x for x in cases if x['model']==model and x['horizon_ms']==h and x['method']==mode]
      p=np.array([x['position_error_mm'] for x in r]);hh=np.array([x['heading_error_deg'] for x in r]);
      summary.append(dict(model=model,horizon_ms=h,method=mode,n=len(r),distinct_plateaus=len(set(x['plateau_id'] for x in r)),position_rmse_mm=float(np.sqrt(np.mean(p*p))),heading_rmse_deg=float(np.sqrt(np.mean(hh*hh))),position_90_coverage=float(np.mean([x['position_covered'] for x in r])),heading_90_coverage=float(np.mean([x['heading_covered'] for x in r])),joint_95_95_coverage=float(np.mean([x['joint_covered'] for x in r])),mean_position_q90_mm=float(np.mean([x['position_q90_mm'] for x in r])),mean_position_q95_mm=float(np.mean([x['position_q95_mm'] for x in r])),mean_heading_q90_deg=float(np.mean([x['heading_q90_deg'] for x in r])),mean_heading_q95_deg=float(np.mean([x['heading_q95_deg'] for x in r])),n_folds=4,folds_achieving_90_position=sum(x['position_90_coverage']>=.9 for x in fresults if x['model']==model and x['method']==mode and x['horizon_ms']==h)))
      for label in ('recent_change','settled','future_change_posthoc','no_future_change_posthoc'):
        rr=[x for x in r if (bool(x['recent_change']) if label=='recent_change' else not bool(x['recent_change']) if label=='settled' else bool(x['future_change_posthoc']) if label=='future_change_posthoc' else not bool(x['future_change_posthoc']))]
        if rr:
          poolstr.append(dict(model=model,horizon_ms=h,method=mode,stratum=label,n=len(rr),position_coverage=float(np.mean([x['position_covered'] for x in rr])),heading_coverage=float(np.mean([x['heading_covered'] for x in rr])),joint_coverage=float(np.mean([x['joint_covered'] for x in rr])),mean_position_q90_mm=float(np.mean([x['position_q90_mm'] for x in rr])),mean_position_q95_mm=float(np.mean([x['position_q95_mm'] for x in rr]))))
wcsv('stage19_pooled_summary.csv',summary);wcsv('stage19_pooled_strata.csv',poolstr)
meta={'data_zip_sha256':hashlib.sha256(ZIP.read_bytes()).hexdigest(),'stage18_model_selection':str(SEL),'fold_design':'Fold f from Stage18 selected causal model tau using validation block 40-50,50-60,60-70,70-80 respectively; next disjoint block 50-60,60-70,70-80,80-90 for residual calibration, followed by 60-70,70-80,80-90,90-100 for evaluation','alpha_position_marginal':0.1,'alpha_heading_marginal':0.1,'alpha_joint_each':0.05,'quantile':'ceil((n+1)*(1-alpha))th sorted residual, infinity when index exceeds n','conditional_rule':'observed command change in past 150ms (causal); no future_change used in calibration or policy','horizons_ms':[100,250,500],'models':['command_only','causal_zero_offset'],'timing':'nominal dt 5ms, predictor uses issue-time-or-earlier commands, logged command application timing uncertain','limitations':['one robot continuous dataset; chronological blocks not exchangeable; split conformal nominal finite-sample guarantee not applicable to dependent drifting recording','project has inspected measured dataset across earlier stages, so the present holdout is chronological, not pristine prospective external data','error bounds describe one-step pose prediction, not obstacle avoidance, docking safety, or physical reliability','reference waveform files deliberately excluded; arbitrary input raw data only','future command changes only used for retrospective audit and never interval construction']}
(ROOT/'stage19_protocol.json').write_text(json.dumps(meta,indent=2))
print('STAGE19 pooled',flush=True)
for r in summary:print(r,flush=True)
print('records',len(cases),'done',flush=True)
