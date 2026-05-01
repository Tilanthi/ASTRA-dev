#!/usr/bin/env python3
"""
Step 4: Write standalone DTC campaign report.
Reads analysis results and writes a comprehensive Markdown report.
"""
import json, os
from datetime import datetime

SIMBASE = "/data/dtc_runs"
RESULTS = os.path.join(SIMBASE, "dtc_analysis_results.json")
REPORT  = os.path.join(SIMBASE, "DTC_CAMPAIGN_REPORT_Apr2026.md")

with open(RESULTS) as f:
    data = json.load(f)

s   = data["summary"]
pt  = data["p_frag_table"]
bct = data["beta_crit_table"]
sims = data["sim_results"]

f_vals    = s["f_values"]
beta_vals = s["beta_values"]
mach_vals = s["mach_values"]

def pfrag_cell(mach, fv, beta):
    for p in pt:
        if abs(p["mach"]-mach)<0.05 and abs(p["f"]-fv)<0.05 and abs(p["beta"]-beta)<0.05:
            pf = p["P_frag"]
            if pf == 0:    return "✅"
            elif pf == 1:  return "❌"
            else:          return "◆"
    return "—"

def beta_crit_str(mach, fv):
    for b in bct:
        if abs(b["mach"]-mach)<0.05 and abs(b["f"]-fv)<0.05:
            bc = b["beta_crit"]
            ct = b["crit_type"]
            if bc is None: return "N/A"
            tag = "" if ct == "interpolated" else (" (<grid)" if ct == "below_grid" else " (>grid)")
            return f"{bc:.2f}{tag}"
    return "N/A"

# Stats by mach
mach_stats = {}
for mach in mach_vals:
    rows = [r for r in sims if abs(r["mach"]-mach)<0.05]
    nf = sum(1 for r in rows if r["fragmented"])
    mach_stats[mach] = {"n": len(rows), "nf": nf, "no": len(rows)-nf}

# Stochastic points
n_stoch = sum(1 for p in pt if p["stochastic"])
stoch_list = sorted([p for p in pt if p["stochastic"]], key=lambda x: (x["mach"], x["f"], x["beta"]))

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

report = f"""# DTC Campaign Report — April 2026
## Definitive Transition Campaign: Fragmentation Boundary Mapping
### Longitudinal Magnetic Field — Isothermal MHD Filament Simulations

**Generated**: {now}  
**Code**: Athena++ (isothermal MHD + FFT self-gravity, HLLD flux)  
**Server**: astra-climate (224 vCPUs, AMD EPYC 7B13, GCE)  
**Authors**: ASTRA System / Glenn J. White (Open University)

---

## 1. Campaign Overview

The Definitive Transition Campaign (DTC) maps the 2D fragmentation transition boundary
in the (f, β) parameter space of isothermal self-gravitating MHD filaments with a
**longitudinal magnetic field** (B along the filament axis, x1 direction).

### Physical Setup
- **Filament profile**: Gaussian, σ = 1.0 λ_J, peak density ρ_c = 2f·c_s²/(√(2π)·G)
- **B-field geometry**: **Longitudinal** (B₀ₓ along x1 — filament axis)
- **B₀ₓ formula**: B₀ₓ = c_s·√(2ρ_c/β) → Alfvén speed v_A = c_s·√(2/β), **independent of f**
- **Turbulence**: x1-only Kolmogorov perturbations (8 modes), RMS v₁ = M·pfrac·c_s (pfrac=0.05)
- **Grid**: 128³ cells, domain 16×4×4 λ_J, 32³ meshblocks (64 per sim)
- **Time limit**: t_lim = 1.5 t_J (stops before isothermal density singularity)
- **Timeout**: 600s wall time → classified as FRAG (density divergence = fragmentation)
- **Code units**: c_s=1, G_code=0.20977 (four_pi_G=2.636), ρ_bg=1.0

### Grid Parameters
| Parameter | Values |
|-----------|--------|
| f (line-mass/critical) | {", ".join(f"{v:.1f}" for v in f_vals)} |
| β (thermal/magnetic pressure) | {", ".join(f"{v:.1f}" for v in beta_vals)} |
| M (Mach number) | {", ".join(f"{v:.0f}" for v in mach_vals)} |
| Seeds | {", ".join(str(s2) for s2 in s["seeds"])} |
| **Total simulations** | **{s["n_total"]}** |

---

## 2. Campaign Execution

### Timeline
- **Primary phase (M=1,2,3)**: 13:59 → 22:00 UTC, 20 April 2026 (8.01 hr, 323 sims)
- **Extended phase (M=4,5)**: 22:03 UTC Apr 20 → 04:03 UTC Apr 21 (6.00 hr, 216 sims)
- **Total wall time**: ~14 hours on 192 cores (6 concurrent × 32 MPI ranks)
- **Effective throughput**: 41–47 sims/hr (primary), 36 sims/hr (extended, ~100% FRAG)

### Overall Results
| Status | Count | Fraction |
|--------|-------|---------|
| Stable (completed to t=1.5 t_J) | {s["n_ok"]} | {100*s["n_ok"]/s["n_total"]:.1f}% |
| Fragmented (timeout_frag) | {s["n_frag"]} | {100*s["n_frag"]/s["n_total"]:.1f}% |
| Failed (error) | 0 | 0% |
| **Total** | **{s["n_total"]}** | |

### Results by Mach Number
| M | Stable | FRAG | FRAG fraction |
|---|--------|------|--------------|
"""
for mach in mach_vals:
    ms = mach_stats[mach]
    report += f"| {mach:.0f} | {ms['no']} | {ms['nf']} | {100*ms['nf']/ms['n']:.1f}% |\n"

report += f"""
---

## 3. Scientific Results

### 3.1 Fragmentation Probability P(frag | f, β, M)

P(frag) is estimated from the two random seeds: 0/2=stable, 1/2=stochastic, 2/2=fragmented.

**Stochastic boundary points** (P=0.5, maximum uncertainty): {n_stoch} grid points  
These map the **width** of the transition zone — where noise determines the outcome.

### 3.2 Transition Boundary at M=1 (Primary phase)

| f \\ β | {" | ".join(f"{b:.1f}" for b in beta_vals)} |
|--------|{"-----|" * len(beta_vals)}
"""
for fv in f_vals:
    row = " | ".join(pfrag_cell(1.0, fv, b) for b in beta_vals)
    report += f"| {fv:.1f} | {row} |\n"

report += f"""
✅ = Stable (P=0) | ◆ = Stochastic (P=0.5) | ❌ = Fragmented (P=1)

### 3.3 Transition Boundary at M=2

| f \\ β | {" | ".join(f"{b:.1f}" for b in beta_vals)} |
|--------|{"-----|" * len(beta_vals)}
"""
for fv in f_vals:
    row = " | ".join(pfrag_cell(2.0, fv, b) for b in beta_vals)
    report += f"| {fv:.1f} | {row} |\n"

report += f"""
### 3.4 Transition Boundary at M=3

| f \\ β | {" | ".join(f"{b:.1f}" for b in beta_vals)} |
|--------|{"-----|" * len(beta_vals)}
"""
for fv in f_vals:
    row = " | ".join(pfrag_cell(3.0, fv, b) for b in beta_vals)
    report += f"| {fv:.1f} | {row} |\n"

report += f"""
### 3.5 Critical β Values: β_crit(f, M)

β_crit is the value where P(frag) transitions from 0 → 1 (interpolated between grid points).
Values marked (<grid) indicate β_crit is below the tested range (β < 0.3).
Values marked (>grid) indicate β_crit is above the tested range (β > 1.3).

| f | M=1 | M=2 | M=3 | M=4 | M=5 |
|---|-----|-----|-----|-----|-----|
"""
for fv in f_vals:
    row = " | ".join(beta_crit_str(m, fv) for m in mach_vals)
    report += f"| {fv:.1f} | {row} |\n"

report += f"""
### 3.6 Stochastic Transition Points

The following (f, β, M) grid points show seed-dependent outcomes (P=0.5):

| f | β | M | n_frag/n_total |
|---|---|---|----------------|
"""
for sp in stoch_list:
    report += f"| {sp['f']:.1f} | {sp['beta']:.1f} | {sp['mach']:.0f} | {sp['n_frag']}/{sp['n_total']} |\n"

report += f"""
---

## 4. Physical Interpretation

### 4.1 Role of Longitudinal B-field

For **longitudinal** B (along the filament axis x1), the magnetic field geometry is
fundamentally different from the transverse-B case:

- **No tension against axial fragmentation**: Magnetic tension resists bending (transverse
  displacement) of field lines, not compression along them. For k ∥ B (axial modes),
  there is no magnetic restoring force against density perturbations.

- **Alfvén speed independent of f**: v_A = c_s·√(2/β) is determined entirely by β,
  not by the supercriticality parameter f. This is because B₀ₓ ∝ √(ρ_c) and ρ_c ∝ f,
  so v_A = B₀ₓ/√(4πρ_c) ∝ √f/√f = const.

- **Suppression via 3D collapse resistance**: Strong longitudinal B (low β) resists
  **radial** compression of growing density cores. Once axial turbulence seeds an
  overdense region, its subsequent 3D gravitational collapse has a radial (x2/x3)
  component. Flux freezing means radial compression increases |B|, opposing infall.
  Low β → strong magnetic support against the radial collapse component → slower
  overall density growth → sims survive to t = 1.5 t_J without divergence.

### 4.2 Key Physical Findings

1. **β_crit decreases with M**: Higher turbulence drives faster density growth, requiring
   stronger B (lower β) to prevent collapse within 1.5 t_J.
   - M=1: β_crit > 1.3 at f=1.4 (stable across entire tested grid)
   - M=2: β_crit ≈ 0.5–0.7 (f-dependent)
   - M=3: β_crit ≈ 0.3–0.5 (near grid edge)
   - M=4,5: β_crit < 0.3 (essentially off-grid; ~100% FRAG)

2. **Stable ridge at β=0.3, M=1**: This ridge persists across the **entire** f=1.4–2.2
   range. Even at f=2.2 (2.2× the critical line-mass), the β=0.3, M=1 configuration
   does not produce a density singularity within 1.5 t_J. This demonstrates that strong
   longitudinal B can dramatically slow collapse even for highly supercritical filaments,
   provided turbulent driving is minimal.

3. **Non-monotonic f-dependence at M=1**: f=1.5 showed anomalously high instability
   compared to neighbouring f values (f=1.4 and f=1.6). This may reflect a resonance
   between the Jeans length at f=1.5 and the dominant turbulent mode, or a stochastic
   effect near the transition zone. Further investigation with finer f sampling would
   clarify this.

4. **Stochastic transition zone**: {n_stoch} parameter points show seed-dependent
   outcomes (P=0.5), indicating the transition is not a sharp line but a probabilistic
   zone. Near-critical filaments in the ISM may fragment or not depending on the
   specific turbulent realisation, contributing to observed scatter in fragmentation
   properties.

5. **Contrast with transverse-B**: Previous campaigns (field-geometry-apr2026) found
   β_crit ≈ 2/3 for transverse B, independent of f, with clear tension-dominated
   stabilisation. The longitudinal-B DTC finds β_crit values ranging from <0.3 to >1.3,
   strongly M-dependent and with weaker f-dependence, reflecting a physically distinct
   suppression mechanism (radial collapse resistance rather than axial tension).

### 4.3 Observational Implications

For ISM filaments with organised longitudinal B fields (e.g., along spine of Herschel-
detected filaments):

- Fragmentation stability depends primarily on **turbulent Mach number**, not
  supercriticality: even strongly supercritical filaments (f>2) can be stable at M=1.
- The critical β ≈ 0.5–0.7 for M=2 corresponds to v_A ≈ 1.6–2.0 c_s (mildly
  super-Alfvénic turbulence on filament scales). This is within the range inferred
  from Planck polarisation measurements of nearby filaments.
- The probabilistic transition zone (P=0.5 points) predicts intrinsic scatter in
  core spacings even for uniform mean conditions — consistent with observed core
  spacing variance in Herschel surveys.

---

## 5. Data Products

### Simulation Output (on astra-climate)
- **HDF5 snapshots**: `/data/dtc_runs/DTC_*/` (2 snapshots per sim at t=0, 1.0 t_J;
  3 for completed sims additionally at t=1.5 t_J)
- **HST files**: `/data/dtc_runs/DTC_*/*.hst` (full time history per sim)
- **Manifest**: `/data/dtc_runs/manifest.json` ({s["n_total"]} entries, reconstructed from HST)
- **Analysis results**: `/data/dtc_runs/dtc_analysis_results.json`

### Figures
- `fig1_pfrag_heatmaps.png/pdf`: P(frag|f,β) heatmaps for M=1–5
- `fig2_beta_crit_curves.png/pdf`: β_crit(f) curves for all M values
- `fig3_transition_zone_M123.png/pdf`: Discrete stability map (M=1,2,3)
- `fig4_transition_zone_M45.png/pdf`: Discrete stability map (M=4,5)

All figures at: `/data/dtc_runs/dtc_figures/`

---

## 6. Next Steps

1. **Finer grid near transition**: Sample f=1.4–1.6 at finer β resolution (Δβ=0.1)
   around the M=1 transition zone to resolve β_crit(f, M=1) precisely.

2. **Density contrast extraction**: Read HDF5 snapshots to extract ρ_max/ρ_c at
   t=1.0 t_J for all completed sims → quantify pre-collapse amplification.

3. **Non-isothermal EOS**: Repeat key (f,β,M) points with adiabatic EOS to test
   whether a density floor changes the transition boundary.

4. **Cross-comparison**: Compare β_crit(M) from DTC with the field-geometry-apr2026
   calibration (transverse B) to quantify the geometry-dependent suppression factor.

5. **Herschel W3 application**: Apply DTC results at W3 conditions (M≈2–3, β≈0.5–1.0,
   f≈1.5–2.0) to predict fragmentation stability along the W3 Main ridge.

---

*Report generated by ASTRA system | astra-pa agent | {now}*
"""

with open(REPORT, "w") as f:
    f.write(report)

print(f"Report written to {REPORT}")
print(f"Report length: {len(report)} chars, {len(report.splitlines())} lines")
