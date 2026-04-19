#!/usr/bin/env python3
"""
analyse_transition_v2.py
========================
Analysis of the Transition Mapping V2 campaign (240 MHD simulations).

Maps the stability boundary in (f, β, M) space where:
  f  = mass-to-flux ratio (f > 1 = supercritical)
  β  = plasma beta
  M  = Mach number
  C  = clumping factor = <ρ²> / <ρ>²

Output directory: /home/fetch-agi/analysis_transition_v2/
Log file:         /home/fetch-agi/analyse_transition_v2.log

Figures generated:
  fig1_heatmap_M1.pdf   - C_final heatmap vs (f,β) for M=1
  fig2_heatmap_M2.pdf   - C_final heatmap vs (f,β) for M=2 + p1 overlay
  fig3_heatmap_M3.pdf   - C_final heatmap vs (f,β) for M=3
  fig4_timeseries.pdf   - C(t) time series for selected sims
  fig5_stability.pdf    - Stability boundary contours for M=1 and M=3

JSON: transition_v2_results.json
"""

import os
import sys
import re
import json
import glob
import logging
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import LogLocator, LogFormatter
import h5py
from datetime import datetime

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
SIM_BASE   = "/data/transition_mapping_v2/C5_transition_v2"
OUT_DIR    = "/home/fetch-agi/analysis_transition_v2"
LOG_FILE   = "/home/fetch-agi/analyse_transition_v2.log"

os.makedirs(OUT_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)

log.info("=" * 70)
log.info("analyse_transition_v2.py  —  started %s", datetime.utcnow().isoformat())
log.info("SIM_BASE : %s", SIM_BASE)
log.info("OUT_DIR  : %s", OUT_DIR)
log.info("=" * 70)

# Physical thresholds
F_CRIT   = np.sqrt(3.0)   # ≈ 1.732  gravitational threshold
BETA_CRIT = 2.0 / 3.0     # ≈ 0.667  magnetic threshold
C_THRESH  = 2.0            # clumping threshold for stability boundary

# Known collapsed sims (< 21 snapshots = physically collapsed)
COLLAPSED = {
    "TM2_f2p2_b1p3_M3p0_p0",
    "TM2_f2p2_b1p5_M1p0_p0",
    "TM2_f2p2_b1p5_M2p0_p0",
    "TM2_f2p2_b1p5_M3p0_p0",
    "TM2_f2p3_b0p5_M1p0_p0",
    "TM2_f2p3_b0p5_M2p0_p0",
    "TM2_f2p3_b0p5_M3p0_p0",
}

# ---------------------------------------------------------------------------
# HDF5 reader
# ---------------------------------------------------------------------------
def read_athdf(fpath):
    """Return (time, rho_3d) where rho_3d.shape = (NX3, NX2, NX1)."""
    with h5py.File(fpath, "r") as fh:
        time  = float(fh.attrs["Time"])
        cons  = fh["cons"][()]
        locs  = fh["LogicalLocations"][()]
        bs    = fh.attrs["MeshBlockSize"]
        gs    = fh.attrs["RootGridSize"]

    rho_blocks = cons[0]   # (nblock, nz, ny, nx)
    NX1 = int(gs[0]); NX2 = int(gs[1]); NX3 = int(gs[2])
    rho_3d = np.zeros((NX3, NX2, NX1), dtype=np.float32)

    for ib in range(rho_blocks.shape[0]):
        ix, iy, iz = int(locs[ib, 0]), int(locs[ib, 1]), int(locs[ib, 2])
        bx = rho_blocks.shape[3]; by = rho_blocks.shape[2]; bz = rho_blocks.shape[1]
        x1s = ix * bx; x2s = iy * by; x3s = iz * bz
        rho_3d[x3s:x3s+bz, x2s:x2s+by, x1s:x1s+bx] = rho_blocks[ib]
    return time, rho_3d


def clumping(rho):
    """Clumping factor C = <ρ²> / <ρ>²."""
    r = rho.astype(np.float64)
    return float(np.mean(r * r) / (np.mean(r) ** 2))


# ---------------------------------------------------------------------------
# Directory / parameter parsing
# ---------------------------------------------------------------------------
_TAG_RE = re.compile(
    r"TM2_f(\d+p\d+)_b(\d+p\d+)_M(\d+p\d+)_p(\d+)$"
)

def parse_simname(name):
    """Return dict with f, beta, M, phase or None."""
    m = _TAG_RE.match(name)
    if m is None:
        return None
    f     = float(m.group(1).replace("p", "."))
    beta  = float(m.group(2).replace("p", "."))
    mach  = float(m.group(3).replace("p", "."))
    phase = int(m.group(4))
    return dict(f=f, beta=beta, mach=mach, phase=phase)


def get_snapshots(simdir, simname):
    """Return sorted list of HDF5 snapshot paths."""
    pattern = os.path.join(simdir, f"{simname}.out.?????.athdf")
    snaps = sorted(glob.glob(pattern))
    return snaps


# ---------------------------------------------------------------------------
# Main data collection loop
# ---------------------------------------------------------------------------
log.info("Scanning simulation directories …")

sim_dirs = sorted(d for d in os.listdir(SIM_BASE)
                  if os.path.isdir(os.path.join(SIM_BASE, d)) and d.startswith("TM2_"))

log.info("Found %d simulation directories", len(sim_dirs))

results = {}   # simname → {f, beta, mach, phase, C_final, last_t, n_snaps, collapsed}

for simname in sim_dirs:
    pars = parse_simname(simname)
    if pars is None:
        log.warning("Cannot parse simname: %s  — skipping", simname)
        continue

    simdir = os.path.join(SIM_BASE, simname)
    snaps  = get_snapshots(simdir, simname)

    if not snaps:
        log.warning("%s: no snapshots found — skipping", simname)
        continue

    # Read last snapshot only for C_final
    last_snap = snaps[-1]
    try:
        time_last, rho_last = read_athdf(last_snap)
        C_final = clumping(rho_last)
    except Exception as exc:
        log.error("%s: failed reading %s: %s", simname, last_snap, exc)
        C_final = float("nan")
        time_last = float("nan")

    is_collapsed = (simname in COLLAPSED) or (len(snaps) < 21)

    results[simname] = dict(
        f        = pars["f"],
        beta     = pars["beta"],
        mach     = pars["mach"],
        phase    = pars["phase"],
        C_final  = round(C_final, 4),
        last_t   = round(time_last, 4),
        n_snaps  = len(snaps),
        collapsed= is_collapsed,
        fragmented = (C_final >= C_THRESH),
    )

log.info("Processed %d simulations", len(results))

# Quick summary
n_collapsed  = sum(1 for r in results.values() if r["collapsed"])
n_fragmented = sum(1 for r in results.values() if r["fragmented"] and not r["collapsed"])
log.info("  Collapsed  (< 21 snaps): %d", n_collapsed)
log.info("  Fragmented (C ≥ %.1f):   %d", C_THRESH, n_fragmented)
log.info("  Stable     (C <  %.1f):  %d", C_THRESH,
         len(results) - n_collapsed - n_fragmented)

# Print a few representative values
for label, sname in [("f=1.5 β=0.5 M=2 (subcrit)", "TM2_f1p5_b0p5_M2p0_p0"),
                     ("f=2.0 β=0.9 M=2 (near trans)", "TM2_f2p0_b0p9_M2p0_p0"),
                     ("f=2.5 β=0.9 M=2 (supercrit)",  "TM2_f2p5_b0p9_M2p0_p0"),
                     ("f=2.3 β=0.5 M=3 (collapsed)",  "TM2_f2p3_b0p5_M3p0_p0")]:
    if sname in results:
        r = results[sname]
        log.info("  %-35s  C_final=%.3f  t_last=%.3f  collapsed=%s",
                 label, r["C_final"], r["last_t"], r["collapsed"])

# ---------------------------------------------------------------------------
# Time-series data for Figure 4  (read ALL snapshots for selected sims)
# ---------------------------------------------------------------------------
TS_SIMS = [
    ("TM2_f1p5_b0p5_M2p0_p0",  "f=1.5 β=0.5 M=2 (subcrit)"),
    ("TM2_f2p0_b0p9_M2p0_p0",  "f=2.0 β=0.9 M=2 (near trans)"),
    ("TM2_f2p5_b0p9_M2p0_p0",  "f=2.5 β=0.9 M=2 (supercrit)"),
    ("TM2_f2p3_b0p7_M2p0_p0",  "f=2.3 β=0.7 M=2 p0 (trans zone)"),
    ("TM2_f2p3_b0p7_M2p0_p1",  "f=2.3 β=0.7 M=2 p1 (alt seed)"),
    ("TM2_f2p3_b0p5_M3p0_p0",  "f=2.3 β=0.5 M=3 (collapsed)"),
]

timeseries = {}   # simname → (times_arr, C_arr)

log.info("Reading time series for %d selected sims …", len(TS_SIMS))
for simname, label in TS_SIMS:
    simdir = os.path.join(SIM_BASE, simname)
    snaps  = get_snapshots(simdir, simname)
    if not snaps:
        log.warning("  %s: no snapshots — skipping time series", simname)
        continue
    times = []; cvals = []
    for snap in snaps:
        try:
            t, rho = read_athdf(snap)
            times.append(t); cvals.append(clumping(rho))
        except Exception as exc:
            log.error("  %s snap %s: %s", simname, snap, exc)
    if times:
        timeseries[simname] = (np.array(times), np.array(cvals))
        log.info("  %s: %d snaps, C_final=%.3f, t_final=%.3f",
                 simname, len(times), cvals[-1], times[-1])

# ---------------------------------------------------------------------------
# Helper: build 2D grid for heatmap
# ---------------------------------------------------------------------------
F_VALS = [1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5]
B_VALS = [0.5, 0.7, 0.9, 1.1, 1.3, 1.5]

def make_grid(mach, phase=0):
    """Return (C_grid, collapse_grid) arrays shape (len(F_VALS), len(B_VALS))."""
    C_grid  = np.full((len(F_VALS), len(B_VALS)), np.nan)
    col_grid= np.zeros((len(F_VALS), len(B_VALS)), dtype=bool)
    for i, f in enumerate(F_VALS):
        for j, b in enumerate(B_VALS):
            # Build expected simname
            ftag = f"{f:.1f}".replace(".", "p")
            btag = f"{b:.1f}".replace(".", "p")
            mtag = f"{mach:.1f}".replace(".", "p")
            sname = f"TM2_f{ftag}_b{btag}_M{mtag}_p{phase}"
            if sname in results:
                r = results[sname]
                C_grid[i, j]  = r["C_final"]
                col_grid[i, j]= r["collapsed"]
    return C_grid, col_grid


# ---------------------------------------------------------------------------
# Color map for C values (log-stretched, 1→30)
# ---------------------------------------------------------------------------
CMAP = "plasma"
C_VMIN, C_VMAX = 1.0, 25.0
NORM = mcolors.LogNorm(vmin=C_VMIN, vmax=C_VMAX)

# ---------------------------------------------------------------------------
# Figure 1 — Heatmap M=1
# ---------------------------------------------------------------------------
log.info("Generating Figure 1: heatmap M=1 …")

fig, ax = plt.subplots(figsize=(9, 6))
C1, col1 = make_grid(1.0, 0)

im = ax.imshow(C1.T, origin="lower", aspect="auto",
               extent=[min(F_VALS)-0.05, max(F_VALS)+0.05,
                       min(B_VALS)-0.1,  max(B_VALS)+0.1],
               norm=NORM, cmap=CMAP, interpolation="nearest")

# Mark collapsed
for i, f in enumerate(F_VALS):
    for j, b in enumerate(B_VALS):
        if col1[i, j]:
            ax.plot(f, b, 'x', color='white', ms=14, mew=3, zorder=5)
            ax.plot(f, b, 'x', color='black', ms=12, mew=2, zorder=6)

# Annotate C values
for i, f in enumerate(F_VALS):
    for j, b in enumerate(B_VALS):
        if not np.isnan(C1[i, j]):
            txt = f"{C1[i,j]:.1f}"
            ax.text(f, b, txt, ha='center', va='center', fontsize=7,
                    color='white' if C1[i,j] > 3 else 'black', fontweight='bold')

cbar = plt.colorbar(im, ax=ax, label="Clumping factor C = ⟨ρ²⟩/⟨ρ⟩²")
ax.axvline(F_CRIT, color='cyan', ls='--', lw=2, label=f"f_crit = √3 ≈ {F_CRIT:.3f}")
ax.axhline(BETA_CRIT, color='lime', ls='--', lw=2, label=f"β_crit = 2/3 ≈ {BETA_CRIT:.3f}")
ax.set_xlabel("Mass-to-flux ratio f", fontsize=12)
ax.set_ylabel("Plasma β", fontsize=12)
ax.set_title("Transition Mapping V2 — M = 1.0\nC_final (log colour); ✕ = physically collapsed", fontsize=11)
ax.legend(loc='upper left', fontsize=9)
ax.set_xticks(F_VALS)
ax.set_yticks(B_VALS)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "fig1_heatmap_M1.pdf"), dpi=150)
fig.savefig(os.path.join(OUT_DIR, "fig1_heatmap_M1.png"), dpi=150)
plt.close(fig)
log.info("  Saved fig1_heatmap_M1.pdf/.png")

# ---------------------------------------------------------------------------
# Figure 2 — Heatmap M=2  +  p1 overlay
# ---------------------------------------------------------------------------
log.info("Generating Figure 2: heatmap M=2 + p1 overlay …")

fig, ax = plt.subplots(figsize=(9, 6))
C2, col2 = make_grid(2.0, 0)

im = ax.imshow(C2.T, origin="lower", aspect="auto",
               extent=[min(F_VALS)-0.05, max(F_VALS)+0.05,
                       min(B_VALS)-0.1,  max(B_VALS)+0.1],
               norm=NORM, cmap=CMAP, interpolation="nearest")

# Mark collapsed p0
for i, f in enumerate(F_VALS):
    for j, b in enumerate(B_VALS):
        if col2[i, j]:
            ax.plot(f, b, 'x', color='white', ms=14, mew=3, zorder=5)
            ax.plot(f, b, 'x', color='black', ms=12, mew=2, zorder=6)

# Annotate p0 C values
for i, f in enumerate(F_VALS):
    for j, b in enumerate(B_VALS):
        if not np.isnan(C2[i, j]):
            ax.text(f, b - 0.07, f"{C2[i,j]:.1f}", ha='center', va='center',
                    fontsize=6, color='white' if C2[i,j] > 3 else 'black',
                    style='normal', fontweight='bold')

# Overlay p1 sims as small circles for transition zone
TRANS_F = [1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3]
for f in TRANS_F:
    for b in B_VALS:
        ftag = f"{f:.1f}".replace(".", "p")
        btag = f"{b:.1f}".replace(".", "p")
        sname = f"TM2_f{ftag}_b{btag}_M2p0_p1"
        if sname in results:
            C_p1 = results[sname]["C_final"]
            norm_val = np.clip((np.log10(C_p1) - np.log10(C_VMIN)) /
                               (np.log10(C_VMAX) - np.log10(C_VMIN)), 0, 1)
            color = plt.cm.plasma(norm_val)
            ax.scatter(f, b + 0.12, s=60, c=[color], edgecolors='white',
                       linewidths=1.0, zorder=7, marker='o')
            ax.text(f, b + 0.18, f"{C_p1:.1f}", ha='center', va='bottom',
                    fontsize=5.5, color='yellow', fontstyle='italic')

cbar = plt.colorbar(im, ax=ax, label="Clumping factor C = ⟨ρ²⟩/⟨ρ⟩²")
ax.axvline(F_CRIT, color='cyan', ls='--', lw=2, label=f"f_crit = √3 ≈ {F_CRIT:.3f}")
ax.axhline(BETA_CRIT, color='lime', ls='--', lw=2, label=f"β_crit = 2/3 ≈ {BETA_CRIT:.3f}")
ax.set_xlabel("Mass-to-flux ratio f", fontsize=12)
ax.set_ylabel("Plasma β", fontsize=12)
ax.set_title(
    "Transition Mapping V2 — M = 2.0\n"
    "Main grid (p0, square tiles) + transition zone second seeds (p1, small circles)",
    fontsize=11)
ax.legend(loc='upper left', fontsize=9)
ax.set_xticks(F_VALS)
ax.set_yticks(B_VALS)

# Add legend patch for p1 overlay
from matplotlib.patches import Patch, Circle
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='cyan',  ls='--', lw=2, label=f"f_crit = √3 ≈ {F_CRIT:.3f}"),
    Line2D([0], [0], color='lime',  ls='--', lw=2, label=f"β_crit = 2/3 ≈ {BETA_CRIT:.3f}"),
    Line2D([0], [0], marker='x',    color='k', ms=10, mew=2, ls='none', label="Collapsed"),
    Line2D([0], [0], marker='o',    color='yellow', ms=6, ls='none',
           markeredgecolor='white', label="p1 extra seed"),
]
ax.legend(handles=legend_elements, loc='upper left', fontsize=9)

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "fig2_heatmap_M2.pdf"), dpi=150)
fig.savefig(os.path.join(OUT_DIR, "fig2_heatmap_M2.png"), dpi=150)
plt.close(fig)
log.info("  Saved fig2_heatmap_M2.pdf/.png")

# ---------------------------------------------------------------------------
# Figure 3 — Heatmap M=3
# ---------------------------------------------------------------------------
log.info("Generating Figure 3: heatmap M=3 …")

fig, ax = plt.subplots(figsize=(9, 6))
C3, col3 = make_grid(3.0, 0)

im = ax.imshow(C3.T, origin="lower", aspect="auto",
               extent=[min(F_VALS)-0.05, max(F_VALS)+0.05,
                       min(B_VALS)-0.1,  max(B_VALS)+0.1],
               norm=NORM, cmap=CMAP, interpolation="nearest")

for i, f in enumerate(F_VALS):
    for j, b in enumerate(B_VALS):
        if col3[i, j]:
            ax.plot(f, b, 'x', color='white', ms=14, mew=3, zorder=5)
            ax.plot(f, b, 'x', color='black', ms=12, mew=2, zorder=6)
        if not np.isnan(C3[i, j]):
            ax.text(f, b, f"{C3[i,j]:.1f}", ha='center', va='center',
                    fontsize=7, color='white' if C3[i,j] > 3 else 'black',
                    fontweight='bold')

cbar = plt.colorbar(im, ax=ax, label="Clumping factor C = ⟨ρ²⟩/⟨ρ⟩²")
ax.axvline(F_CRIT, color='cyan', ls='--', lw=2, label=f"f_crit = √3 ≈ {F_CRIT:.3f}")
ax.axhline(BETA_CRIT, color='lime', ls='--', lw=2, label=f"β_crit = 2/3 ≈ {BETA_CRIT:.3f}")
ax.set_xlabel("Mass-to-flux ratio f", fontsize=12)
ax.set_ylabel("Plasma β", fontsize=12)
ax.set_title("Transition Mapping V2 — M = 3.0\nC_final (log colour); ✕ = physically collapsed", fontsize=11)
ax.legend(loc='upper left', fontsize=9)
ax.set_xticks(F_VALS)
ax.set_yticks(B_VALS)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "fig3_heatmap_M3.pdf"), dpi=150)
fig.savefig(os.path.join(OUT_DIR, "fig3_heatmap_M3.png"), dpi=150)
plt.close(fig)
log.info("  Saved fig3_heatmap_M3.pdf/.png")

# ---------------------------------------------------------------------------
# Figure 4 — C(t) time series
# ---------------------------------------------------------------------------
log.info("Generating Figure 4: C(t) time series …")

COLORS_TS = ['#4c72b0', '#dd8452', '#55a868', '#c44e52', '#8172b3', '#937860']
STYLES    = ['-', '--', '-.', ':', '-', '--']

fig, ax = plt.subplots(figsize=(10, 6))

for idx, (simname, label) in enumerate(TS_SIMS):
    if simname not in timeseries:
        log.warning("  No time-series data for %s", simname)
        continue
    times, cvals = timeseries[simname]
    col = COLORS_TS[idx % len(COLORS_TS)]
    sty = STYLES[idx % len(STYLES)]
    lw  = 2.5 if "collapsed" in label else 1.8
    ax.plot(times, cvals, color=col, ls=sty, lw=lw,
            marker='o', ms=4, markevery=2, label=label)

ax.axhline(C_THRESH, color='gray', ls=':', lw=1.5,
           label=f"C_thresh = {C_THRESH:.1f} (fragmentation boundary)")
ax.axhline(1.0, color='black', ls='-', lw=0.8, alpha=0.4)
ax.set_xlabel("Time t  [t_J]", fontsize=12)
ax.set_ylabel("Clumping factor C = ⟨ρ²⟩/⟨ρ⟩²", fontsize=12)
ax.set_title("Transition Mapping V2 — C(t) evolution for selected simulations", fontsize=11)
ax.legend(loc='upper left', fontsize=9, framealpha=0.85)
ax.set_yscale("log")
ax.grid(True, which='both', alpha=0.3)
ax.set_ylim(bottom=0.9)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "fig4_timeseries.pdf"), dpi=150)
fig.savefig(os.path.join(OUT_DIR, "fig4_timeseries.png"), dpi=150)
plt.close(fig)
log.info("  Saved fig4_timeseries.pdf/.png")

# ---------------------------------------------------------------------------
# Figure 5 — Stability boundary  (C_final = C_THRESH contour)
# ---------------------------------------------------------------------------
log.info("Generating Figure 5: stability boundary …")

from scipy.interpolate import griddata

# Build dense interpolation grids for M=1 and M=3
F_FINE = np.linspace(1.5, 2.5, 100)
B_FINE = np.linspace(0.5, 1.5, 100)
FF, BB = np.meshgrid(F_FINE, B_FINE)

def interpolated_C(mach):
    """Interpolate C_final onto fine grid for a given Mach number."""
    points = []; values = []
    for r in results.values():
        if r["mach"] == mach and r["phase"] == 0:
            if not np.isnan(r["C_final"]):
                points.append([r["f"], r["beta"]])
                # Collapsed sims → assign a large C to indicate supercritical
                val = r["C_final"] if not r["collapsed"] else 30.0
                values.append(val)
    if len(points) < 3:
        return None
    pts = np.array(points); vals = np.array(values)
    C_interp = griddata(pts, vals, (FF, BB), method='linear')
    return C_interp

fig, ax = plt.subplots(figsize=(9, 6))

for mach, color, label in [(1.0, '#2196F3', 'M=1.0'), (3.0, '#F44336', 'M=3.0')]:
    C_interp = interpolated_C(mach)
    if C_interp is None:
        log.warning("  Not enough data for M=%.1f interpolation", mach)
        continue
    # Contour at C_THRESH
    try:
        cs = ax.contour(FF, BB, C_interp, levels=[C_THRESH],
                        colors=[color], linewidths=2.5)
        ax.clabel(cs, fmt=f"C={C_THRESH:.0f} (M={mach:.0f})", fontsize=8)
        # Shaded region above threshold
        ax.contourf(FF, BB, C_interp, levels=[C_THRESH, 1e6],
                    alpha=0.12, colors=[color])
    except Exception as exc:
        log.warning("  Contour plot for M=%.1f failed: %s", mach, exc)

# Theoretical thresholds
ax.axvline(F_CRIT, color='cyan', ls='--', lw=2, label=f"f_crit = √3 ≈ {F_CRIT:.3f}")
ax.axhline(BETA_CRIT, color='lime', ls='--', lw=2, label=f"β_crit = 2/3 ≈ {BETA_CRIT:.3f}")

# Theoretical stability curve: f_crit(β) = √3 × √(1 + 2/β) / √3   (rough approximation)
# Simple: f threshold grows as β decreases (magnetic support)
# From linear MHD: λ_J,eff decreases with β → f_crit(β) ≈ √(1 + (4/3)·(1/(β·π²)))
# Actually we let the data speak; add a rough analytic curve for guidance
beta_theory = np.linspace(0.4, 1.6, 200)
# Rough: f_crit ≈ √3 at large β, increases at small β (magnetic suppression needs larger f)
f_crit_theory = np.sqrt(3) * np.sqrt(1.0 + (2.0 / (3.0 * beta_theory)))
ax.plot(f_crit_theory, beta_theory, 'k-', lw=1.5, alpha=0.6,
        label="Theoretical f_crit(β)  [approx]")

# Mark data points
for mach, marker, col in [(1.0, 's', '#2196F3'), (3.0, '^', '#F44336')]:
    for r in results.values():
        if r["mach"] == mach and r["phase"] == 0:
            mfc = col if r["fragmented"] or r["collapsed"] else 'none'
            ms  = 12 if r["collapsed"] else 6
            ax.plot(r["f"], r["beta"], marker=marker, color=col,
                    mfc=mfc, ms=ms, mew=1.5, zorder=4, alpha=0.7)

# Legend
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
legend_elements = [
    Line2D([0],[0], color='#2196F3', lw=2.5, label=f"C={C_THRESH:.0f} boundary M=1"),
    Line2D([0],[0], color='#F44336', lw=2.5, label=f"C={C_THRESH:.0f} boundary M=3"),
    Patch(facecolor='#2196F3', alpha=0.15, label="Fragmented (M=1)"),
    Patch(facecolor='#F44336', alpha=0.15, label="Fragmented (M=3)"),
    Line2D([0],[0], color='cyan',  ls='--', lw=2, label=f"f_crit = √3 ≈ {F_CRIT:.3f}"),
    Line2D([0],[0], color='lime',  ls='--', lw=2, label=f"β_crit = 2/3 ≈ {BETA_CRIT:.3f}"),
    Line2D([0],[0], color='k',     ls='-',  lw=1.5, alpha=0.6, label="Theoretical f_crit(β)"),
    Line2D([0],[0], marker='s', color='#2196F3', ms=6, ls='none',
           mfc='#2196F3', label="Fragmented sim (M=1)"),
    Line2D([0],[0], marker='s', color='#2196F3', ms=6, ls='none',
           mfc='none', label="Stable sim (M=1)"),
    Line2D([0],[0], marker='^', color='#F44336', ms=6, ls='none',
           mfc='#F44336', label="Fragmented sim (M=3)"),
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=8, framealpha=0.9,
          ncol=2)

ax.set_xlabel("Mass-to-flux ratio f", fontsize=12)
ax.set_ylabel("Plasma β", fontsize=12)
ax.set_title(
    "Transition Mapping V2 — Stability boundary\n"
    f"Contour: C_final = {C_THRESH:.1f} for M=1 (blue) and M=3 (red)\n"
    "Filled region = fragmented; higher M shifts boundary to lower f",
    fontsize=10)
ax.set_xlim(1.45, 2.55)
ax.set_ylim(0.40, 1.60)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "fig5_stability_boundary.pdf"), dpi=150)
fig.savefig(os.path.join(OUT_DIR, "fig5_stability_boundary.png"), dpi=150)
plt.close(fig)
log.info("  Saved fig5_stability_boundary.pdf/.png")

# ---------------------------------------------------------------------------
# Save JSON results
# ---------------------------------------------------------------------------
log.info("Saving JSON …")

json_out = dict(
    run_timestamp  = datetime.utcnow().isoformat(),
    campaign       = "Transition Mapping V2",
    n_sims         = len(results),
    n_collapsed    = n_collapsed,
    n_fragmented   = n_fragmented,
    c_threshold    = C_THRESH,
    f_crit_theory  = round(F_CRIT, 6),
    beta_crit_theory = round(BETA_CRIT, 6),
    simulations    = results,
)

json_path = os.path.join(OUT_DIR, "transition_v2_results.json")
with open(json_path, "w") as fj:
    json.dump(json_out, fj, indent=2)
log.info("  Saved %s (%.1f KB)", json_path, os.path.getsize(json_path) / 1024)

# ---------------------------------------------------------------------------
# Summary statistics per M value
# ---------------------------------------------------------------------------
log.info("")
log.info("=" * 60)
log.info("SUMMARY STATISTICS")
log.info("=" * 60)
for mach in [1.0, 2.0, 3.0]:
    subset = [r for r in results.values() if r["mach"] == mach and r["phase"] == 0]
    n_frag = sum(1 for r in subset if r["fragmented"] or r["collapsed"])
    n_stab = sum(1 for r in subset if not r["fragmented"] and not r["collapsed"])
    C_vals = [r["C_final"] for r in subset if not np.isnan(r["C_final"])]
    log.info("  M=%.1f: %d fragmented, %d stable, C_final range=[%.2f, %.2f]",
             mach, n_frag, n_stab, min(C_vals), max(C_vals))

# Print boundary sims: highest f in each (M, β) that is still stable
log.info("")
log.info("Stability boundary (last stable f at each β for M=1 and M=3):")
for mach in [1.0, 3.0]:
    log.info("  M=%.1f:", mach)
    for b in B_VALS:
        stable_fs = [r["f"] for r in results.values()
                     if r["mach"] == mach and r["beta"] == b
                     and r["phase"] == 0 and not r["fragmented"] and not r["collapsed"]]
        frag_fs   = [r["f"] for r in results.values()
                     if r["mach"] == mach and r["beta"] == b
                     and r["phase"] == 0 and (r["fragmented"] or r["collapsed"])]
        f_max_stab = max(stable_fs) if stable_fs else "none"
        f_min_frag = min(frag_fs)   if frag_fs   else "none"
        log.info("    β=%.1f:  last stable f=%-5s  first fragmented f=%s",
                 b, f_max_stab, f_min_frag)

log.info("")
log.info("=" * 60)
log.info("Analysis complete.  Outputs in %s", OUT_DIR)
log.info("Figures: fig1_heatmap_M1, fig2_heatmap_M2, fig3_heatmap_M3,")
log.info("         fig4_timeseries, fig5_stability_boundary")
log.info("JSON:    transition_v2_results.json")
log.info("=" * 60)
