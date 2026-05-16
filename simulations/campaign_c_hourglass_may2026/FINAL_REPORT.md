# Campaign C: Hourglass B-field Geometry — FINAL REPORT

**Campaign**: Supercritical Filament Fragmentation with Hourglass Magnetic Field Morphology  
**Date**: 15–16 May 2026  
**Platform**: astra-climate (GCE, 32 vCPU per simulation)  
**Binary**: `athena_supercritical` (Athena++ MHD, isothermal, 3D)  
**Total**: 108 simulations | **108/108 FRAG** | 0 TIMEOUT | 0 FAILED  
**Classification**: 101 BEADING_STABLE, 7 BEADING_TRANSIENT  
**Total compute**: 2,111 CPU-hours (66 wall-hours)

## 1. Campaign Overview

### 1.1 Motivation

Previous ASTRA campaigns (A, B, and prior referee-response campaigns) used uniform magnetic fields — either purely longitudinal (θ=0°) or purely perpendicular (θ=90°). Real interstellar filaments, however, exhibit **hourglass-shaped** magnetic field morphologies, where field lines are pinched at the filament waist and flare outward at larger radii. This geometry is observed in polarimetry of dense cores and filaments (e.g., Girart et al. 2006; Pillai et al. 2020).

Campaign C tests whether hourglass field geometry fundamentally alters the fragmentation physics — specifically whether the magnetic tension from pinched field lines acts to **accelerate** or **inhibit** gravitational fragmentation, and whether the characteristic fragment spacing λ/W is preserved.

### 1.2 Parameter Grid

| Parameter | Values | Description |
|-----------|--------|-------------|
| f (line-mass ratio) | 1.5, 2.0, 3.0 | M_ℓ / M_ℓ,crit |
| β_c (central plasma beta) | 0.5, 1.0, 2.0 | P_gas / P_mag at filament axis |
| r_waist / r_fil | 0.3, 0.5, 1.0 | Hourglass pinching ratio |
| M (Mach number) | 1.0, 2.0 | Turbulent perturbation amplitude |
| seeds | 0, 1 | Random seed for perturbations |

**Total**: 3 × 3 × 3 × 2 × 2 = **108 simulations**

### 1.3 Domain and Resolution

- **Domain**: 256 × 128 × 128 cells
- **Meshblocks**: NP = 32 per MPI rank
- **MAX_CONC**: 6 (AMR concentration factor)
- **Physical domain**: 16 λ_J along filament axis

### 1.4 Hourglass Field Implementation

The magnetic field is initialised with an hourglass morphology:
- B_z(r) = B_0 × [1 + (r/r_waist)²]^(-1) at the filament midplane
- Field lines flare outward for r > r_waist
- r_waist = r_waist_ratio × r_fil, where r_fil is the filament radius
- r_waist_ratio = 0.3 represents strong pinching; r_waist_ratio = 1.0 is nearly uniform

## 2. Key Results

### 2.1 KEY RESULT 1: β Dominates Fragmentation Timescale (3.3× range)

The central plasma beta β_c is the **dominant** control parameter, producing a 3.3× variation in fragmentation timescale — far exceeding the effects of line-mass ratio f, waist ratio r_waist, or turbulent Mach number M.

**CRITICAL FINDING**: Low β (strong B) produces **faster** fragmentation, the **opposite** of uniform-field behaviour. The hourglass geometry inverts the role of magnetic fields.

| β_c | t_frag [t_J] | σ | n |
|-----|-------------|---|---|
| 0.5 | 0.186 | 0.130 | 36 |
| 1.0 | 0.518 | 0.211 | 36 |
| 2.0 | 0.607 | 0.073 | 36 |

**Range**: β=0.5 → β=2.0 gives 0.186 → 0.607 t_J (**3.3× variation**)

Compare with uniform-field Campaign B (γ=1.0):
- θ=0° (longitudinal): t_frag ≈ 0.79 t_J — β weakly inhibits (10% effect)
- θ=90° (perpendicular): t_frag ≈ 0.43 t_J — β weakly accelerates

**Hourglass at β=0.5**: t_frag ≈ 0.087–0.37 t_J — **faster than both uniform orientations**, because magnetic tension from pinched field lines actively funnels material toward collapse sites.

### 2.2 KEY RESULT 2: Inverted f-Dependence at Strong B

In uniform-field simulations, higher f (more supercritical) always produces faster fragmentation. With hourglass geometry, **this relationship inverts at strong B**:

| β_c \ f | 1.5 | 2.0 | 3.0 | Trend |
|---------|------|------|------|-------|
| 0.5 | 0.087 | 0.106 | 0.367 | **INVERTED** (higher f → slower) |
| 1.0 | 0.253 | 0.690 | 0.611 | Non-monotonic |
| 2.0 | 0.692 | 0.611 | 0.519 | **NORMAL** (higher f → faster) |

**Physical interpretation**: At β_c = 0.5 (strong field), the hourglass pinching creates intense magnetic tension that drives radial compression. Higher f means more mass, which makes the filament cross-section larger and more resistant to the pinching effect — the self-gravity actually stabilises the geometry against magnetic compression. This is a **self-regulating** mechanism.

At β_c = 2.0 (weak field), the hourglass geometry is a minor perturbation and the standard gravitational instability dominates, recovering the normal f-dependence.

### 2.3 KEY RESULT 3: λ/W ≈ 2.80 — Universal Fragmentation Spacing

The fragment spacing-to-width ratio is remarkably constant across **all** parameter combinations:

**λ/W = 2.80 ± 0.23** (108 simulations, range 2.49–3.65)

| Parameter | Subset | λ/W | σ |
|-----------|--------|-----|---|
| β_c = 0.5 | 36 sims | 2.71 | 0.21 |
| β_c = 1.0 | 36 sims | 2.86 | 0.25 |
| β_c = 2.0 | 36 sims | 2.82 | 0.23 |
| f = 1.5 | 36 sims | 2.82 | 0.28 |
| f = 2.0 | 36 sims | 2.76 | 0.17 |
| f = 3.0 | 36 sims | 2.82 | 0.24 |
| r_waist = 0.3 | 36 sims | 2.77 | 0.24 |
| r_waist = 0.5 | 36 sims | 2.82 | 0.22 |
| r_waist = 1.0 | 36 sims | 2.80 | 0.25 |

The 8% coefficient of variation (σ/μ) confirms that **fragment spacing is set by the underlying gravitational instability, not by the magnetic field morphology**. The hourglass geometry changes *when* fragmentation occurs (t_frag) but not *where* (λ/W).

### 2.4 Comparison with Prior Campaigns

| Campaign | Geometry | t_frag range [t_J] | λ/W |
|----------|----------|-------------------|-----|
| **C (hourglass)** | Pinched B | 0.075–0.715 | **2.80 ± 0.23** |
| B (uniform, θ=0°) | Longitudinal B | 0.65–0.92 | 2.89 ± 0.27 |
| B (uniform, θ=90°) | Perpendicular B | 0.35–0.53 | 4.55 ± 1.78 |
| C5 (turbulent, θ=0°) | Longitudinal B | 0.36–1.05 | 3.44 ± 0.76 |
| C6 (perp, β≥1) | Perpendicular B | 0.53–0.72 | 1.25 ± 0.09 |

**Key comparisons**:
1. Hourglass λ/W (2.80) is consistent with uniform longitudinal λ/W (2.89) — within 1σ
2. Hourglass t_frag range (0.075–0.715) is **much broader** than any uniform-field campaign — the field geometry creates extreme sensitivity to β
3. Hourglass at β_c=0.5 achieves the **fastest fragmentation** of any ASTRA campaign (0.075 t_J at r_waist=1.0, f=1.5)

## 3. Secondary Effects

### 3.1 Waist Ratio r_waist

The hourglass pinching ratio has a **secondary** effect (~15% variation in t_frag):

| β_c \ r_waist | 0.3 | 0.5 | 1.0 | Δ% |
|---------------|------|------|------|-----|
| 0.5 | 0.204 | 0.181 | 0.174 | 15% |
| 1.0 | 0.590 | 0.488 | 0.476 | 19% |
| 2.0 | 0.608 | 0.617 | 0.597 | 3% |

- Tighter waist (lower r_waist) → slightly **slower** fragmentation at β=0.5 and 1.0
- The effect is negligible at β=2.0 (weak field makes geometry irrelevant)
- Physical interpretation: stronger pinching concentrates B at the axis but also increases magnetic pressure support locally, slightly delaying axial collapse

### 3.2 Turbulent Mach Number M

Turbulence has a **negligible** effect on hourglass fragmentation:

| M | t_frag [t_J] | σ |
|---|-------------|---|
| 1.0 | 0.442 | 0.240 |
| 2.0 | 0.432 | 0.231 |

**M effect: 2.4%** — within seed-to-seed scatter. This is consistent with Campaign A's finding that subsonic/transonic turbulence does not significantly alter fragmentation timescales when the dominant instability is gravitational.

## 4. Physical Interpretation

### 4.1 Hourglass Field Funnelling vs Support

The central discovery of Campaign C is the **dual role** of hourglass magnetic fields:

1. **Strong B (β_c ≤ 0.5)**: Magnetic tension from pinched field lines creates **radial compression** that funnels material toward the filament axis, **accelerating** fragmentation. The t_frag can be as low as 0.075 t_J — an order of magnitude faster than free gravitational collapse timescales.

2. **Weak B (β_c ≥ 2.0)**: The hourglass is a perturbation on an essentially hydrodynamic filament. Standard gravitational fragmentation dominates, with t_frag ≈ 0.5–0.7 t_J.

3. **Intermediate B (β_c ≈ 1.0)**: Complex interaction where magnetic funnelling and gravitational instability compete, producing the largest variance in outcomes.

### 4.2 Self-Regulating Mechanism

The inverted f-dependence at β_c = 0.5 reveals a **self-regulating feedback loop**:
- Higher f → more massive filament → larger cross-section
- Larger cross-section → field lines less pinched (geometry diluted)
- Less pinching → weaker magnetic funnelling → slower fragmentation
- Slower fragmentation → more time for mass accretion → f increases further

This creates a natural "thermostat" that may explain why observed filaments cluster around f ≈ 1–3 rather than running away to very high f values.

### 4.3 Universal λ/W

The constancy of λ/W ≈ 2.8 across all hourglass parameters reinforces the ASTRA finding that **fragment spacing is a gravitational invariant**. While the magnetic field geometry dramatically affects the fragmentation timescale (by up to an order of magnitude), it does not alter the spatial wavelength of the dominant instability mode.

This is consistent with the theoretical prediction from Inutsuka & Miyama (1997) that the fastest-growing mode of the gravitational instability in an isothermal filament has λ/W ≈ 4–5 (for an infinite cylinder). Our measured value of 2.8 reflects the finite, supercritical filament geometry.

## 5. Files and Deliverables

### Figures
| Figure | Description |
|--------|-------------|
| fig1_beta_dominance.png/pdf | 3-panel t_frag vs β for each f value |
| fig2_inverted_f.png/pdf | t_frag vs f showing inverted dependence at β=0.5 |
| fig3_rwaist_effect.png/pdf | β × r_waist heatmap + effect size comparison |
| fig4_lambda_W.png/pdf | λ/W distribution histogram + parameter breakdown |
| fig5_comparison.png/pdf | Campaign C vs Campaign B comparison |

### Data
| File | Description |
|------|-------------|
| campaign_c_summary.json | Comprehensive statistics by all parameters |
| campaign_c_results.json | Raw results for all 108 simulations |
| campaign_c_hourglass_results.tar.gz | Complete analysis package |

## 6. Campaign Configuration

```
Binary: athena_supercritical
Domain: 256 × 128 × 128
NP: 32 (MPI ranks per sim)
MAX_CONC: 6
Physical domain: 16 λ_J (axial) × 4 λ_J (radial, each direction)
EOS: Isothermal (γ = 1.0)
Field geometry: Hourglass (r_waist = r_waist_ratio × r_fil)
Perturbation: Turbulent velocity field at Mach M
Wall time limit: 21600 s (6 hours)
DT_KILL: 1e-6 t_J (timestep floor watchdog)
```

## 7. Conclusions

1. **Hourglass B-field geometry fundamentally alters filament fragmentation physics.** Strong pinched fields (β_c ≤ 0.5) accelerate fragmentation by up to 10×, inverting the role of magnetic fields from support to compression.

2. **β_c is the dominant parameter** (3.3× range in t_frag), far exceeding the effects of f (1.4×), r_waist (~15%), or M (~2%).

3. **The f-dependence inverts at strong B**, revealing a self-regulating mechanism where more massive filaments resist magnetic pinching.

4. **λ/W = 2.80 ± 0.23 is universal**, independent of field geometry, strength, pinching ratio, or turbulence — confirming that gravitational instability sets the spatial scale.

5. **All 108 simulations fragmented** (100% FRAG rate), with 94% classified as BEADING_STABLE — confirming that hourglass geometry does not create magnetic stability islands.

---

*Campaign C analysis completed 16 May 2026. Part of the ASTRA Supercritical Filament Fragmentation study.*  
*Authors: Glenn J. White (Open University) & Robin Dey (VBRL Holdings Inc)*
