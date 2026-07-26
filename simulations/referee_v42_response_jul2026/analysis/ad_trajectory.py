#!/usr/bin/env python3
import glob, re, json, numpy as np, h5py
from pathlib import Path
AD_DIR="/data/referee_v40_campaigns_jul2026"
def global_rho(fn):
    with h5py.File(fn,"r") as h5:
        prim=np.array(h5["prim"][0]); loc=np.array(h5["LogicalLocations"])
    nb,nzb,nyb,nxb=prim.shape
    rho=np.empty(((loc[:,2].max()+1)*nzb,(loc[:,1].max()+1)*nyb,(loc[:,0].max()+1)*nxb),dtype=prim.dtype)
    for b in range(nb):
        xi,yi,zi=loc[b]
        rho[zi*nzb:(zi+1)*nzb,yi*nyb:(yi+1)*nyb,xi*nxb:(xi+1)*nxb]=prim[b]
    return rho
def axial_stats(rho,Lx=8.0):
    C=float(rho.max()/(rho.mean()+1e-30))
    prof=rho.mean(axis=(0,1)); d=prof/(prof.mean()+1e-30)-1.0
    rms=float(d.std()); n=len(d); thr=max(3.0*rms,0.02); pk=[]
    for i in range(2,n-2):
        if d[i]>d[i-1] and d[i]>=d[i+1] and d[i]>thr: pk.append(i*Lx/n)
    lam=None
    if len(pk)>=2:
        sp=np.diff(pk); sp=np.append(sp,Lx-(pk[-1]-pk[0])); lam=float(np.median(sp))
    return C,rms,len(pk),lam
def tof(fn):
    with h5py.File(fn,"r") as h5: return float(h5.attrs["Time"])
pids=sorted({re.sub(r"\.prim\.\d+\.athdf$","",Path(f).name) for f in glob.glob(AD_DIR+"/AD_*.prim.*.athdf")})
out=[]
for pid in pids:
    snaps=sorted(glob.glob(AD_DIR+"/"+pid+".prim.*.athdf"),key=lambda s:int(re.search(r"\.(\d+)\.athdf$",s).group(1)))
    traj=[]
    for fn in snaps:
        try:
            rho=global_rho(fn); C,rms,npk,lam=axial_stats(rho); t=tof(fn)
            traj.append({"t":round(t,3),"C":round(C,2),"npk":npk,"lam":(round(lam,4) if lam else None)})
        except Exception as e:
            traj.append({"err":str(e)})
    out.append({"pid":pid,"traj":traj})
    valid=[p for p in traj if p.get("lam")]
    lams=[p["lam"] for p in valid[-4:]]
    spread=round((max(lams)-min(lams))/np.median(lams)*100,1) if len(lams)>=2 else None
    print("%-40s nsnap=%d tail_lam=%s spread_pct=%s"%(pid,len(traj),str(lams),str(spread)))
json.dump(out,open("/data/referee_v42_campaigns_jul2026/ad_lambda_trajectory.json","w"),indent=1)
print("WROTE ad_lambda_trajectory.json")
