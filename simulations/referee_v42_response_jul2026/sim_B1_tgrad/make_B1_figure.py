#!/usr/bin/env python3
"""B1 figure: transverse-averaged longitudinal density profile for the T-gradient run
(warm half x<Lx/2, cool half x>Lx/2) vs the uniform-T control, at the beading epoch.
Demonstrates that a ~12% (observed-magnitude) temperature gradient produces spatially
differential fragmentation: the cool (locally supercritical) half beads while the warm
(locally subcritical) half stays smooth; the control fragments uniformly."""
import glob, re, json, numpy as np, h5py, os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.signal import find_peaks
D="/data/referee_v42_campaigns_jul2026/configs_B1"
A=0.125; Lx=16.0

def prof_at_maxpeaks(pattern):
    snaps=sorted(glob.glob(D+"/"+pattern),key=lambda s:int(re.search(r"\.(\d+)\.athdf$",s).group(1)))
    best=None
    for fn in snaps:
        with h5py.File(fn,"r") as h5:
            prim=np.array(h5["prim"][0]); loc=np.array(h5["LogicalLocations"]); t=float(h5.attrs["Time"])
        nb,nzb,nyb,nxb=prim.shape; NX=(loc[:,0].max()+1)*nxb
        rho=np.zeros(((loc[:,2].max()+1)*nzb,(loc[:,1].max()+1)*nyb,NX))
        for b in range(nb):
            xi,yi,zi=loc[b]; rho[zi*nzb:(zi+1)*nzb,yi*nyb:(yi+1)*nyb,xi*nxb:(xi+1)*nxb]=prim[b]
        prof=rho.mean(axis=(0,1)); xs=(np.arange(NX)+0.5)*Lx/NX
        d=prof/prof.mean()-1.0; pk,_=find_peaks(d,prominence=max(3*d.std(),0.05))
        if best is None or len(pk)>=best["npk"]:
            best={"t":t,"npk":len(pk),"xs":xs,"prof":prof,"pk":xs[pk]}
    return best

grad=prof_at_maxpeaks("B1_tgrad_f1.05_a1e-2_s42.prim.*.athdf")
ctrl=prof_at_maxpeaks("B1_ctrl_uniform_f1.05_s42.prim.*.athdf")

fig,(ax1,ax2)=plt.subplots(2,1,figsize=(10,7),sharex=True)
# T-gradient run
ax1.plot(grad["xs"],grad["prof"],color="#333",lw=1.2)
ax1.plot(grad["pk"],np.interp(grad["pk"],grad["xs"],grad["prof"]),"v",color="crimson",ms=7,label="detected beads")
ax1.axvspan(0,Lx/2,color="#c65a2e",alpha=0.10); ax1.axvspan(Lx/2,Lx,color="#2e6ec6",alpha=0.10)
ax1.text(Lx*0.25,ax1.get_ylim()[1]*0.9,"WARM half\n(locally subcritical)",ha="center",color="#a03000",fontsize=10)
ax1.text(Lx*0.75,ax1.get_ylim()[1]*0.9,"COOL half\n(locally supercritical)",ha="center",color="#003a80",fontsize=10)
ax1.set_ylabel(r"$\langle\rho\rangle_{yz}(x)$")
ax1.set_title(r"T-gradient run ($A=0.125$, $\sim$12%% $\lambda_J$): differential fragmentation (t=%.2f, %d beads)"%(grad["t"],grad["npk"]))
ax1.legend(fontsize=9,loc="upper left")
# cs^2 profile on twin axis
axt=ax1.twinx(); xs=grad["xs"]
axt.plot(xs,1+A*np.sin(2*np.pi*xs/Lx),color="green",ls="--",lw=1,alpha=0.7)
axt.set_ylabel(r"imposed $c_s^2/c_{s0}^2$",color="green"); axt.tick_params(axis="y",colors="green")
# control
ax2.plot(ctrl["xs"],ctrl["prof"],color="#333",lw=1.2)
ax2.plot(ctrl["pk"],np.interp(ctrl["pk"],ctrl["xs"],ctrl["prof"]),"v",color="crimson",ms=7)
ax2.set_ylabel(r"$\langle\rho\rangle_{yz}(x)$"); ax2.set_xlabel(r"$x$ [$\lambda_J$]")
ax2.set_title(r"Uniform-T control (same $f$): fragments uniformly (t=%.2f, %d beads)"%(ctrl["t"],ctrl["npk"]))
fig.tight_layout(); fig.savefig(D+"/../B1_tgrad_figure.png",dpi=145); fig.savefig(D+"/../B1_tgrad_figure.pdf")

def medsp(p): 
    p=np.sort(p); return float(np.median(np.diff(p))) if len(p)>1 else None
res={"gradient":{"t":round(grad["t"],3),"n_beads":grad["npk"],
      "n_warm":int((grad["pk"]<Lx/2).sum()),"n_cool":int((grad["pk"]>=Lx/2).sum()),
      "lambda_cool_lamJ":medsp(grad["pk"][grad["pk"]>=Lx/2]),
      "lambda_warm_lamJ":medsp(grad["pk"][grad["pk"]<Lx/2])},
     "control":{"t":round(ctrl["t"],3),"n_beads":ctrl["npk"],"lambda_lamJ":medsp(ctrl["pk"])}}
for seg in ["lambda_cool_lamJ","lambda_warm_lamJ"]:
    v=res["gradient"][seg]; 
    if v: res["gradient"][seg.replace("lamJ","over_Wfil")]=round(v/0.3*0.65,3)
if res["control"]["lambda_lamJ"]:
    res["control"]["lambda_over_Wfil"]=round(res["control"]["lambda_lamJ"]/0.3*0.65,3)
json.dump(res,open(D+"/../B1_tgrad_result.json","w"),indent=1)
print(json.dumps(res,indent=1))
