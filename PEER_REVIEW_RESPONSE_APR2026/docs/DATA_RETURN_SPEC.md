# Data Return Specification
## For Integration into MNRAS Filament Spacing Paper

After completing the peer review response campaign, the following data products are required for paper integration.

---

## CRITICAL DATA PRODUCTS

### 1. Simulation Catalog (CSV)

**File**: `simulation_catalog.csv`

**Required columns**:
- sim_id: Unique simulation identifier
- phase: Campaign phase (1-4)
- f: Line mass fraction
- beta: Plasma beta
- mach: Mach number
- seed: Random seed
- eos: Equation of state (isothermal/adiabatic)
- bfield: Magnetic field geometry (longitudinal/perpendicular/oblique)
- theta: Field angle (for oblique)
- status: FRAG/STABLE/TIMEOUT/ERROR
- t_frag: Fragmentation time (t_J)
- dt_min: Minimum timestep reached
- rho_c_max: Maximum central density
- longitudinal_peaks: Number of density peaks along filament axis
- lambda_frag: Measured fragmentation spacing (if peaks ≥ 2)
- lambda_W: Fragmentation spacing in units of filament width
- fragmentation_quality: excellent/good/marginal/none
- wall_time_seconds: Wall-clock time
- hdf5_outputs: Number of HDF5 snapshots

### 2. Analysis Figures (PDF)

**Figure 1**: Beading Threshold Map - `fig1_beading_threshold.pdf`
- Left: Near-critical longitudinal B-field (heatmap of n_peaks vs f, β)
- Right: Perpendicular B-field (heatmap of n_peaks vs f, β)
- Shows: Where longitudinal beading emerges (addresses T1/T2, T3)

**Figure 2**: λ/W Comparison - `fig2_lambda_W_comparison.pdf`
- Plot: λ/W vs f for different field geometries
- Shows: Perpendicular vs longitudinal field fragmentation spacing
- Includes: HGBS reference line (λ/W = 2.1) and IM92 line (λ/W = 4.0)

**Figure 3**: Oblique Calibration - `fig3_oblique_calibration.pdf`
- Plot: λ_frag vs θ (30°, 45°, 60°)
- Shows: Validation of λ_frag = 1.11 λ_MJ across field geometries (addresses T9)

**Figure 4**: Adiabatic Comparison - `fig4_adia_comparison.pdf`
- Plot: t_frag vs f for isothermal vs adiabatic
- Shows: Effect of EOS on beading emergence (addresses T1/T2)

### 3. Summary Report (Markdown)

**File**: `SUMMARY_REPORT.md`

**Required sections**:

```markdown
# Peer Review Response Campaign - Summary Report

## Executive Summary
- Total simulations completed
- Fragmentation rate
- Longitudinal beading detection rate

## Response by Concern

### T1/T2: Longitudinal Fragmentation Detection
- Simulations with ≥2 peaks: [count]
- Threshold f for beading: [value]
- Sample snapshot showing beading: [image]

### T3: Realistic Field Geometry
- Perpendicular field beading rate: [value]
- λ/W for perpendicular fields: [mean ± std]
- Comparison with HGBS: [statement]

### T9: Field-Geometry Calibration
- Oblique field calibration: λ_frag = [coefficient] × λ_MJ
- Statistical basis: [n_sims] simulations
- Comparison to previous: [statement]

## Conclusions
- Which concerns are fully addressed
- Which concerns are partially addressed
- Recommended additional work (if any)
```

---

## DERIVED DATA PRODUCTS

### Peak Detection Analysis

For each simulation with ≥2 longitudinal peaks, provide:

```json
{
  "sim_id": "example_sim",
  "n_peaks": 3,
  "peak_positions": [128, 256, 384],
  "peak_amplitudes": [2.34, 2.56, 2.12],
  "peak_spacings": [128, 128],
  "lambda_frag": 128.0,
  "lambda_frag_uncertainty": 8.5,
  "quality_metric": 0.45,
  "quality_label": "excellent"
}
```

### Fragmentation Threshold Analysis

For the near-critical regime (Phase 1), provide:

```json
{
  "f_threshold": 1.05,
  "f_threshold_uncertainty": 0.02,
  "beta_dependence": "weak",
  "mach_dependence": "moderate",
  "eos_dependence": "strong"
}
```

### Field Geometry Comparison

For perpendicular vs longitudinal fields (Phase 2), provide:

```json
{
  "longitudinal_lambda_W": {
    "mean": 3.7,
    "std": 0.3,
    "n_sims": 80
  },
  "perpendicular_lambda_W": {
    "mean": 2.3,
    "std": 0.4,
    "n_sims": 96
  },
  "hgbs_agreement": {
    "longitudinal": "poor (3.7 vs 2.1)",
    "perpendicular": "good (2.3 vs 2.1)"
  }
}
```

---

## FILE ORGANIZATION

```
peer_review_response_APR2026/
├── status/
│   ├── *.json                    # Individual simulation status files
│   └── simulation_catalog.csv    # Master catalog (REQUIRED)
├── runs/
│   └── [phase]/
│       └── [sim_id]/
│           ├── *.athdf           # HDF5 snapshots
│           └── *.hst            # History files
├── analysis_output/
│   ├── SUMMARY_REPORT.md         # Required
│   ├── fig1_beading_threshold.pdf  # Required
│   ├── fig2_lambda_W_comparison.pdf  # Required
│   ├── fig3_oblique_calibration.pdf  # Required
│   ├── fig4_adia_comparison.pdf  # Required
│   └── simulation_catalog.csv    # Required
└── sample_snapshots/
    ├── near_critical_beading.png   # Required
    ├── perpendicular_beading.png   # Required
    └── oblique_beading.png          # Required
```

---

## VALIDATION CHECKLIST

Before returning data, verify:

- [ ] All 320 simulations have corresponding status files
- [ ] CSV catalog has no missing values (use NA or -1 for inapplicable)
- [ ] All 4 required figures are present and valid PDFs
- [ ] Summary report addresses T1/T2, T3, T9 concerns
- [ ] Sample snapshots clearly show beading vs no-beading
- [ ] HDF5 files are accessible and readable
- [ ] Peak detection analysis is reproducible from code
- [ ] λ_frag measurements include uncertainties

---

## DELIVERY FORMAT

Package as:
```
peer_review_response_APR2026_results.tar.gz

Contents:
- status/simulation_catalog.csv
- analysis_output/*
- sample_snapshots/*
- scripts/analyze_campaign.py  # For reproducibility
- README_RESULTS.txt           # This file
```

Upload to GitHub and provide location for integration.

---

## CONTACT FOR CLARIFICATION

If any requirements are unclear, or if simulation results don't match expected formats, contact before running full campaign to avoid wasted computational effort.

**Key questions to resolve before starting**:
1. Can your Athena++ version compile with both isothermal AND adiabatic EOS?
2. Can you generate HDF5 outputs at Δt = 0.05 tJ without I/O issues?
3. Do you have sufficient disk space (~320 GB) for all HDF5 outputs?
4. Can Ray handle 200 CPUs on your system (12 concurrent × 16 MPI ranks)?

If any answer is NO, adjust specifications before starting.
