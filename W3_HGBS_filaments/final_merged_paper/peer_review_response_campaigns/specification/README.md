# Peer Review Response Simulation Campaigns
## MNRAS Major Revision - 2026-04-30

## Overview
These campaigns address all unresolved questions from peer review using ATHENA++ MHD simulations on 200 CPUs (ray cluster).

## Campaign Priorities

### CRITICAL: Campaign 8 - Mixed Field Geometry Quantification
**Resolves**: Central tension (perpendicular λ/W ≈ 1.25 vs observed 2.79)

**Question**: What fraction of filaments with oblique B-fields are needed to reproduce λ/W = 2.79?

**Specification**:
```
Campaign 8: Mixed Geometry λ/W Calibration
Objective: Quantify λ/W(θ) for oblique B-fields to determine mixing fraction required

Parameters:
  - f = 1.5 (representative supercritical)
  - β = [0.3, 0.5, 1.0, 1.5, 2.0] (full range)
  - θ = [0°, 15°, 30°, 45°, 60°, 75°, 90°] (7 angles)
  - M = 1.0 (fixed)
  - Seeds: 5 per parameter point

Total simulations: 5 (β values) × 7 (angles) × 5 (seeds) = 175

Domain: 16λ_J × 1λ_J × 1λ_J at 512 × 64 × 64
  - Long axial domain to capture multiple fragmentation wavelengths

Runtime: ~15 hours on 200 CPUs

Output requirements:
  - HDF5 snapshots at 50% compression intervals
  - λ/W measurements for each simulation
  - t_frag measurements
  - Classification (FRAG/STABLE/RADIAL)
  - Longitudinal density profiles for beading analysis

Analysis needed:
  - Fit λ/W(θ) for each β
  - Determine mixing fraction f_L needed to produce λ/W = 2.79
  - Compare with Planck (2016) polarimetric statistics
```

### CRITICAL: Campaign 9 - Supercritical Longitudinal Beading
**Resolves**: Supercritical extrapolation gap, radial vs longitudinal fragmentation

**Key Innovation**: Use STAGED FRAGMENTATION - initialize with near-critical f, then ramp to supercritical over time

**Specification**:
```
Campaign 9: Staged Fragmentation in Supercritical Regime
Objective: Test whether supercritical filaments can show longitudinal beading
if they start near-critical and fragment before radial collapse dominates

Parameters:
  - f_initial = [0.9, 1.0, 1.1, 1.2] (near-critical start)
  - f_final = [1.5, 2.0, 2.5, 3.0] (supercritical end)
  - β = [0.5, 1.0, 2.0] (representative)
  - M = 1.0 (fixed)
  - Seeds: 5 per parameter point

Total simulations: 4 (f_initial) × 4 (f_final) × 3 (β) × 5 = 240

Innovation: Time-dependent line mass
  - Phase 1: Evolve at f_initial until t = 1.2 t_J (allow fragmentation onset)
  - Phase 2: Ramp f to f_final linearly over 0.3 t_J
  - Phase 3: Evolve at f_final until t = 2.0 t_J or fragmentation

Domain: 16λ_J × 1λ_J × 1λ_J at 512 × 64 × 64

Runtime: ~20 hours on 200 CPUs

Output requirements:
  - HDF5 snapshots throughout staged evolution
  - Density evolution tracking
  - Longitudinal beading detection (σ(ρ)/⟨ρ⟩ > 3)
  - Radial collapse detection (σ(ρ)/⟨ρ⟩ profile analysis)
  - Final λ/W measurements if beading occurs
  - Classification: LONGITUDINAL_BEADING, RADIAL_COLLAPSE, NO_FRAG

Critical test: Does early-time fragmentation at near-critical f leave
persistent longitudinal structure that survives supercritical ramp?
```

### Campaign 10 - Filament Length L/3 Convergence Test
**Resolves**: Pairwise median L/3 convergence, proper NN validation for all regions

**Specification**:
```
Campaign 10: Filament Length Dependence & NN Statistics Validation
Objective: Quantify L/3 convergence effect and compute proper NN spacing
for all 8 HGBS regions

Simulation setup (for each region):
  - Use actual HGBS filament lengths from skeleton analysis
  - Taurus: L ≈ 8.5 pc, N = 536 cores
  - Orion B: L ≈ 12 pc, N = 1844 cores
  - Aquila: L ≈ 10 pc, N = 749 cores
  - Perseus: L ≈ 9 pc, N = 816 cores
  - Ophiuchus: L ≈ 6 pc, N = 513 cores
  - Serpens: L ≈ 7 pc, N = 194 cores
  - TMC1: L ≈ 5 pc, N = 178 cores
  - CRA: L ≈ 6 pc, N = 239 cores

For each region, run 2 test simulations:
  Test A: Periodic beading at known spacing (d = 0.3 pc)
    - Filament length: L (actual)
    - Place cores at intervals d along filament
    - N = floor(L/d) cores
    - Measure pairwise median vs true spacing

  Test B: Random uniform core distribution
    - Filament length: L (actual)
    - Place N cores uniformly at random along filament
    - Measure pairwise median (should approach L/3)

Plus: Full HGBS re-analysis with proper NN spacing
  - Use existing skeleton and core catalog data
  - Compute NN spacing for all 8 regions
  - Compare with pairwise median
  - Assess systematic bias

Simulations: 8 regions × 2 test cases × 3 seeds = 48
Analysis: Computational (using existing HGBS data)

Runtime: ~2 hours for simulations + ~4 hours for analysis

Output requirements:
  - Pairwise median measurements
  - True spacing (known input)
  - L/3 predicted values
  - Bias quantification: bias = (pairwise_median - true_spacing) / true_spacing
  - Region-by-region NN spacing results (8 files)
  - Cross-region statistical analysis
```

### Campaign 11 - Temporal Evolution Scenario Test
**Resolves**: Were HGBS filaments near-critical at fragmentation time?

**Specification**:
```
Campaign 11: Temporal Evolution Scenario - Near-Critical Fragmentation
Objective: Test whether HGBS filaments could have fragmented at near-critical
mass per unit length, then accreted to become supercritical

Parameters:
  - f_initial = 1.0 (near-critical)
  - Accretion scenarios:
    Scenario A: No accretion (control) - evolve at f=1.0
    Scenario B: Slow accretion - f(t) = 1.0 → 1.5 over 5 t_J
    Scenario C: Rapid accretion - f(t) = 1.0 → 2.0 over 2 t_J
    Scenario D: Very rapid accretion - f(t) = 1.0 → 3.0 over 1 t_J
  - β = [0.5, 1.0, 2.0] (representative)
  - M = 1.0 (fixed)
  - Seeds: 5 per parameter point

Total simulations: 4 (scenarios) × 3 (β) × 5 (seeds) = 60

Key measurements:
  - Fragmentation wavelength λ/W at time of beading
  - Time of fragmentation t_frag
  - Subsequent evolution: does beading persist during accretion?
  - Final core properties

Domain: 16λ_J × 1λ_J × 1λ_J at 512 × 64 × 64

Runtime: ~8 hours on 200 CPUs

Output requirements:
  - λ/W at fragmentation time
  - t_frag measurements
  - Beading persistence tracking: does λ/W remain constant during accretion?
  - Final density profiles
  - Classification: PERSISTENT_BEADING, BEADING_MERGER, RADIAL_COLLAPSE

Critical question: If filaments fragment at f≈1.0 with λ/W≈2-3, then accrete to f≈2-3,
does the observed λ/W still reflect the near-critical fragmentation wavelength?
```

### Campaign 12 - DTC Boundary Reassessment
**Resolves**: Do corrected DTC results shift three-regime framework?

**Specification**:
```
Campaign 12: Refined DTC with Extended Coverage
Objective: Remap the stable-unstable boundary with corrected timeout handling
and assess impact on three-regime framework

Parameters:
  - Focus on β = 0.3 region (where artifacts occurred)
  - Extended M range: M = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
  - f range: f = [1.2, 1.4, 1.6, 1.8, 2.0, 2.2]
  - Seeds: 5 per parameter point
  - Wall-clock timeout: 6 hours (corrected from 600s)

Total simulations: 10 (M) × 6 (f) × 5 (seeds) = 300

Domain: 8λ_J × 1λ_J × 1λ_J at 256 × 128 × 128
  - Smaller domain acceptable for DTC mapping

Runtime: ~12 hours on 200 CPUs

Output requirements:
  - Fragmentation probability P_frag(f, M, β)
  - t_frag measurements
  - Classification: FRAG, STABLE, STABLE_PARTIAL, RADIAL
  - Comparison with original DTC results
  - Updated three-regime framework diagram
  - Boundary shift analysis: Δβ_crit, Δf_crit

Key question: Does extended M range or corrected timeout significantly
shift the stability boundary?
```

### Campaign 13 - Independent β Validation
**Resolves**: β-constraint from λ/W vs independent Zeeman/polarimetry

**Research component**: Compile literature β measurements for HGBS regions
**No new simulations required** - use existing Campaign 5 + 7 data

**Specification**:
```
Campaign 13: Literature β Compilation and Validation
Objective: Compare λ/W-derived β predictions with independent measurements

Data collection:
  - Compile Zeeman effect measurements for HGBS regions
  - Compile dust polarimetry measurements
  - Compile gas/dust emission line ratio methods
  - Literature search for: Taurus, Orion B, Aquila, Perseus, Ophiuchus,
    Serpens, TMC1, CRA

Analysis:
  - For each region with independent β measurement:
    * Get λ/W from paper (use robust regions: 4 measurements)
    * Use Campaign 7 calibration: λ/W(β) from Table 7
    * Predict β from λ/W using inverse interpolation
    * Compare with measured β

  Expected calibration from Campaign 7 (f = 1.0-1.2):
    β = 0.3 → λ/W = 4.74
    β = 0.5 → λ/W = 4.38
    β = 1.0 → λ/W = 3.19
    β = 1.5 → λ/W = 2.86
    β = 2.0 → λ/W = 2.80

  Statistical comparison:
    - Compute Δβ = β_pred - β_meas
    - Assess consistency: |Δβ| < 0.5?
    - Identify regions with good/poor agreement

Output requirements:
  - Table comparing predicted vs measured β
  - Scatter plot: β_pred vs β_meas
  - Assessment of λ/W → β as a diagnostic tool
  - Discussion of systematic uncertainties

Runtime: Literature research (~1 week)
```

## Campaign Summary

| Campaign | Simulations | Runtime | Priority |
|----------|-------------|---------|----------|
| C8: Mixed Geometry | 175 | 15 hrs | CRITICAL |
| C9: Staged Fragmentation | 240 | 20 hrs | CRITICAL |
| C10: L/3 Convergence | 48 + analysis | 6 hrs | HIGH |
| C11: Temporal Evolution | 60 | 8 hrs | MEDIUM |
| C12: Refined DTC | 300 | 12 hrs | MEDIUM |
| C13: β Validation | Literature | 1 week | HIGH |

**Total simulation time**: ~61 hours on 200 CPUs

**Total cost**: ~2.5 days of cluster time

## Output Format Requirements

All campaigns must produce:

1. **results.json** - Machine-readable summary:
```json
{
  "campaign": "C8_Mixed_Geometry",
  "date": "2026-04-30",
  "n_simulations": 175,
  "parameters": {
    "f_values": [1.5],
    "beta_values": [0.3, 0.5, 1.0, 1.5, 2.0],
    "theta_values": [0, 15, 30, 45, 60, 75, 90],
    "seeds": [42, 137, 314, 527, 816]
  },
  "measurements": {
    "lambda_W": [...],
    "t_frag": [...],
    "classification": [...]
  }
}
```

2. **analysis_summary.pdf** - Visual summary figures:
   - Key plots (λ/W vs θ, λ/W vs β, t_frag vs f)
   - Comparison tables
   - Statistical analysis

3. **README.md** - Campaign-specific documentation:
   - Scientific objective
   - Parameter justification
   - Key findings
   - Recommendations for paper

4. **HDF5 snapshots** (selected simulations only):
   - Density fields at key times
   - Longitudinal profiles
   - For validation and visualization

## Execution Instructions

Using ray cluster (200 CPUs):

```bash
# Activate environment
conda activate astra

# Run campaign
python -m ray.execute --num-cpus 200 run_campaign_8.py

# Or use the runner script
bash run_all_campaigns.sh
```

## Data Return Format

After campaign completion, package results as:

```
peer_review_response_results_<date>.tar.gz
├── C8_Mixed_Geometry/
│   ├── results.json
│   ├── analysis_summary.pdf
│   ├── README.md
│   └── snapshots/ (selected cases)
├── C9_Staged_Fragmentation/
│   ├── results.json
│   ├── analysis_summary.pdf
│   ├── README.md
│   └── snapshots/
├── C10_L3_Convergence/
│   ├── results.json
│   ├── NN_spacing_results/
│   │   ├── Taurus_nn_spacing.json
│   │   ├── OrionB_nn_spacing.json
│   │   └── ...
│   ├── analysis_summary.pdf
│   └── README.md
├── C11_Temporal_Evolution/
│   ├── results.json
│   ├── analysis_summary.pdf
│   └── README.md
├── C12_Refined_DTC/
│   ├── results.json
│   ├── analysis_summary.pdf
│   ├── README.md
│   └── boundary_comparison.pdf
└── C13_Beta_Validation/
    ├── beta_comparison_table.tex
    ├── beta_comparison.pdf
    └── README.md
```

Return to: /Users/gjw255/astrodata/SWARM/ASTRA-dev/W3_HGBS_filaments/final_merged_paper/peer_review_response_campaigns/
