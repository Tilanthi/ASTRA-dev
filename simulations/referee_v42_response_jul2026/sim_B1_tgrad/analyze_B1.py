#!/usr/bin/env python3
"""B1: measure the local fragmentation wavelength in the WARM vs COOL halves of the
imposed sinusoidal temperature gradient, and compare to the fixed-density sqrt(T)
prediction lambda ~ cs_loc.  T-profile: cs^2(x1)=cs0^2[1+A sin(2 pi (x1-x1min)/Lx)],
A=0.125 -> warm half x in (0,Lx/2) (sin>0), cool half x in (Lx/2,Lx) (sin<0)."""
import glob, re, json, numpy as np, h5py
from scipy.signal import find_peaks
D="/data/referee_v42_campaigns_jul2026/configs_B1"
A=0.125; Lx=16.0; x1min=0.0

def global_rho(fn):
    with h5py.File(fn,"r") as h5:
        prim=np.array(h5["prim"][0]); loc=np.array(h5["LogicalLocations"])
        x1f=np.array(h5["x1f"]); t=float(h5.attrs["Time"])
    nb,nzb,nyb,nxb=prim.shape
    NX=(loc[:,0].max()+1)*nxb
    rho=np.zeros(((loc[:,2].max()+1)*nzb,(loc[:,1].max()+1)*nyb,NX))
    for b in range(nb):
        xi,yi,zi=loc[b]
        rho[zi*nzb:(zi+1)*nzb,yi*nyb:(yi+1)*nyb,xi*nxb:(xi+1)*nxb]=prim[b]
    return rho,NX,t

def spacing(prof,xs):
    d=prof/prof.mean()-1.0
    thr=max(3*d.std(),0.05)
    pk,_=find_peaks(d,prominence=thr)
    return xs[pk]

snaps=sorted(glob.glob(D+"/B1_*.prim.*.athdf"),key=lambda s:int(re.search(r"\.(\d+)\.athdf$",s).group(1)))
best=None
for fn in snaps:
    rho,NX,t=global_rho(fn)
    xs=x1min+(np.arange(NX)+0.5)*Lx/NX
    prof=rho.mean(axis=(0,1))
    pkx=spacing(prof,xs)
    npk=len(pkx)
    if best is None or npk>=best["npk"]:
        best={"t":round(t,3),"npk":npk,"pkx":pkx.tolist(),"prof":prof.tolist(),"xs":xs.tolist()}

pkx=np.array(best["pkx"])
warm=pkx[pkx<Lx/2]; cool=pkx[pkx>=Lx/2]
def med_sp(p):
    if len(p)<2: return None,len(p)
    return float(np.median(np.diff(np.sort(p)))),len(p)
lw,nw=med_sp(warm); lc,nc=med_sp(cool)
# quarter regions (warmest around x=Lx/4, coolest around x=3Lx/4)
wq=pkx[(pkx>Lx/8)&(pkx<3*Lx/8)]; cq=pkx[(pkx>5*Lx/8)&(pkx<7*Lx/8)]
lwq,nwq=med_sp(wq); lcq,ncq=med_sp(cq)
# predictions (fixed-density sqrt(T)): lambda ~ cs_loc; half-averaged and quarter (peak/trough)
cs_warm_half=np.sqrt(1+A*(2/np.pi)); cs_cool_half=np.sqrt(1-A*(2/np.pi))
cs_warm_pk=np.sqrt(1+A);            cs_cool_tr=np.sqrt(1-A)
out={"beading_epoch":best["t"],"n_peaks":best["npk"],
     "warm_half":{"median_lambda":lw,"n":nw},"cool_half":{"median_lambda":lc,"n":nc},
     "warm_quarter":{"median_lambda":lwq,"n":nwq},"cool_quarter":{"median_lambda":lcq,"n":ncq},
     "ratio_half_measured":(lw/lc if (lw and lc) else None),
     "ratio_half_predicted":cs_warm_half/cs_cool_half,
     "ratio_quarter_measured":(lwq/lcq if (lwq and lcq) else None),
     "ratio_quarter_predicted":cs_warm_pk/cs_cool_tr,
     "peaks_x":pkx.tolist()}
json.dump({**out,"prof":best["prof"],"xs":best["xs"]},open(D+"/../B1_tgrad_result.json","w"),indent=1)
print(json.dumps(out,indent=1))
