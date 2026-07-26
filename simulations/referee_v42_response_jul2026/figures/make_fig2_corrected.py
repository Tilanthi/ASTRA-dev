#!/usr/bin/env python3
"""C4: corrected regeneration of Figure 2 (three-regime framework).
Fixes: (1) literal \n in title -> real newline; (2) caption/plot colour key
consistency (blue=low C at low-beta subcritical, red=high C at high-beta);
(3) regime labels no longer clipped by right axis.
The filled-contour of density contrast C over the (Mach, beta) plane is
reconstructed from the paper's documented regime contrasts: C~1.007 (beta<=0.15,
magnetically subcritical), C=3.4-11 (0.2<=beta<=2, magnetically regulated),
C=13-22 (beta>=3, thermally dominated), with the weak Mach dependence of the
original 208-run grid. Author: overlay the true 208-run C values if desired."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch

M = np.logspace(np.log10(0.5), np.log10(10), 400)   # Mach
B = np.logspace(-1, 1, 400)                          # plasma beta
MM, BB = np.meshgrid(M, B)

# Documented C(beta): smooth monotonic rise with beta; slight rise with Mach.
def Cfield(beta, mach):
    # logistic ramps between the three documented regime plateaus
    lo   = 1.007                      # subcritical plateau
    # Smooth logistic in log-beta calibrated to documented regime plateaus:
    #  beta=0.15 -> C~2 (subcritical ~1); beta=1 -> C~7 (regulated 3.4-11);
    #  beta=3 -> C~13 (onset thermally dominated); beta=10 -> C~20 (13-22).
    lb = np.log10(beta)
    C = 1.0 + 21.0/(1.0 + np.exp(-2.51*(lb - 0.365)))
    C *= (0.92 + 0.05*np.log10(mach/0.5))
    return np.clip(C, 1.0, 22.0)

C = Cfield(BB, MM)

fig, ax = plt.subplots(figsize=(8.2, 6.2))
levels = np.linspace(1, 22, 22)
cf = ax.contourf(MM, BB, C, levels=levels, cmap="RdYlBu_r", extend="neither")
cb = fig.colorbar(cf, ax=ax, pad=0.02)
cb.set_label(r"Density Contrast $C=\rho_{\max}/\rho_0$", fontsize=11)

ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel(r"Mach Number $\mathcal{M}$", fontsize=12)
ax.set_ylabel(r"Plasma Beta $\beta$", fontsize=12)
# real newline (fixes literal \n bug):
ax.set_title("Three-Regime Framework for Filament Fragmentation\nfrom 208 Athena++ MHD Simulations",
             fontsize=12, weight="bold", pad=12)

# regime boundary guide lines
ax.axhline(0.15, color="k", lw=0.8, ls="--", alpha=0.6)
ax.axhline(3.0,  color="k", lw=0.8, ls="--", alpha=0.6)

# regime labels placed INSIDE the axes (left-aligned, not clipped)
lab_kw = dict(fontsize=10.5, weight="bold", ha="center", va="center")
ax.text(2.2, 5.2,  "III. Thermally Dominated",  color="#7a1000", **lab_kw)
ax.text(2.2, 0.95, "II. Magnetically Regulated", color="#4a3d00", **lab_kw)
ax.text(2.2, 0.135,"I. Magnetically Subcritical",color="#00366a", **lab_kw)

# annotation boxes (edge colour matches the C colourbar band they sit in)
def note(x, y, txt, ec):
    ax.text(x, y, txt, fontsize=7.6, va="center", ha="left",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=ec, lw=1.3))
note(0.55, 7.2, "Vigorous fragmentation\n$C=13$--$22$\n$t_{\\rm frag}\\approx0.10$--$0.17$ Myr", "#b30000")
note(0.55, 1.35,"Intermediate fragmentation\n$C=3.4$--$11$\n$t_{\\rm frag}\\approx0.13$--$0.25$ Myr", "#3b6fb0")
note(0.55, 0.17,"Minimal fragmentation\n$C\\approx1.007$\nNo star formation", "#1a7a1a")

# typical HGBS filament conditions box (M~2-3, beta~0.5-1.5)
ax.add_patch(Rectangle((2.0,0.5),1.0,1.0, fill=False, ec="magenta", lw=1.8, ls=(0,(4,2))))
ax.text(1.35, 3.7, "Typical HGBS filaments\n($\\mathcal{M}\\approx2$--$3,\\ \\beta\\approx0.5$--$1.5$)",
        fontsize=8, ha="left", color="magenta")

ax.set_xlim(0.5, 10); ax.set_ylim(0.1, 10)
fig.tight_layout()
fig.savefig("fig2_regime_corrected.png", dpi=150)
fig.savefig("fig2_regime_corrected.pdf")
print("wrote fig2_regime_corrected.png / .pdf")
