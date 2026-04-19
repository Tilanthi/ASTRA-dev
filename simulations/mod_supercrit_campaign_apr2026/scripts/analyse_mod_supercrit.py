#!/usr/bin/env python3
"""
Analysis script for Moderate Supercriticality Campaign — April 2026
5×5 grid: f ∈ {1.5, 2.0, 2.5, 3.0, 3.5} × M ∈ {1.0, 2.0, 3.0, 4.0, 5.0}
f = √(2/β)

Reads HDF5 snapshots from /home/fetch-agi/mod_supercrit/C4_mod_supercrit/
Outputs JSON + 5 figures to /home/fetch-agi/analysis_mod_supercrit/

Run on astra-climate after all sims complete.
"""

import os, sys, json, glob, math
import numpy as np

try:
    import h5py
except ImportError:
    os.system("pip install h5py -q"); import h5py

try:
    from scipy.signal import find_peaks
except ImportError:
    os.system("pip install scipy -q"); from scipy.signal import find_peaks

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ── Constants ────────────────────────────────────────────────────────
LAMBDA_J    = 1.0   # thermal Jeans wavelength (code units; 4πG=4π²=39.478)
RHO0        = 1.0   # background density
SEED_LAMBDA = 2.0   # seeded perturbation wavelength
F_CRIT      = math.sqrt(3.0)  # f_crit = √3 ≈ 1.732 (stability threshold)

BASEDIR = "/home/fetch-agi/mod_supercrit/C4_mod_supercrit"
OUTDIR  = "/home/fetch-agi/analysis_mod_supercrit"
os.makedirs(OUTDIR, exist_ok=True)

# ── Sim catalogue ────────────────────────────────────────────────────
f_values = [1.5, 2.0, 2.5, 3.0, 3.5]
M_values = [1.0, 2.0, 3.0, 4.0, 5.0]

sims = []
for f in f_values:
    beta = round(2.0 / f**2, 6)
    ftag = f"{f:.1f}".replace(".", "p")
    for mach in M_values:
        mtag = f"{mach:.1f}".replace(".", "p")
        sims.append(dict(
            run_id = f"MSC_f{ftag}_M{mtag}",
            f=f, beta=beta, mach=mach
        ))

print(f"Catalogue: {len(sims)} sims")


# ── HDF5 reader ──────────────────────────────────────────────────────
def read_athdf(fpath):
    """Return (time, rho_3d) where rho_3d.shape = (NX3, NX2, NX1)."""
    with h5py.File(fpath, "r") as fh:
        time = float(fh.attrs["Time"])
        cons = fh["cons"][()]
        locs = fh["LogicalLocations"][()]
        bs   = fh.attrs["MeshBlockSize"]
        gs   = fh.attrs["RootGridSize"]

    rho_blocks = cons[0]  # (nblock, nz, ny, nx)
    NX1, NX2, NX3 = int(gs[0]), int(gs[1]), int(gs[2])
    rho_3d = np.zeros((NX3, NX2, NX1), dtype=np.float32)

    for ib in range(rho_blocks.shape[0]):
        ix, iy, iz = int(locs[ib, 0]), int(locs[ib, 1]), int(locs[ib, 2])
        bx, by, bz = rho_blocks.shape[3], rho_blocks.shape[2], rho_blocks.shape[1]
        x1s, x2s, x3s = ix*bx, iy*by, iz*bz
        rho_3d[x3s:x3s+bz, x2s:x2s+by, x1s:x1s+bx] = rho_blocks[ib]

    dx = 16.0 / NX1
    x1 = np.arange(NX1) * dx - 8.0 + 0.5*dx
    return time, rho_3d, x1


# ── Analyse one simulation ────────────────────────────────────────────
def analyse_sim(s):
    rid    = s["run_id"]
    rundir = f"{BASEDIR}/{rid}"
    print(f"\n{'─'*60}")
    print(f"  {rid}  (f={s['f']:.1f}, β={s['beta']:.4f}, M={s['mach']:.1f})")

    hdf5_files = sorted(glob.glob(f"{rundir}/*.athdf"))
    if not hdf5_files:
        print(f"  WARNING: no HDF5 snapshots in {rundir}")
        return None
    print(f"  Found {len(hdf5_files)} snapshots")

    # C(t) curve
    times, C_vals = [], []
    for fpath in hdf5_files:
        try:
            t, rho3d, _ = read_athdf(fpath)
            times.append(t)
            C_vals.append(float(rho3d.max() / RHO0))
        except Exception as e:
            print(f"  WARN {os.path.basename(fpath)}: {e}")

    if not times:
        print("  ERROR: all snapshots unreadable")
        return None

    idx    = np.argsort(times)
    times  = np.array(times)[idx]
    C_vals = np.array(C_vals)[idx]
    print(f"  t: {times[0]:.2f} → {times[-1]:.2f},  C: {C_vals[0]:.3f} → {C_vals[-1]:.3f}")

    # Spatial analysis on last snapshot
    hdf5_sorted = [hdf5_files[i] for i in idx]
    rho3d_last, t_last, x1 = None, None, None
    for fpath in reversed(hdf5_sorted):
        try:
            t_last, rho3d_last, x1 = read_athdf(fpath)
            break
        except Exception:
            continue

    if rho3d_last is None:
        print("  ERROR: cannot read final snapshot")
        return None

    # 1-D profile
    rho1d = rho3d_last.mean(axis=(0, 1))  # average over y, z → shape (NX1,)

    mu    = rho1d.mean()
    sigma = rho1d.std()
    height_thresh = max(mu + 2.0*sigma, 1.1*mu)
    min_distance  = max(3, int(len(x1) * 0.03))

    peaks, _ = find_peaks(rho1d, height=height_thresh, distance=min_distance)
    if len(peaks) < 2:
        peaks, _ = find_peaks(rho1d, height=mu + 0.5*sigma, distance=min_distance)

    if len(peaks) >= 2:
        spacings  = np.abs(np.diff(x1[peaks]))
        lam_frag  = float(spacings.mean())
        lam_std   = float(spacings.std())
    elif len(peaks) == 1:
        lam_frag, lam_std = float("nan"), 0.0
    else:
        lam_frag, lam_std = float("nan"), 0.0

    ratio = lam_frag / LAMBDA_J if np.isfinite(lam_frag) else float("nan")
    print(f"  N_peaks={len(peaks)},  λ_frag={lam_frag:.3f}±{lam_std:.3f} λ_J  (ratio={ratio:.3f})")

    return dict(
        run_id=rid, f=s["f"], beta=s["beta"], mach=s["mach"],
        n_snapshots=len(times),
        t_final=float(times[-1]),
        C_initial=float(C_vals[0]), C_final=float(C_vals[-1]), C_max=float(C_vals.max()),
        n_peaks=int(len(peaks)),
        lambda_frag=lam_frag, lambda_frag_std=lam_std, lambda_J=LAMBDA_J,
        ratio_frag_J=ratio,
        times=times.tolist(), C_vals=C_vals.tolist(),
        rho1d_last=rho1d.tolist(), x1_coords=x1.tolist(),
        peak_indices=peaks.tolist(),
    )


# ── Run all sims ──────────────────────────────────────────────────────
results = []
for s in sims:
    r = analyse_sim(s)
    if r is not None:
        results.append(r)

print(f"\n{'='*60}")
print(f"Analysis complete: {len(results)}/{len(sims)} sims processed")

json_out = f"{OUTDIR}/mod_supercrit_analysis.json"
with open(json_out, "w") as fh:
    json.dump(results, fh, indent=2)
print(f"JSON saved: {json_out}")

if not results or not HAS_MPL:
    print("Skipping figures")
    sys.exit(0)


# ── Figures ───────────────────────────────────────────────────────────

# ── Fig 1: C(t) time series, one panel per f value ───────────────────
fig, axes = plt.subplots(1, len(f_values), figsize=(18, 4.5), sharey=True)
cmap = plt.cm.viridis(np.linspace(0.1, 0.9, len(M_values)))

for col, f_val in enumerate(f_values):
    ax = axes[col]
    for row, m_val in enumerate(M_values):
        rid = f"MSC_f{f'{f_val:.1f}'.replace('.','p')}_M{f'{m_val:.1f}'.replace('.','p')}"
        rset = [r for r in results if r["run_id"] == rid]
        if rset:
            r = rset[0]
            ax.semilogy(r["times"], r["C_vals"], color=cmap[row], lw=2, label=f"M={m_val:.1f}")
    ax.set_title(f"f={f_val:.1f}  (β={2.0/f_val**2:.3f})", fontsize=10)
    ax.set_xlabel("t [t_J]", fontsize=9)
    ax.grid(True, alpha=0.3)
    if col == 0:
        ax.set_ylabel("C = ρ_max/ρ₀", fontsize=9)
    ax.legend(fontsize=7)

plt.suptitle("Moderate Supercriticality Campaign: C(t) by f value, coloured by Mach number",
             fontsize=12, y=1.02)
plt.tight_layout()
fig.savefig(f"{OUTDIR}/fig1_Ct_by_f.png", dpi=150, bbox_inches="tight")
fig.savefig(f"{OUTDIR}/fig1_Ct_by_f.pdf", dpi=150, bbox_inches="tight")
plt.close(); print("Saved fig1")


# ── Fig 2: C_final heatmap (f vs M) ──────────────────────────────────
C_grid    = np.full((len(f_values), len(M_values)), np.nan)
Ncore_grid = np.full((len(f_values), len(M_values)), np.nan)

for i, f_val in enumerate(f_values):
    for j, m_val in enumerate(M_values):
        rid = f"MSC_f{f'{f_val:.1f}'.replace('.','p')}_M{f'{m_val:.1f}'.replace('.','p')}"
        rset = [r for r in results if r["run_id"] == rid]
        if rset:
            C_grid[i, j]     = rset[0]["C_final"]
            Ncore_grid[i, j] = rset[0]["n_peaks"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

im1 = ax1.imshow(np.log10(C_grid), aspect="auto", origin="lower",
                 cmap="hot", interpolation="nearest",
                 extent=[-0.5, len(M_values)-0.5, -0.5, len(f_values)-0.5])
ax1.set_xticks(range(len(M_values))); ax1.set_xticklabels([f"{m:.0f}" for m in M_values])
ax1.set_yticks(range(len(f_values))); ax1.set_yticklabels([f"{f:.1f}" for f in f_values])
ax1.set_xlabel("Mach number M", fontsize=11); ax1.set_ylabel("Mass-to-flux ratio f", fontsize=11)
ax1.set_title("log₁₀[C_final] at t=4 t_J", fontsize=11)
plt.colorbar(im1, ax=ax1, label="log₁₀(ρ_max/ρ₀)")
ax1.axhline(y=list(f_values).index(min(f_values, key=lambda x: abs(x - F_CRIT)))+0.5,
            color="cyan", ls="--", lw=1.5, label=f"f_crit≈{F_CRIT:.2f}")
for i, f_val in enumerate(f_values):
    for j, m_val in enumerate(M_values):
        if np.isfinite(C_grid[i, j]):
            ax1.text(j, i, f"{C_grid[i,j]:.1f}", ha="center", va="center",
                     fontsize=8, color="white", fontweight="bold")

im2 = ax2.imshow(Ncore_grid, aspect="auto", origin="lower",
                 cmap="Blues", interpolation="nearest",
                 extent=[-0.5, len(M_values)-0.5, -0.5, len(f_values)-0.5])
ax2.set_xticks(range(len(M_values))); ax2.set_xticklabels([f"{m:.0f}" for m in M_values])
ax2.set_yticks(range(len(f_values))); ax2.set_yticklabels([f"{f:.1f}" for f in f_values])
ax2.set_xlabel("Mach number M", fontsize=11); ax2.set_ylabel("Mass-to-flux ratio f", fontsize=11)
ax2.set_title("N_cores detected at t=4 t_J", fontsize=11)
plt.colorbar(im2, ax=ax2, label="N_peaks")
for i in range(len(f_values)):
    for j in range(len(M_values)):
        if np.isfinite(Ncore_grid[i, j]):
            ax2.text(j, i, f"{int(Ncore_grid[i,j])}", ha="center", va="center",
                     fontsize=10, color="navy", fontweight="bold")

plt.suptitle("Moderate Supercriticality Campaign — 5×5 f-M Grid", fontsize=13, y=1.02)
plt.tight_layout()
fig.savefig(f"{OUTDIR}/fig2_heatmaps.png", dpi=150, bbox_inches="tight")
fig.savefig(f"{OUTDIR}/fig2_heatmaps.pdf", dpi=150, bbox_inches="tight")
plt.close(); print("Saved fig2")


# ── Fig 3: C_final vs f for each M, and vs M for each f ──────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

for j, m_val in enumerate(M_values):
    col = plt.cm.viridis(j / max(1, len(M_values)-1))
    Cf = [C_grid[i, j] for i in range(len(f_values))]
    ax1.semilogy(f_values, Cf, "o-", color=col, lw=2, ms=7, label=f"M={m_val:.0f}")
ax1.axvline(x=F_CRIT, color="k", ls="--", lw=1.5, label=f"f_crit={F_CRIT:.2f}")
ax1.set_xlabel("Mass-to-flux ratio f = √(2/β)", fontsize=11)
ax1.set_ylabel("C_final = ρ_max/ρ₀  at  t=4 t_J", fontsize=11)
ax1.set_title("C_final vs f (coloured by Mach)", fontsize=11)
ax1.legend(fontsize=9); ax1.grid(True, alpha=0.3)

for i, f_val in enumerate(f_values):
    col = plt.cm.plasma(i / max(1, len(f_values)-1))
    Cm = [C_grid[i, j] for j in range(len(M_values))]
    ax2.semilogy(M_values, Cm, "o-", color=col, lw=2, ms=7, label=f"f={f_val:.1f}")
ax2.set_xlabel("Mach number M", fontsize=11)
ax2.set_ylabel("C_final = ρ_max/ρ₀  at  t=4 t_J", fontsize=11)
ax2.set_title("C_final vs M (coloured by f)", fontsize=11)
ax2.legend(fontsize=9); ax2.grid(True, alpha=0.3)

plt.suptitle("Moderate Supercriticality: Density Contrast Parameter Dependence", fontsize=12, y=1.02)
plt.tight_layout()
fig.savefig(f"{OUTDIR}/fig3_Cfinal_vs_params.png", dpi=150, bbox_inches="tight")
fig.savefig(f"{OUTDIR}/fig3_Cfinal_vs_params.pdf", dpi=150, bbox_inches="tight")
plt.close(); print("Saved fig3")


# ── Fig 4: 1-D density profiles at t=4 (5×5 grid) ──────────────────
fig, axes = plt.subplots(len(f_values), len(M_values),
                         figsize=(22, 4*len(f_values)), sharex=True)

for i, f_val in enumerate(f_values):
    for j, m_val in enumerate(M_values):
        ax = axes[i, j]
        rid = f"MSC_f{f'{f_val:.1f}'.replace('.','p')}_M{f'{m_val:.1f}'.replace('.','p')}"
        rset = [r for r in results if r["run_id"] == rid]
        if rset:
            r = rset[0]
            x1 = np.array(r["x1_coords"]); rho = np.array(r["rho1d_last"])
            ax.plot(x1, rho, "b-", lw=1.2)
            if r["peak_indices"]:
                pk = np.array(r["peak_indices"])
                ax.plot(x1[pk], rho[pk], "rv", ms=6, zorder=5)
            ax.set_title(f"f={f_val:.1f}, M={m_val:.0f}\nC={r['C_final']:.2f}, N={r['n_peaks']}",
                         fontsize=7)
        else:
            ax.text(0.5, 0.5, "NO DATA", transform=ax.transAxes,
                    ha="center", va="center", fontsize=8, color="red")
        ax.tick_params(labelsize=6)
        ax.grid(True, alpha=0.3)
        if j == 0:
            ax.set_ylabel("⟨ρ⟩", fontsize=7)
        if i == len(f_values)-1:
            ax.set_xlabel("x₁ [λ_J]", fontsize=7)

plt.suptitle("x₂,x₃-averaged density profiles at t = 4.0 t_J  (f-rows, M-columns)",
             fontsize=12, y=1.01)
plt.tight_layout()
fig.savefig(f"{OUTDIR}/fig4_density_profiles_5x5.png", dpi=120, bbox_inches="tight")
fig.savefig(f"{OUTDIR}/fig4_density_profiles_5x5.pdf", dpi=120, bbox_inches="tight")
plt.close(); print("Saved fig4")


# ── Fig 5: C_final vs f — comparison with β-sweep (M=3) ─────────────
# Load existing sweep results if available
sweep_json = "/home/fetch-agi/analysis_sweeps/sweep_analysis.json"
sweep_c12 = []
if os.path.exists(sweep_json):
    with open(sweep_json) as fh:
        sweep_results = json.load(fh)
    sweep_c12 = [r for r in sweep_results if r["campaign"] == "C1C2_beta_sweep"]
    print(f"  Loaded {len(sweep_c12)} sweep points for comparison")

fig, ax = plt.subplots(figsize=(9, 6))

# Sweep campaign M=3
if sweep_c12:
    fs_sweep = [math.sqrt(2.0/r["beta"]) for r in sweep_c12]
    Cs_sweep = [r["C_final"] for r in sweep_c12]
    ax.semilogy(fs_sweep, Cs_sweep, "ks--", ms=9, lw=1.5, label="β-sweep M=3 (prev.)", zorder=5)

# New campaign M=3 (j=2)
j_m3 = M_values.index(3.0)
Cf_m3 = [C_grid[i, j_m3] for i in range(len(f_values))]
ax.semilogy(f_values, Cf_m3, "ro-", ms=9, lw=2, label="MSC campaign M=3 (new)", zorder=6)

# All M values from new campaign
for j, m_val in enumerate(M_values):
    if m_val == 3.0:
        continue
    col = plt.cm.plasma(j / max(1, len(M_values)-1))
    Cf = [C_grid[i, j] for i in range(len(f_values))]
    ax.semilogy(f_values, Cf, "o-", color=col, lw=1.5, ms=6, label=f"MSC M={m_val:.0f}", alpha=0.7)

ax.axvline(x=F_CRIT, color="gray", ls="--", lw=2, label=f"f_crit = √3 ≈ {F_CRIT:.2f}")
ax.axvspan(f_values[0], F_CRIT, alpha=0.08, color="blue", label="Stabilised region (f<f_crit)")
ax.axvspan(F_CRIT, f_values[-1], alpha=0.08, color="red",  label="Supercritical (f>f_crit)")

ax.set_xlabel("Mass-to-flux ratio f = √(2/β)", fontsize=12)
ax.set_ylabel("C_final = ρ_max/ρ₀  at  t=4 t_J", fontsize=12)
ax.set_title("Moderate Supercriticality Regime: C_final vs f\n(compared to β-sweep at M=3)",
             fontsize=12)
ax.legend(fontsize=9, ncol=2); ax.grid(True, alpha=0.3)

plt.tight_layout()
fig.savefig(f"{OUTDIR}/fig5_Cfinal_vs_f_comparison.png", dpi=150, bbox_inches="tight")
fig.savefig(f"{OUTDIR}/fig5_Cfinal_vs_f_comparison.pdf", dpi=150, bbox_inches="tight")
plt.close(); print("Saved fig5")


# ── Summary table ─────────────────────────────────────────────────────
print(f"\n{'='*70}")
print(f"SUMMARY TABLE: C_final at t=4 t_J")
print(f"{'='*70}")
header = f"{'f':>6}  {'β':>8}  " + "  ".join([f"M={m:.0f}" for m in M_values])
print(header)
print("─" * len(header))
for i, f_val in enumerate(f_values):
    beta = 2.0 / f_val**2
    row = f"{f_val:>6.1f}  {beta:>8.4f}  "
    for j in range(len(M_values)):
        if np.isfinite(C_grid[i, j]):
            row += f"  {C_grid[i,j]:>6.2f}"
        else:
            row += f"  {'---':>6}"
    print(row)

print(f"\nAll figures and JSON saved to: {OUTDIR}")
print("Done.")
