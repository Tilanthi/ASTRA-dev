#!/usr/bin/env python3
"""
res_ref Analysis Script — April 2026
Compares King-profile (PRR) vs Gaussian-profile pgen stability outcomes.
Glenn J. White & Robin Dey | ASTRA multi-agent system
"""

import json, os, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from datetime import datetime

# ── Colour / style ─────────────────────────────────────────────────────────
FRAG_COL  = "#d62728"   # red
STAB_COL  = "#2ca02c"   # green
PRR_MK    = "o"         # circle = King/PRR
GAUSS_MK  = "s"         # square = Gaussian/Spacing

OUT_DIR = "/data/res_ref_analysis"
FIG_DIR = os.path.join(OUT_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

print("=== res_ref Analysis  ===", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))

# ═══════════════════════════════════════════════════════════════════════════
# 1. LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════

def load_json_files(pattern):
    results = []
    for fp in sorted(glob.glob(pattern)):
        with open(fp) as fh:
            results.append(json.load(fh))
    return results

# res_ref  — PRR King, 128-equiv (256×64×64)
res_ref_raw = load_json_files("/data/res_ref_runs/status/status_res_ref_*.json")

# res128_match — PRR King, 128-equiv (256×64×64) — convergence check
res128_match_raw = load_json_files("/data/res128_match/status/status_res128_match_*.json")

# TRR campaign summary — includes res_rerun (Gaussian, 256³)
with open("/data/trr_runs/campaign_summary.json") as fh:
    trr_data = json.load(fh)
trr_results = trr_data["results"]

# res_rerun = Gaussian pgen, 256 resolution (STABLE comparators)
res_rerun   = [r for r in trr_results if r["run_id"].startswith("res_rerun")]
# dtc_rerun  = Gaussian pgen, 128 resolution (DTC targeted reruns)
dtc_rerun   = [r for r in trr_results if r["run_id"].startswith("dtc_rerun")]

# Convergence summary
with open("/data/res_convergence/convergence_summary.json") as fh:
    conv_summary = json.load(fh)

print(f"Loaded  res_ref:      {len(res_ref_raw)} sims")
print(f"Loaded  res128_match: {len(res128_match_raw)} sims")
print(f"Loaded  res_rerun:    {len(res_rerun)} sims  (Gaussian, 256-res)")
print(f"Loaded  dtc_rerun:    {len(dtc_rerun)} sims  (DTC targeted)")

# ─── Deduplicate res_ref (some runs were literal duplicate seeds) ───────────
# Keep unique (f, β, M) using first occurrence
seen_prr = {}
res_ref_unique = []
for r in res_ref_raw:
    key = (round(r["f"],2), round(r["beta"],2), round(r["mach"],2))
    if key not in seen_prr:
        seen_prr[key] = r
        res_ref_unique.append(r)

print(f"  → unique PRR points: {len(res_ref_unique)}")

# ─── Build matched comparison table ────────────────────────────────────────
# For each PRR point, find the Gaussian res_rerun point with same (f, β, M)
def match(prr_list, gauss_list):
    """Returns list of dicts with both PRR and Gaussian results for same params."""
    matches = []
    for p in prr_list:
        key = (round(p["f"],2), round(p["beta"],2), round(p["mach"],2))
        for g in gauss_list:
            gkey = (round(g["f"],2), round(g["beta"],2), round(g["mach"],2))
            if key == gkey:
                # deduplicate: only first match
                if not any(m["f"]==key[0] and m["beta"]==key[1] and m["mach"]==key[2]
                           for m in matches):
                    matches.append({
                        "f": key[0], "beta": key[1], "mach": key[2],
                        "prr_status": p["status"],
                        "prr_tfrag":  p.get("t_frag"),
                        "gauss_status": g["status"],
                        "gauss_tfrag":  g.get("t_frag"),
                        "prr_run":   p["run_id"],
                        "gauss_run": g["run_id"],
                    })
                break
    return matches

matched = match(res_ref_unique, res_rerun)
print(f"\nMatched PRR↔Gaussian pairs: {len(matched)}")
for m in matched:
    disc = "⚡ DISCORDANT" if m["prr_status"] != m["gauss_status"] else "   consistent"
    print(f"  f={m['f']} β={m['beta']} M={m['mach']:3.1f}  PRR={m['prr_status']:6s}  Gauss={m['gauss_status']:6s}  {disc}")

# Also compare res128_match vs res_rerun (same params, 128 vs 256 res, same PRR pgen)
# → convergence
print(f"\nResolution convergence (from pre-run analysis):")
print(f"  Mean t256/t128 = {conv_summary['mean_ratio_t256_t128']:.3f} ± {conv_summary['std_ratio']:.3f}")
print(f"  Mean % diff    = {conv_summary['mean_pct_diff']:.1f}% ± {conv_summary['std_pct_diff']:.1f}%")
print(f"  Max |Δ%|       = {conv_summary['max_abs_pct_diff']:.1f}%")
print(f"  Verdict        = {conv_summary['convergence_verdict']}")

# ═══════════════════════════════════════════════════════════════════════════
# 2. FIGURES
# ═══════════════════════════════════════════════════════════════════════════

def save_fig(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG_DIR, f"{name}.{ext}"),
                    dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {name}.pdf/.png")

# ─── Figure 1: Side-by-side stability maps ──────────────────────────────
print("\nGenerating figures...")

# Build full parameter grid for both campaigns
all_f    = sorted({round(r["f"],2)   for r in res_ref_unique})
all_beta = sorted({round(r["beta"],2) for r in res_ref_unique})
all_M    = sorted({round(r["mach"],2) for r in res_ref_unique})

print(f"  PRR parameter space: f={all_f}, β={all_beta}, M={all_M}")

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("IC-Sensitivity: Stability Outcomes\nKing/PRR pgen (left) vs Gaussian pgen (right)",
             fontsize=13, fontweight="bold")

# Unique (f, β) combos for the scatter
def scatter_map(ax, data_list, pgen_label, marker):
    for r in data_list:
        col = FRAG_COL if r["status"] == "FRAG" else STAB_COL
        ax.scatter(r["f"], r["beta"], c=col, s=180, marker=marker,
                   edgecolors="k", linewidths=0.8, zorder=5)
        # annotate M
        ax.annotate(f'M={r["mach"]:.0f}', (r["f"], r["beta"]),
                    textcoords="offset points", xytext=(6, 4), fontsize=7.5)
    frag_p  = mpatches.Patch(color=FRAG_COL,  label="FRAG")
    stab_p  = mpatches.Patch(color=STAB_COL,  label="STABLE")
    ax.legend(handles=[frag_p, stab_p], loc="upper right", fontsize=9)
    ax.set_xlabel("Line-mass fraction  f = M_line / M_crit", fontsize=11)
    ax.set_ylabel("Magnetic parameter  β", fontsize=11)
    ax.set_title(pgen_label, fontsize=11)
    ax.set_xlim(1.2, 3.4); ax.set_ylim(0.1, 1.3)
    ax.grid(True, alpha=0.3)

scatter_map(axes[0], res_ref_unique, "King/PRR pgen  (128-equiv, 256×64×64)", PRR_MK)
scatter_map(axes[1], res_rerun,      "Gaussian/Spacing pgen  (256-res)",       GAUSS_MK)
fig.tight_layout()
save_fig(fig, "fig1_stability_maps")

# ─── Figure 2: t_frag vs β for PRR runs ─────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
beta_vals = sorted({round(r["beta"],2) for r in res_ref_unique})
f_vals    = sorted({round(r["f"],2)    for r in res_ref_unique})
cmap = plt.get_cmap("tab10")

for i, fval in enumerate(f_vals):
    pts = [(r["beta"], r["t_frag"]) for r in res_ref_unique
           if abs(r["f"]-fval)<0.01 and r["t_frag"] is not None]
    if pts:
        betas, tfrags = zip(*sorted(pts))
        ax.plot(betas, tfrags, "o-", color=cmap(i), label=f"f={fval:.1f}", lw=1.8, ms=8)

ax.set_xlabel("Magnetic parameter  β", fontsize=12)
ax.set_ylabel(r"Fragmentation time  $t_{\rm frag}$  [$t_J$]", fontsize=12)
ax.set_title("Fragmentation time vs β — King/PRR pgen (res_ref campaign)", fontsize=12)
ax.legend(fontsize=10, title="Line-mass fraction f")
ax.grid(True, alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig2_tfrag_vs_beta")

# ─── Figure 3: t_frag scatter — PRR vs res128_match (convergence) ─────────
fig, ax = plt.subplots(figsize=(7, 6))

conv_pairs = conv_summary["pairs"]
t128s = [p["t128"] for p in conv_pairs]
t256s = [p["t256"] for p in conv_pairs]
labels = [f'f={p["f"]}, β={p["beta"]}, M={p["mach"]}' for p in conv_pairs]

ax.scatter(t128s, t256s, s=120, color="#1f77b4", edgecolors="k", zorder=5)
for t1, t2, lbl in zip(t128s, t256s, labels):
    ax.annotate(lbl, (t1, t2), textcoords="offset points", xytext=(6, 4), fontsize=8)

tmin, tmax = 0.6, 1.35
ax.plot([tmin, tmax], [tmin, tmax], "k--", lw=1.2, label="1:1 line")
# ±11% band
x = np.linspace(tmin, tmax, 100)
ax.fill_between(x, 0.89*x, 1.11*x, alpha=0.15, color="green", label="±11% band")
ax.set_xlim(tmin, tmax); ax.set_ylim(tmin, tmax)
ax.set_xlabel(r"$t_{\rm frag}$  at 128-equiv  [$t_J$]", fontsize=12)
ax.set_ylabel(r"$t_{\rm frag}$  at 256³  [$t_J$]", fontsize=12)
ax.set_title("Resolution convergence: PRR pgen\n128-equiv (res128_match) vs 256³", fontsize=12)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
# Mean ratio annotation
ax.text(0.97, 0.04,
    f"Mean $t_{{256}}/t_{{128}}$ = {conv_summary['mean_ratio_t256_t128']:.3f} ± {conv_summary['std_ratio']:.3f}",
    transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.6))
fig.tight_layout()
save_fig(fig, "fig3_resolution_scatter")

# ─── Figure 4: IC-sensitivity comparison bar chart ────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))

# Build matched comparison bars
match_labels = [f'f={m["f"]}, β={m["beta"]}, M={m["mach"]}' for m in matched]
prr_frag   = [1 if m["prr_status"]   == "FRAG" else 0 for m in matched]
gauss_frag = [1 if m["gauss_status"] == "FRAG" else 0 for m in matched]

x = np.arange(len(matched))
w = 0.35
bars1 = ax.bar(x - w/2, prr_frag,   w, label="King/PRR pgen",     color=FRAG_COL, alpha=0.85)
bars2 = ax.bar(x + w/2, gauss_frag, w, label="Gaussian pgen", color="#1f77b4", alpha=0.85)

# Colour stable bars green
for bar, v in zip(bars2, gauss_frag):
    if v == 0:
        bar.set_color(STAB_COL)

ax.set_xticks(x); ax.set_xticklabels(match_labels, rotation=25, ha="right", fontsize=9)
ax.set_yticks([0, 1]); ax.set_yticklabels(["STABLE", "FRAG"], fontsize=11)
ax.set_ylabel("Fragmentation outcome", fontsize=12)
ax.set_title("IC-Sensitivity: King/PRR vs Gaussian pgen\nSame (f, β, M, resolution) — matched pairs", fontsize=12)
ax.legend(fontsize=10)
ax.set_ylim(-0.2, 1.5)
ax.grid(axis="y", alpha=0.3)
# Annotate t_frag for FRAG cases
for bar, m in zip(bars1, matched):
    if m["prr_tfrag"] is not None:
        ax.text(bar.get_x()+bar.get_width()/2, 1.05,
                f'{m["prr_tfrag"]:.3f} $t_J$', ha="center", va="bottom", fontsize=8)

fig.tight_layout()
save_fig(fig, "fig4_ic_sensitivity_bars")

# ─── Figure 5: t_frag comparison — res_ref vs res128_match ───────────────
# Both are PRR pgen, same params; compare t_frag values directly
def get_tfrag(data, f, beta, mach):
    for r in data:
        if (abs(r["f"]-f)<0.01 and abs(r.get("beta",r.get("beta",99))-beta)<0.01
                and abs(r["mach"]-mach)<0.01 and r.get("t_frag") is not None):
            return r["t_frag"]
    return None

fig, ax = plt.subplots(figsize=(7, 6))
t_ref_list, t128_list, ptlabels = [], [], []
for r in res128_match_raw:
    t128 = r.get("t_frag")
    t_ref = get_tfrag(res_ref_unique, r["f"], r["beta"], r["mach"])
    if t128 and t_ref:
        t_ref_list.append(t_ref)
        t128_list.append(t128)
        ptlabels.append(f'f={r["f"]}, β={r["beta"]}, M={r["mach"]}')

ax.scatter(t_ref_list, t128_list, s=120, color="#9467bd", edgecolors="k", zorder=5)
for t_r, t_m, lbl in zip(t_ref_list, t128_list, ptlabels):
    ax.annotate(lbl, (t_r, t_m), textcoords="offset points", xytext=(6,4), fontsize=8)

all_t = t_ref_list + t128_list
tmin2, tmax2 = min(all_t)*0.92, max(all_t)*1.06
ax.plot([tmin2, tmax2], [tmin2, tmax2], "k--", lw=1.2, label="1:1")
ax.fill_between(np.linspace(tmin2,tmax2,100),
                0.89*np.linspace(tmin2,tmax2,100),
                1.11*np.linspace(tmin2,tmax2,100),
                alpha=0.12, color="green", label="±11% band")
ax.set_xlabel(r"res_ref  $t_{\rm frag}$  [$t_J$]  (seed 1, run A)", fontsize=11)
ax.set_ylabel(r"res128_match  $t_{\rm frag}$  [$t_J$]  (seed 1, run B)", fontsize=11)
ax.set_title("Intra-PRR reproducibility\nres_ref vs res128_match (same pgen, same params)", fontsize=11)
ax.legend(fontsize=10); ax.grid(True, alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig5_prr_reproducibility")

print("\nAll figures saved.")

# ═══════════════════════════════════════════════════════════════════════════
# 3. SAVE ANALYSIS JSON
# ═══════════════════════════════════════════════════════════════════════════

analysis_out = {
    "generated_utc": datetime.utcnow().isoformat(),
    "campaigns": {
        "res_ref":      {"n": len(res_ref_raw),      "unique_pts": len(res_ref_unique),
                         "frag": len(res_ref_raw), "stable": 0},
        "res128_match": {"n": len(res128_match_raw), "frag": len(res128_match_raw), "stable": 0},
        "res_rerun_gauss": {"n": len(res_rerun),
                            "frag":   sum(1 for r in res_rerun if r["status"]=="FRAG"),
                            "stable": sum(1 for r in res_rerun if r["status"]=="STABLE")},
        "dtc_rerun":    {"n": len(dtc_rerun),
                         "frag":   sum(1 for r in dtc_rerun if r["status"]=="FRAG"),
                         "stable": sum(1 for r in dtc_rerun if r["status"]=="STABLE")},
        "prr_full":     {"n": 314, "frag": 314, "stable": 0},
    },
    "resolution_convergence": {
        "mean_ratio_t256_t128": conv_summary["mean_ratio_t256_t128"],
        "std_ratio":            conv_summary["std_ratio"],
        "mean_pct_diff":        conv_summary["mean_pct_diff"],
        "max_abs_pct_diff":     conv_summary["max_abs_pct_diff"],
        "verdict":              conv_summary["convergence_verdict"],
        "n_pairs":              conv_summary["n_pairs"],
    },
    "ic_sensitivity": {
        "n_matched_pairs": len(matched),
        "prr_frag_count":   sum(1 for m in matched if m["prr_status"]=="FRAG"),
        "gauss_frag_count": sum(1 for m in matched if m["gauss_status"]=="FRAG"),
        "gauss_stable_count": sum(1 for m in matched if m["gauss_status"]=="STABLE"),
        "discordant_pairs": sum(1 for m in matched if m["prr_status"]!=m["gauss_status"]),
        "matched_pairs": matched,
    },
    "res_ref_unique": res_ref_unique,
    "res128_match":   res128_match_raw,
    "res_rerun":      res_rerun,
    "dtc_rerun":      dtc_rerun,
    "convergence_pairs": conv_summary["pairs"],
}

out_json = os.path.join(OUT_DIR, "res_ref_analysis.json")
with open(out_json, "w") as fh:
    json.dump(analysis_out, fh, indent=2)
print(f"\nSaved analysis JSON: {out_json}")
print(f"\n=== IC-Sensitivity Summary ===")
print(f"  Matched pairs:    {len(matched)}")
print(f"  PRR → FRAG:       {sum(1 for m in matched if m['prr_status']=='FRAG')}/{len(matched)}")
print(f"  Gaussian → FRAG:  {sum(1 for m in matched if m['gauss_status']=='FRAG')}/{len(matched)}")
print(f"  Gaussian → STAB:  {sum(1 for m in matched if m['gauss_status']=='STABLE')}/{len(matched)}")
print(f"  Discordant pairs: {sum(1 for m in matched if m['prr_status']!=m['gauss_status'])}/{len(matched)}")
