#!/usr/bin/env python3
"""
Step 3: Generate DTC analysis figures.
- Fig 1-5: P(frag|f,beta) heatmaps for M=1,2,3,4,5
- Fig 6: beta_crit(f) curves for all M values
- Fig 7: Stochastic zone map
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

SIMBASE = "/data/dtc_runs"
RESULTS = os.path.join(SIMBASE, "dtc_analysis_results.json")
FIGDIR  = os.path.join(SIMBASE, "dtc_figures")
os.makedirs(FIGDIR, exist_ok=True)

with open(RESULTS) as f:
    data = json.load(f)

p_frag_table   = data["p_frag_table"]
beta_crit_table = data["beta_crit_table"]
summary        = data["summary"]

f_vals    = summary["f_values"]
beta_vals = summary["beta_values"]
mach_vals = summary["mach_values"]

# ── Colour scheme ──────────────────────────────────────────────────────────
CMAP = matplotlib.colormaps["RdYlGn_r"]   # green=stable, red=FRAG
STOCH_COLOR = "gold"

def make_pfrag_matrix(mach):
    """Build 2D array P_frag[i_beta, i_f] for a given Mach number."""
    nf, nb = len(f_vals), len(beta_vals)
    P  = np.full((nb, nf), np.nan)
    St = np.zeros((nb, nf), dtype=bool)
    lookup = {(p["f"], p["beta"]): p for p in p_frag_table if p["mach"] == mach}
    for ib, beta in enumerate(beta_vals):
        for iv, fv in enumerate(f_vals):
            entry = lookup.get((fv, beta))
            if entry:
                P[ib, iv]  = entry["P_frag"]
                St[ib, iv] = entry["stochastic"]
    return P, St

# ── Figs 1–5: P(frag|f,β) heatmaps ───────────────────────────────────────
fig_hm, axes_hm = plt.subplots(1, 5, figsize=(22, 5), sharey=True)
fig_hm.suptitle(
    "DTC: Fragmentation Probability P(frag | f, β) — Longitudinal B-field",
    fontsize=13, fontweight="bold", y=1.02
)

for ax, mach in zip(axes_hm, mach_vals):
    P, St = make_pfrag_matrix(mach)
    im = ax.imshow(
        P, origin="lower", aspect="auto",
        extent=[f_vals[0]-0.05, f_vals[-1]+0.05,
                beta_vals[0]-0.1, beta_vals[-1]+0.1],
        vmin=0, vmax=1, cmap=CMAP, interpolation="nearest"
    )
    # Overlay stochastic points
    for ib, beta in enumerate(beta_vals):
        for iv, fv in enumerate(f_vals):
            if St[ib, iv]:
                ax.plot(fv, beta, "D", color=STOCH_COLOR,
                        markersize=8, markeredgecolor="k", markeredgewidth=0.5, zorder=5)
            elif not np.isnan(P[ib, iv]):
                txt = "✓" if P[ib, iv] == 0 else "✗"
                col = "darkgreen" if P[ib, iv] == 0 else "darkred"
                ax.text(fv, beta, txt, ha="center", va="center",
                        fontsize=8, color=col, fontweight="bold", zorder=6)

    ax.set_title(f"M = {mach:.0f}", fontsize=12, fontweight="bold")
    ax.set_xlabel("f  (line-mass / critical)", fontsize=10)
    ax.set_xticks(f_vals)
    ax.set_xticklabels([f"{v:.1f}" for v in f_vals], rotation=45, fontsize=7)
    ax.set_yticks(beta_vals)

axes_hm[0].set_ylabel("β  (thermal / magnetic pressure)", fontsize=10)
axes_hm[0].set_yticklabels([f"{v:.1f}" for v in beta_vals], fontsize=9)

cbar = fig_hm.colorbar(im, ax=axes_hm.tolist(), shrink=0.8, pad=0.02)
cbar.set_label("P(frag)", fontsize=11)
cbar.set_ticks([0, 0.5, 1])
cbar.set_ticklabels(["0 (stable)", "0.5 (stochastic)", "1.0 (FRAG)"])

legend_elems = [
    Patch(facecolor="green", edgecolor="k", label="Stable (✓)"),
    Line2D([0],[0], marker="D", color="w", markerfacecolor=STOCH_COLOR,
           markeredgecolor="k", markersize=9, label="Stochastic (1/2 FRAG)"),
    Patch(facecolor="red", edgecolor="k", label="Fragmented (✗)"),
]
fig_hm.legend(handles=legend_elems, loc="upper right", fontsize=9,
              bbox_to_anchor=(1.01, 1.0))

fig_hm.tight_layout()
path1 = os.path.join(FIGDIR, "fig1_pfrag_heatmaps.png")
fig_hm.savefig(path1, dpi=150, bbox_inches="tight")
fig_hm.savefig(path1.replace(".png", ".pdf"), bbox_inches="tight")
plt.close(fig_hm)
print(f"Saved {path1}")

# ── Fig 6: β_crit(f) curves for all M ────────────────────────────────────
fig6, ax6 = plt.subplots(figsize=(9, 6))

colors_M = plt.cm.plasma(np.linspace(0.1, 0.9, len(mach_vals)))
markers_M = ["o", "s", "^", "D", "v"]

for mach, col, mk in zip(mach_vals, colors_M, markers_M):
    rows = sorted([b for b in beta_crit_table if b["mach"] == mach], key=lambda x: x["f"])
    fv_list    = [r["f"]         for r in rows if r["beta_crit"] is not None]
    bc_list    = [r["beta_crit"] for r in rows if r["beta_crit"] is not None]
    ctype_list = [r["crit_type"] for r in rows if r["beta_crit"] is not None]

    # Solid line for interpolated, dashed for extrapolated
    solid_f  = [fv_list[i] for i, ct in enumerate(ctype_list) if ct == "interpolated"]
    solid_bc = [bc_list[i] for i, ct in enumerate(ctype_list) if ct == "interpolated"]
    extra_f  = [fv_list[i] for i, ct in enumerate(ctype_list) if ct in ("below_grid","above_grid")]
    extra_bc = [bc_list[i] for i, ct in enumerate(ctype_list) if ct in ("below_grid","above_grid")]

    if solid_f:
        ax6.plot(solid_f, solid_bc, "-", color=col, marker=mk,
                 markersize=7, linewidth=2, label=f"M = {mach:.0f}")
    if extra_f:
        ax6.plot(extra_f, extra_bc, "--", color=col, marker=mk,
                 markersize=7, linewidth=1.5, alpha=0.6)
    # Combine for label if needed
    if not solid_f and extra_f:
        ax6.plot(extra_f, extra_bc, "--", color=col, marker=mk,
                 markersize=7, linewidth=1.5, label=f"M = {mach:.0f} (extrap.)")

ax6.axhline(2/3, color="gray", linestyle=":", linewidth=1.5,
            label=r"β$_{\rm crit}$ = 2/3 (transverse B theory)")
ax6.axhspan(0.3, 0.31, alpha=0.2, color="blue", label="Grid lower limit (β=0.3)")
ax6.axhspan(1.29, 1.3, alpha=0.2, color="orange", label="Grid upper limit (β=1.3)")

ax6.set_xlabel("f  (line-mass / critical line-mass)", fontsize=12)
ax6.set_ylabel(r"β$_{\rm crit}$(f, M)", fontsize=12)
ax6.set_title("DTC: Critical plasma-β for fragmentation onset\n(Longitudinal B-field, isothermal MHD)",
              fontsize=12, fontweight="bold")
ax6.set_xlim(1.35, 2.25)
ax6.set_ylim(0.1, 1.5)
ax6.set_xticks(f_vals)
ax6.set_xticklabels([f"{v:.1f}" for v in f_vals])
ax6.legend(fontsize=10, loc="upper right")
ax6.grid(True, alpha=0.3)

fig6.tight_layout()
path6 = os.path.join(FIGDIR, "fig2_beta_crit_curves.png")
fig6.savefig(path6, dpi=150, bbox_inches="tight")
fig6.savefig(path6.replace(".png", ".pdf"), bbox_inches="tight")
plt.close(fig6)
print(f"Saved {path6}")

# ── Fig 7: Stochastic zone map (all M combined) ───────────────────────────
fig7, axes7 = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
fig7.suptitle("DTC: Transition zone classification by M\n(✓=stable, ◆=stochastic, ✗=FRAG)",
              fontsize=12, fontweight="bold")

for ax, mach in zip(axes7, [1.0, 2.0, 3.0]):
    P, St = make_pfrag_matrix(mach)
    # 0=stable, 0.5=stochastic, 1=frag → use discrete colormap
    cmap3 = mcolors.ListedColormap(["#2ecc71", "#f1c40f", "#e74c3c"])
    bounds = [-0.25, 0.25, 0.75, 1.25]
    norm3  = mcolors.BoundaryNorm(bounds, cmap3.N)

    ax.imshow(P, origin="lower", aspect="auto",
              extent=[f_vals[0]-0.05, f_vals[-1]+0.05,
                      beta_vals[0]-0.1, beta_vals[-1]+0.1],
              cmap=cmap3, norm=norm3, interpolation="nearest")

    # Annotate each cell
    lookup = {(p["f"], p["beta"]): p for p in p_frag_table if p["mach"] == mach}
    for ib, beta in enumerate(beta_vals):
        for iv, fv in enumerate(f_vals):
            entry = lookup.get((fv, beta))
            if entry:
                txt = "✓" if entry["P_frag"] == 0 else ("◆" if entry["stochastic"] else "✗")
                ax.text(fv, beta, txt, ha="center", va="center", fontsize=9, fontweight="bold")

    ax.set_title(f"M = {mach:.0f}", fontsize=12, fontweight="bold")
    ax.set_xlabel("f", fontsize=11)
    ax.set_xticks(f_vals)
    ax.set_xticklabels([f"{v:.1f}" for v in f_vals], rotation=45, fontsize=7)
    ax.set_yticks(beta_vals)

axes7[0].set_ylabel("β", fontsize=12)
axes7[0].set_yticklabels([f"{v:.1f}" for v in beta_vals])

legend_elems7 = [
    Patch(facecolor="#2ecc71", label="Stable (✓, P=0)"),
    Patch(facecolor="#f1c40f", label="Stochastic (◆, P=0.5)"),
    Patch(facecolor="#e74c3c", label="Fragmented (✗, P=1)"),
]
fig7.legend(handles=legend_elems7, loc="lower center", ncol=3,
            fontsize=10, bbox_to_anchor=(0.5, -0.05))

fig7.tight_layout()
path7 = os.path.join(FIGDIR, "fig3_transition_zone_M123.png")
fig7.savefig(path7, dpi=150, bbox_inches="tight")
fig7.savefig(path7.replace(".png", ".pdf"), bbox_inches="tight")
plt.close(fig7)
print(f"Saved {path7}")

# ── Fig 8: Extended phase (M=4,5) summary ─────────────────────────────────
fig8, axes8 = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
fig8.suptitle("DTC Extended Phase: M=4,5 Fragmentation Map",
              fontsize=12, fontweight="bold")

for ax, mach in zip(axes8, [4.0, 5.0]):
    P, St = make_pfrag_matrix(mach)
    cmap3 = mcolors.ListedColormap(["#2ecc71", "#f1c40f", "#e74c3c"])
    bounds = [-0.25, 0.25, 0.75, 1.25]
    norm3  = mcolors.BoundaryNorm(bounds, cmap3.N)
    ax.imshow(P, origin="lower", aspect="auto",
              extent=[f_vals[0]-0.05, f_vals[-1]+0.05,
                      beta_vals[0]-0.1, beta_vals[-1]+0.1],
              cmap=cmap3, norm=norm3, interpolation="nearest")
    lookup = {(p["f"], p["beta"]): p for p in p_frag_table if p["mach"] == mach}
    for ib, beta in enumerate(beta_vals):
        for iv, fv in enumerate(f_vals):
            entry = lookup.get((fv, beta))
            if entry:
                txt = "✓" if entry["P_frag"] == 0 else ("◆" if entry["stochastic"] else "✗")
                ax.text(fv, beta, txt, ha="center", va="center", fontsize=9, fontweight="bold")
    ax.set_title(f"M = {mach:.0f}", fontsize=12, fontweight="bold")
    ax.set_xlabel("f", fontsize=11)
    ax.set_xticks(f_vals)
    ax.set_xticklabels([f"{v:.1f}" for v in f_vals], rotation=45, fontsize=7)
    ax.set_yticks(beta_vals)

axes8[0].set_ylabel("β", fontsize=12)
axes8[0].set_yticklabels([f"{v:.1f}" for v in beta_vals])
fig8.legend(handles=legend_elems7, loc="lower center", ncol=3,
            fontsize=10, bbox_to_anchor=(0.5, -0.05))
fig8.tight_layout()
path8 = os.path.join(FIGDIR, "fig4_transition_zone_M45.png")
fig8.savefig(path8, dpi=150, bbox_inches="tight")
fig8.savefig(path8.replace(".png", ".pdf"), bbox_inches="tight")
plt.close(fig8)
print(f"Saved {path8}")

print(f"\nAll figures saved to {FIGDIR}/")
print("Files generated:")
for fn in sorted(os.listdir(FIGDIR)):
    size = os.path.getsize(os.path.join(FIGDIR, fn))
    print(f"  {fn}  ({size//1024} KB)")
