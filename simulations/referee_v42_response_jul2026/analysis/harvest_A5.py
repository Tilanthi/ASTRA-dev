#!/usr/bin/env python3
"""A5/A5b harvest: collapse indicator |grav-E(t)/grav-E(0)| vs t for the
magnetic-subcriticality long-integration runs, comparing at MATCHED time so the
plasma-beta dependence is not confounded by the runs reaching different final t.
Strong field (low beta) should show strongly suppressed collapse; beta=1 runs away."""
import glob, re, json, numpy as np, os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D="/data/referee_v42_campaigns_jul2026"

def series(hf):
    t=[]; ge=[]
    for ln in open(hf):
        if ln.startswith("#"): continue
        p=ln.split()
        if len(p)>=10: t.append(float(p[0])); ge.append(float(p[9]))
    t=np.array(t); ge=np.array(ge)
    return t, np.abs(ge/ge[0])

def ratio_at(t, r, tq):
    idx=np.searchsorted(t, tq)
    return float(r[min(idx, len(r)-1)]) if len(r) else None

cmap={0.05:"#08306b",0.10:"#2171b5",0.15:"#6baed6",0.30:"#fd8d3c",1.0:"#cb181d",2.0:"#67000d"}
rows=[]
fig,ax=plt.subplots(figsize=(9,5.5))
for hf in sorted(glob.glob(D+"/configs_A5/../A5_*.hst")) + sorted(glob.glob(D+"/A5b_*.hst")):
    m=re.search(r"A5b?_f([\d.]+)_b([\d.]+)_", os.path.basename(hf))
    if not m: continue
    f=float(m.group(1)); b=float(m.group(2))
    t,r=series(hf)
    if len(t)<3: continue
    ls="-" if f<=1.0 else "--"
    ax.semilogy(t, r, ls, color=cmap.get(b,"k"), lw=1.5, alpha=0.85,
                label=f"f={f}, b={b}")
    rows.append({"f":f,"beta":b,"t_final":round(float(t[-1]),3),
                 "gravE_ratio_at_0.85":round(ratio_at(t,r,0.85),1),
                 "gravE_ratio_final":round(float(r[-1]),1)})
ax.axvline(0.85, color="gray", ls=":", lw=1)
ax.text(0.855, ax.get_ylim()[1]*0.4, "matched-time\ncomparison", fontsize=8, color="gray")
ax.set_xlabel(r"$t$ [$t_J$]"); ax.set_ylabel(r"collapse indicator  $|E_{\rm grav}(t)/E_{\rm grav}(0)|$")
ax.set_title("A5: radial collapse vs plasma-$\\beta$ (longitudinal B, ambient/periodic)\n"
             "strong field (low $\\beta$) strongly suppresses collapse")
ax.legend(fontsize=7, ncol=3, loc="lower right"); ax.grid(alpha=0.3, which="both")
fig.tight_layout(); fig.savefig(D+"/A5_collapse_vs_beta.png", dpi=145); fig.savefig(D+"/A5_collapse_vs_beta.pdf")

# summary grouped by beta at matched time (near-critical f<=1.0 subset)
by_b={}
for r in rows:
    if r["f"]<=1.0:
        by_b.setdefault(r["beta"],[]).append(r["gravE_ratio_at_0.85"])
summary={str(b):{"mean_gravE_ratio_at_0.85":round(float(np.mean(v)),1),"n":len(v)} for b,v in sorted(by_b.items())}
json.dump({"runs":rows,"by_beta_at_t0.85_fle1.0":summary}, open(D+"/A5_harvest.json","w"), indent=1)
print("BY BETA at t=0.85 (f<=1.0):", json.dumps(summary))
for r in sorted(rows,key=lambda x:(x["f"],x["beta"])):
    print(r)
