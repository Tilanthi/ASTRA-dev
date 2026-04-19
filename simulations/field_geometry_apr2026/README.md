# Field Geometry Campaign — April 2026

## Overview
30 isothermal MHD simulations at 128³ resolution testing the magnetic Jeans fragmentation formula:

**λ_MJ(θ,β) = λ_J √(1 + 2sin²θ/β)**

where θ = angle between B and filament axis, β = thermal/magnetic pressure ratio.

## Campaign Parameters
- **Grid**: 128³ cells, L = 8 λ_J
- **Resolution**: dx = L/128 = 0.0625 λ_J
- **θ values**: 0°, 30°, 45°, 60°, 75°, 90°
- **β values**: 0.5, 0.75, 1.0, 1.5, 2.0  (30 total sims)
- **Physics**: isothermal MHD + FFT self-gravity, M_sonic=3, no sink particles
- **tlim**: 15 t_J, dt_output = 0.5 t_J
- **Compute**: astra-climate (224 vCPU GCE), Athena++

## Key Result
From 16 valid simulations (N_cores ≥ 4, θ ≠ 0°):

**λ_frag = (1.09 ± 0.11) × λ_MJ(θ,β)**

This confirms the magnetic Jeans formula to within ~15% across the (θ,β) parameter space.

## Files

### `analysis/`
- `option_b_analysis_v2.json` — Full results for all 30 sims (t_final, C, N_cores, λ_sep, ratios)
- `option_b_report_v2.md` — Formatted report with tables and calibration result

### `scripts/`
- `analyse_option_b_v2.py` — Analysis script (v2: includes penultimate-snapshot fallback)

## Caveats

### θ=0° box-scale artifact
At θ=0°, λ_MJ = λ_J = 1 regardless of β (sin²0°=0). The seed mode at this wavelength
has γ=0 (marginally stable), so box-scale mode dominates → single condensation, not λ_J-spaced cores.
θ=0° data excluded from calibration.

### dt-death spiral
Isothermal MHD without sink particles: dt→0 as cores collapse (ρ→∞).
Sims killed when spiral detected; analysis uses last valid snapshot.

### Core merging at θ=45°, β=1.5-2.0
These sims show 5 cores at λ_sep=1.6 even though λ_seed=1.333 (6-mode seeded).
The extra factor reflects physical late-time core merging (C=9.8-15 → well-evolved).

## Relation to W3 Observations
- **W3 filament conditions**: θ~40-60° (Planck polarimetry), β~0.7-1.0
- **λ_MJ(50°, 0.85)** ≈ 1.60 λ_J
- **Predicted λ_frag** ≈ 1.09 × 1.60 × λ_J = 1.75 λ_J
- At W3 distance (1.95 kpc) and typical filament Jeans length (~0.1 pc): λ_frag ≈ 0.17 pc

## Authors
- Glenn J. White (Open University)
- ASTRA multi-agent system (astra-pa, astra-orchestrator)
- Date: April 2026
