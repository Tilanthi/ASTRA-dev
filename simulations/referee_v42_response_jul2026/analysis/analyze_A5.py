#!/usr/bin/env python3
"""A5: collapse indicator (|grav-E(t)/grav-E(0)|) and dt vs t for the
magnetic-subcriticality long-integration runs. Strong field (low beta) should
resist collapse (flat grav-E, healthy dt); weak field (beta~1) runs away."""
import glob,re,json,numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D="/data/referee_v42_campaigns_jul2026"
def series(hf):
    t=[];dt=[];ge=[]
    for ln in open(hf):
        if ln.startswith("#"): continue
        p=ln.split()
        if len(p)>=10:
            t.append(float(p[0]));dt.append(float(p[1]));ge.append(float(p[9]))
    return np.array(t),np.array(dt),np.array(ge)
rows=[]; fig,axs=plt.subplots(1,2,figsize=(12,5))
cmap={0.05:"#00368a",0.1:"#1f77b4",0.15:"#2ca02c",0.3:"#ff7f0e",1.0:"#d62728"}
for hf in sorted(glob.glob(D+"/A5_*.hst")):
    m=re.search(r"A5_f([\d.]+)_b([\d.]+)_",hf); f=float(m.group(1)); b=float(m.group(2))
    t,dt,ge=series(hf)
    if len(t)<2: continue
    ratio=np.abs(ge/ge[0])
    ls="-" if f==1.5 else "--"
    axs[0].plot(t,ratio,ls,color=cmap.get(b,"k"),label=f"f={f} b={b}")
    axs[1].semilogy(t,dt,ls,color=cmap.get(b,"k"))
    rows.append({"f":f,"beta":b,"t_last":float(t[-1]),"dt_last":float(dt[-1]),
                 "gravE_ratio_last":float(ratio[-1]),"gravE_ratio_max":float(ratio.max())})
axs[0].set_xlabel("t [t_J]"); axs[0].set_ylabel("|grav-E(t)/grav-E(0)|  (collapse indicator)")
axs[0].set_yscale("log"); axs[0].set_title("A5: radial collapse vs plasma-beta (longitudinal B, f>1)")
axs[0].legend(fontsize=7,ncol=2); axs[0].grid(alpha=0.3)
axs[1].set_xlabel("t [t_J]"); axs[1].set_ylabel("timestep dt"); axs[1].set_title("timestep (crash = runaway)")
axs[1].axhline(1e-7,color="gray",ls=":",label="dt_kill"); axs[1].grid(alpha=0.3)
fig.tight_layout(); fig.savefig(D+"/A5_collapse_vs_beta.png",dpi=140)
json.dump(rows,open(D+"/A5_progress.json","w"),indent=1)
print("f    beta  t_last  dt_last   gravE_ratio_last")
for r in sorted(rows,key=lambda x:(x["f"],x["beta"])):
    print("%.1f  %.2f  %.3f  %.2e  %.1f"%(r["f"],r["beta"],r["t_last"],r["dt_last"],r["gravE_ratio_last"]))
