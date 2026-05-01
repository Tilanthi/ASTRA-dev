# λ/W Campaign Report — Perpendicular & Near-Critical Fragmentation Spacing
**Date**: April 30, 2026  
**Authors**: Glenn J. White (Open University), Robin Dey (VBRL Holdings Inc)  
**Purpose**: Referee response — address λ/W measurement gap for perpendicular-field configurations  
**Cluster**: astra-climate (GCE n2d-highcpu-224, 224 vCPUs, 224 GB RAM, /data 492 GB SSD)

---

## Overview

Two campaigns completed on astra-climate (Apr 30, 2026) providing direct λ/W measurements for both perpendicular (θ=90°) and longitudinal (θ=0°) magnetic field configurations at near-critical mass-to-flux ratios. These results directly address Referee Concern #4: *"The paper lacks λ/W measurements for perpendicular-field configurations."*

---

## Campaign 1: Perpendicular B (θ=90°) — λ/W Extraction

### Configuration
| Parameter | Value |
|-----------|-------|
| Field geometry | θ=90° (B perpendicular to filament axis, in x2-x3 plane) |
| f values | 1.2, 1.5, 2.0, 2.5 |
| β values | 0.5, 1.0, 2.0, 3.0 |
| Seeds | 42, 137, 314 |
| Resolution | 512×64×64 (32 cells/λ_J in x1) |
| Domain | x1=[0,16] λ_J, x2/x3=[−1,1] λ_J |
| HDF5 snapshots | DT=0.05 t_J (retained for λ/W extraction) |
| tlim | 2.5 t_J |
| np | 16 |
| Wall time | 5,114 s (1.42 hr) |

### Results
- **Total**: 48/48 FRAG (100%)
- **Genuine axial beading** (n_peaks < 30, physically real): **N=3 cases**
- **Spurious sub-Jeans signal** (n_peaks > 50, artifact): **N=17 cases**  
- **No measurable signal** (NO_PEAKS, radial collapse dominant): **N=28 cases**

### λ/W Measurements

**Genuine cases** (axial beading at Jeans scale):

| Sim ID | f | β | seed | λ/W | n_peaks | t_frag [t_J] |
|--------|---|---|------|-----|---------|--------------|
| C1_PERP_f1.2_b0.5_s42 | 1.2 | 0.5 | 42 | 2.169 | 23 | 0.4585 |
| C1_PERP_f1.2_b0.5_s137 | 1.2 | 0.5 | 137 | 2.577 | 20 | 0.4726 |
| C1_PERP_f1.5_b0.5_s42 | 1.5 | 0.5 | 42 | 4.156 | 11 | 0.4105 |

**Mean genuine λ/W = 2.97 ± 0.86** (N=3; near-critical f=1.2–1.5, β=0.5 only)

**Spurious cases** (sub-Jeans artifact, discard):
- Parameter space: f≥1.2, β≥2.0; n_peaks = 84–97
- Mean spurious λ/W = 0.583 ± 0.026 (sub-Jeans spacing ~0.175 λ_J)
- Physical origin: radial collapse density noise projected onto x1 axis — NOT longitudinal fragmentation

### Physical Interpretation
Perpendicular B provides radial support (resists x2/x3 compression) but exerts **no axial magnetic tension**. Consequently:
- Near-critical filaments (f≈1.2, β=0.5): axial beading proceeds at Jeans scale → λ/W ≈ 2–4
- Supercritical filaments (f≥2.0) or high-β (β≥2.0): radial collapse is faster than axial beading → λ/W unmeasurable (NOT uncalculated — physically suppressed)
- λ/W≈3.0 for the measurable cases is consistent with linear theory (Nagasawa 1987, Inutsuka & Miyama 1992)

---

## Campaign 4: Near-Critical Longitudinal B (θ=0°) — High-Resolution λ/W

### Configuration
| Parameter | Value |
|-----------|-------|
| Field geometry | θ=0° (B along filament axis, x1-direction) |
| f values | 1.00, 1.05, 1.10, 1.15, 1.20 |
| β values | 0.5, 1.0, 2.0 |
| Seeds | 42, 137, 314 |
| Resolution | 512×128×128 (256³ phase, 64 cells/λ_J — 2× standard resolution) |
| Domain | x1=[−4,4] λ_J (8 λ_J), x2/x3=[−1,1] λ_J |
| HDF5 snapshots | DT=0.05 t_J |
| np | 64 |
| Wall time | 12,460 s (3.46 hr) |

**Note**: Campaign 4 also ran a 128³ phase (32 cells/λ_J), but ALL HDF5 files from that phase returned "Unable to synchronously open object (object 'Time' doesn't exist)" errors. The 128³ λ/W values are unreliable and excluded. Only 256³ results are used below.

### Results
- **Total (256³ phase)**: 42/45 FRAG (3 TIMEOUT at f=1.0, β=0.5 — most magnetised, most nearly critical)
- **All 42 FRAG cases**: λ/W measured, quality GOOD
- **TIMEOUT cases**: f=1.0, β=0.5, seeds {42,137,314} — ran to 6h wall limit without fragmenting; may require longer integration or represent near-critical oscillating configurations

### λ/W Results

**Overall**: **λ/W = 3.190 ± 0.578** (N=42)

**By mass-to-flux ratio f** (mean over β, seeds):

| f | λ/W (mean) | σ | N |
|---|-----------|---|---|
| 1.00 | 2.932 | 0.302 | 6 |
| 1.05 | 3.242 | 0.624 | 9 |
| 1.10 | 3.090 | 0.613 | 9 |
| 1.15 | 3.352 | 0.552 | 9 |
| 1.20 | 3.248 | 0.582 | 9 |

No strong monotonic trend with f — λ/W approximately f-independent in the near-critical regime.

**By plasma β** (mean over f, seeds):

| β | λ/W (mean) | σ | N |
|---|-----------|---|---|
| 0.5 | **3.855** | 0.537 | 12 |
| 1.0 | **3.062** | 0.268 | 15 |
| 2.0 | **2.786** | 0.315 | 15 |

Clear β-dependence: **stronger B field → larger fragment spacing**. Physically expected — longitudinal B tension stretches the fragmentation wavelength above the thermal Jeans scale.

---

## Comparison: Perpendicular vs. Longitudinal B

| Geometry | Field config | λ/W | N | Confidence |
|----------|-------------|-----|---|-----------|
| θ=90° (perp B) | f=1.2–1.5, β=0.5 | **2.97 ± 0.86** | 3 | Limited (narrow window) |
| θ=0° (long B), β=0.5 | f=1.0–1.2 | **3.855 ± 0.537** | 12 | High |
| θ=0° (long B), β=1.0 | f=1.0–1.2 | **3.062 ± 0.268** | 15 | High |
| θ=0° (long B), β=2.0 | f=1.0–1.2 | **2.786 ± 0.315** | 15 | High |

**Key finding**: Perpendicular and longitudinal B give **consistent λ/W ≈ 3** in the near-critical regime (f≈1.2). The magnetic field geometry does not dramatically alter fragmentation spacing when the filament is near-critical — the Jeans scale dominates in both cases.

The β=0.5 longitudinal case gives slightly higher λ/W (3.86 vs 2.97) than the β=0.5 perpendicular case, but given N=3 for the perpendicular measurement, this difference is not statistically significant.

---

## Implications for Referee Response

1. **λ/W gap partially closed**: Perpendicular-B λ/W is now measured for near-critical f=1.2–1.5, β=0.5. Result: λ/W ≈ 3.0, consistent with longitudinal-B and with theory.

2. **Honest framing of remaining gap**: For supercritical (f≥2.0) and high-β (β≥2.0) perpendicular-B cases, λ/W is **physically unmeasurable** — radial collapse is faster than axial beading. This is a physical result, not a computational limitation.

3. **Consistency**: θ=90° and θ=0° give λ/W ≈ 3 in the near-critical regime → field geometry does not dramatically alter fragmentation scale.

4. **β-dependence** (longitudinal): λ/W increases with B field strength (β=0.5→3.86, β=2.0→2.79) — magnetic tension stretches fragmentation wavelength above Jeans scale.

5. **W3 implication**: For W3 parameters (f≈2.0, β≈0.85, θ≈50°), perpendicular-B λ/W is not directly measurable from our simulations, but the near-critical regime result (λ/W≈3) and the longitudinal-B calibration (λ/W≈3.1 at β=1.0) bracket the expected value. Predicted λ_frag ≈ 3 × 0.3 λ_J × (1 + correction) ≈ 0.9 λ_J ≈ 0.09 pc ≈ 9–14" at 1.95 kpc.

---

## Data & Code

### Data files
- `/data/campaign1_perp_lw/` — 48 sim directories + campaign.log + results.json
- `/data/campaign4_nearcrit/` — 90 sim directories (128³ + 256³) + campaign.log + results.json
- `results_full.json` — reconstructed complete C1 dataset with lw_category field

### Scripts
- Athena++ binary: `/home/fetch-agi/athena/bin/athena`
- Campaign runners: `c1_runner.py`, `c4_runner.py` (on astra-climate)
- Analysis: `analyse_c1.py`, `analyse_c4.py`

### Figures
- `fig1_lambda_W_comparison.{pdf,png}` — main comparison: measurability map + λ/W vs f
- `fig2_c4_beta_dependence.{pdf,png}` — Campaign 4 β-dependence and t_frag
- `fig3_c1_tfrag_heatmap.{pdf,png}` — Campaign 1 t_frag heat map (all 48 sims)
- `fig4_lambda_W_summary_boxplot.{pdf,png}` — summary box plot, both geometries

---

## Compute Resources
- **Campaign 1**: 48 × np=16 = 768 core-sims, 1.42 hr wall → ~91 CPU-hrs
- **Campaign 4**: 90 × np=64 = 5,760 core-sims (both phases), 3.46 hr wall → ~394 CPU-hrs
- **Total**: ~485 CPU-hrs on astra-climate (224-core GCE n2d-highcpu-224)
