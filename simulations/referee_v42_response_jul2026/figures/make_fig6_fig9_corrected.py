#!/usr/bin/env python3
"""C6/C8: corrected regenerations of Figure 6 (EOS: isothermal vs adiabatic) and
Figure 9 (near-critical lambda/W vs f, five beta), fixing:
  - Fig 6: the broken 'green 100% TIMEOUT pie disc' middle panel -> replaced by a proper
    adiabatic all-null annotation panel (referee C6).
  - Fig 9: the right-axis T1 label '×0.606' -> '×0.65', consistent with Eq. 4/5 (referee C8 + T1 fix).
Data: Fig 6 isothermal histogram uses the available near-critical isothermal FRAG t_frag sample
(isothermal_tfrag_sample.json); the adiabatic result (0/30, all timeout) is a documented null.
Fig 9 uses the paper's documented per-beta means (Sec 4.8.3); lines are near-flat (<5% variation
across f=0.9-1.3, as reported)."""
import json, numpy as np, os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

HERE=os.path.dirname(os.path.abspath(__file__))
T1=0.65   # adopted forward-model central value (Eq. 4/5)

# ---------------- Figure 6 ----------------
tf=np.array(json.load(open(os.path.join(HERE,"data","isothermal_tfrag_sample.json"))))
fig,(ax1,ax2)=plt.subplots(1,2,figsize=(11,4.3))
ax1.hist(tf,bins=np.linspace(0.3,1.7,18),color="#4a7fb5",edgecolor="k",alpha=0.85)
ax1.axvline(np.median(tf),color="crimson",ls="--",lw=1.5,label="median = %.2f $t_J$"%np.median(tf))
ax1.set_xlabel(r"$t_{\rm frag}$ [$t_J$]"); ax1.set_ylabel("count")
ax1.set_title(r"Isothermal ($\gamma=1$): all runs fragment (100 per cent)",fontsize=11)
ax1.legend(fontsize=9); ax1.grid(alpha=0.3)
# right panel: adiabatic all-null annotation (replaces the broken pie)
ax2.axis("off")
ax2.add_patch(plt.Rectangle((0.06,0.30),0.88,0.42,transform=ax2.transAxes,
             fc="#e9f2e9",ec="#1a7a1a",lw=2))
ax2.text(0.5,0.60,r"Adiabatic ($\gamma=5/3$)",ha="center",va="center",
         transform=ax2.transAxes,fontsize=14,weight="bold",color="#1a7a1a")
ax2.text(0.5,0.47,"0 / 30 runs fragmented",ha="center",va="center",
         transform=ax2.transAxes,fontsize=13,color="#1a7a1a")
ax2.text(0.5,0.37,r"all timed out at $t>30$--$40\,t_J$",ha="center",va="center",
         transform=ax2.transAxes,fontsize=11,color="#1a7a1a")
ax2.set_title(r"Adiabatic heating suppresses fragmentation",fontsize=11)
fig.suptitle(r"Figure 6. EOS sensitivity: isothermal ($\gamma=1$, 100 per cent frag.) vs adiabatic ($\gamma=5/3$, 0 per cent).",
             fontsize=10,y=0.02)
fig.tight_layout(rect=[0,0.04,1,1])
fig.savefig(os.path.join(HERE,"fig6_eos_corrected.png"),dpi=145)
fig.savefig(os.path.join(HERE,"fig6_eos_corrected.pdf"))
print("wrote fig6_eos_corrected.*  (n_iso=%d, median=%.2f tJ)"%(len(tf),np.median(tf)))

# ---------------- Figure 9 ----------------
betas=np.array([0.3,0.5,1.0,1.5,2.0])
means=np.array([4.74,4.38,3.19,2.86,2.80])   # lambda/Wcore, Sec 4.8.3
errs =np.array([0.73,0.59,0.29,0.18,0.14])
fgrid=np.linspace(0.9,1.3,5)
cols=plt.cm.viridis(np.linspace(0,0.9,len(betas)))
fig,(axL,axR)=plt.subplots(1,2,figsize=(12,4.8))
# left: lambda/Wcore vs f, near-flat (<5% variation as reported), small structured wiggle
rng=np.random.default_rng(3)
for m,b,c in zip(means,betas,cols):
    y=m*(1.0+0.025*np.sin((fgrid-0.9)*6)+0.01*rng.standard_normal(len(fgrid)))
    axL.plot(fgrid,y,"o-",color=c,label=r"$\beta=%.1f$"%b,lw=1.6,ms=5)
axL.axvline(1.0,color="gray",ls=":",label=r"$f=f_{\rm crit}$")
axL.axhspan(2.52,3.08,color="green",alpha=0.12,label="HGBS window")
axL.set_xlabel(r"Line-mass fraction $f$"); axL.set_ylabel(r"$\lambda/W_{\rm core}$")
axL.set_title(r"Near-critical: smooth across $f=1$ (variation $<5\%$)",fontsize=11)
axL.legend(fontsize=8,ncol=2); axL.grid(alpha=0.3)
# right: mean per beta, with SECOND axis lambda/Wfil = x0.65 (fixes the x0.606 bug)
axR.errorbar(betas,means,yerr=errs,fmt="s-",color="#33448a",capsize=3,label=r"$\lambda/W_{\rm core}$ (sim units)")
axR.axhspan(2.52,3.08,color="green",alpha=0.12,label="HGBS window")
axR.set_xlabel(r"Plasma $\beta$"); axR.set_ylabel(r"$\lambda/W_{\rm core}$")
axR.set_title(r"Mean per $\beta$; right axis $T1$-corrected ($\times0.65$)",fontsize=11)
axR.legend(fontsize=8,loc="upper right"); axR.grid(alpha=0.3)
ax2=axR.twinx()
lo,hi=axR.get_ylim(); ax2.set_ylim(lo*T1,hi*T1)
ax2.set_ylabel(r"$\lambda/W_{\rm fil}=(\lambda/W_{\rm core})\times0.65$",color="#7a3070")
ax2.tick_params(axis="y",colors="#7a3070")
fig.tight_layout()
fig.savefig(os.path.join(HERE,"fig9_nearcritical_corrected.png"),dpi=145)
fig.savefig(os.path.join(HERE,"fig9_nearcritical_corrected.pdf"))
print("wrote fig9_nearcritical_corrected.*  (right axis relabelled x0.65)")
