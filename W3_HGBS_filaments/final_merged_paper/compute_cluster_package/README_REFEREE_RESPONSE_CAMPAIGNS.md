# Referee Response Simulation Campaigns

## Overview

This package contains three targeted Athena++ simulation campaigns designed to address specific concerns raised in the referee report for "Fragmentation of Interstellar Filaments: Complete HGBS Analysis and MHD Simulations."

**Date**: 30 April 2026
**Target Journal**: MNRAS
**Total Simulations**: 289 (54 + 100 + 135)

## Campaign Summary

| Campaign ID | Focus | Simulations | Referee Concern | Priority |
|-------------|-------|-------------|-----------------|----------|
| **C5** | Turbulence λ/W Measurements | 54 | Moderate Concern 8 | **HIGHEST** |
| **C6** | Perpendicular-B β-Dependence | 100 | Moderate Concern 9 | HIGH |
| **C7** | Critical Transition Mapping | 135 | Major Concern 2 | MEDIUM |

### Campaign 5: Turbulence λ/W Measurements (C5_TURBULENCE_LW)

**Referee Quote**: "The finding that realistic turbulence (δv/cs = 1.0) accelerates collapse by a factor of 3-5× is potentially important, but the interpretation requires care. [...] the fragmentation wavelength λ/W was not measured in these runs, and rightly qualifies the 10-15″ angular scale estimate as speculative. However, the implications for the primary theoretical question — whether turbulence modifies the fragmentation wavelength — are left entirely open. Either the wavelength should be measured in follow-up runs, or this sub-campaign should be presented more explicitly as a preliminary result motivating future work, with reduced prominence in the abstract and conclusions."

**Scientific Goal**: Directly measure whether realistic turbulence modifies the fragmentation wavelength λ/W, not just the fragmentation timescale.

**Parameter Space**:
- Mass-to-flux ratio f: 1.0, 1.1, 1.2 (near-critical regime where λ/W is measurable)
- Plasma beta β: 0.5, 1.0, 2.0 (weak to strong B-field)
- Turbulence types:
  - `turbphys`: δv/cs = 1.0 (realistic ISM turbulence, Kolmogorov spectrum)
  - `turbsynth`: δv/cs = 1e-4 (synthetic perturbations, baseline for comparison)
- Random seeds: 3 per parameter point

**Key Comparison**: λ/W_turbphys vs λ/W_turbsynth at identical (f, β)
- If Δλ/W ≠ 0: Turbulence modifies fragmentation wavelength → Major implications for theory-observation comparison
- If Δλ/W ≈ 0: λ/W set by equilibrium properties, not perturbation amplitude → Validates synthetic perturbation approach

**Expected Outcome**: Direct resolution of whether turbulence is a first-order parameter for fragmentation wavelength.

### Campaign 6: Perpendicular-B β-Dependence (C6_PERP_BETA)

**Referee Quote**: "Section 4.7.3 reports a clear β-dependence in the near-critical longitudinal-field measurements: λ/W = 3.86 ± 0.54 at β = 0.5, dropping to 2.79 ± 0.32 at β = 2.0. This range (2.79-3.86) spans the observational result and is in principle a strong discriminant between field strength regimes. Yet this is not developed into a quantitative constraint on HGBS filament plasma beta."

**Scientific Goal**: Map λ/W(β) for perpendicular-field filaments (90% of HGBS filaments per Planck) and improve statistical reliability of perpendicular-B λ/W measurements.

**Current Limitation**: Apr2026 Campaign 1 measured λ/W for perpendicular-B at β=0.5 only (λ/W = 2.97 ± 0.86, N=3). The β-dependence for PERPENDICULAR fields remains UNKNOWN.

**Parameter Space**:
- Field geometry: θ = 90° (perpendicular to filament axis)
- Mass-to-flux ratio f: 1.2, 1.3, 1.4, 1.5 (near-critical window where perpendicular-B λ/W is measurable)
- Plasma beta β: 0.3, 0.5, 1.0, 1.5, 2.0 (extended sampling vs Apr2026's single β=0.5)
- Random seeds: 5 per parameter point (improved statistics vs Apr2026's 3 seeds)
- Domain: 16λ_J × 1λ_J × 1λ_J (extended axial domain)
- Resolution: 512 × 64 × 64 (32 cells/λ_J)

**Key Scientific Questions**:
1. Does perpendicular-B λ/W show β-dependence similar to longitudinal-B?
2. What is the critical β_c(f) where radial collapse begins to dominate?
3. How does field geometry (parallel vs perpendicular) affect the β-dependence?

**Expected Outcomes**:
- Scenario A: Strong β-dependence (similar to longitudinal-B) → Magnetic pressure modifies λ/W even without magnetic tension
- Scenario B: Weak β-dependence → Perpendicular-B fragmentation dominated by thermal Jeans physics
- Scenario C: Measurements only feasible at low β → Physical constraint on measurability

### Campaign 7: Critical Transition Mapping (C7_CRITICAL_TRANSITION)

**Referee Quote**: "The paper's most important theoretical result — that ideal MHD cannot reproduce the observed sub-Jeans spacing — relies on an extrapolation that the authors themselves flag as 'the single largest source of systematic uncertainty.' The λ/W ≈ 3.70 prediction from the field-geometry calibration is derived from near-critical simulations (f = 1.0–1.2) and extrapolated to the supercritical regime (f ≥ 1.5) where HGBS filaments nominally reside."

**Scientific Goal**: Map the λ/W vs f relationship across the critical transition (f = 0.9-1.3) to resolve the regime mismatch between simulations and observations.

**Parameter Space**:
- Mass-to-flux ratio f: 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3 (fine sampling in critical transition)
- Plasma beta β: 0.3, 0.5, 1.0, 1.5, 2.0 (spanning the observed λ/W range)
- Field geometry: θ = 0° (longitudinal, for baseline comparison)
- Random seeds: 3 per parameter point

**Key Scientific Products**:
1. λ/W(f) curves for each β value (5 curves total)
2. Critical f_threshold where fragmentation begins (sub-critical → near-critical)
3. f-dependence of λ/W in the near-critical regime
4. Calibration for extrapolating to supercritical regime

**Expected Outcome**: Direct constraint on which mass-to-flux regime HGBS filaments occupy, reducing the current extrapolation uncertainty.

## Installation and Setup

### Prerequisites

1. **Athena++**: Install or symlink the Athena++ binary
   ```bash
   export ATHENA_BIN=/path/to/athena/bin/athena
   ```

2. **Python Dependencies**:
   ```bash
   pip install numpy scipy h5py pandas matplotlib pyyaml
   ```

3. **Cluster Access**: 200 vCPU cluster (or adjust max_parallel accordingly)

### Directory Structure

```
compute_cluster_package/
├── referee_response_campaign_runner.py          # Main runner script
├── campaign5_turbulence_lambda_W_specification.yaml
├── campaign6_perpendicular_beta_dependence_specification.yaml
├── campaign7_critical_transition_specification.yaml
├── README_REFEREE_RESPONSE_CAMPAIGNS.md         # This file
└── analysis/
    └── measure_lambda_W.py                      # λ/W measurement script
```

## Running the Campaigns

### Quick Start: Run All Campaigns

```bash
python referee_response_campaign_runner.py --all --max-parallel 25
```

This will run Campaigns 5, 6, and 7 sequentially, with up to 25 parallel simulations each.

### Run Individual Campaign

```bash
# Campaign 5: Turbulence λ/W measurements
python referee_response_campaign_runner.py \
    --campaign C5 \
    --config campaign5_turbulence_lambda_W_specification.yaml \
    --max-parallel 25

# Campaign 6: Perpendicular-B β-dependence
python referee_response_campaign_runner.py \
    --campaign C6 \
    --config campaign6_perpendicular_beta_dependence_specification.yaml \
    --max-parallel 12  # Reduced due to higher memory per sim

# Campaign 7: Critical transition mapping
python referee_response_campaign_runner.py \
    --campaign C7 \
    --config campaign7_critical_transition_specification.yaml \
    --max-parallel 25
```

### Monitor Progress

Each campaign creates a `campaign_summary.json` file with real-time progress:

```bash
# Check Campaign 5 progress
tail -f C5_TURBULENCE_LW/logs/*.log

# Check campaign summary
cat C5_TURBULENCE_LW/campaign_summary.json
```

## Computational Requirements

### Per-Campaign Resource Requirements

| Campaign | Simulations | Cores/Sim | Total Cores | Walltime | Memory |
|----------|-------------|-----------|-------------|----------|--------|
| C5 | 54 | 8 | 200 (25 parallel) | ~9 hours | 16 GB/sim |
| C6 | 100 | 16 | 192 (12 parallel) | ~2 days | 32 GB/sim |
| C7 | 135 | 8 | 200 (25 parallel) | ~22 hours | 16 GB/sim |

### Total Cluster Requirements

- **Total Simulations**: 289
- **Total Core-Hours**: ~2,300 (approximately 96 hours on 24 cores)
- **Disk Space**: ~50 GB (including HDF5 snapshots)
- **Peak Memory**: ~600 GB (if running C6 at full parallelism)

## Output and Analysis

### Campaign Output Structure

```
C5_TURBULENCE_LW/
├── C5_TURB_f1.0_b0.5_turbphys_s42/
│   ├── athena_config.dat
│   ├── *.hdf5                                 # HDF5 snapshots
│   └── lambda_W_summary.json                  # Analysis output
├── logs/
├── output/
│   └── lambda_W_analysis.json                 # Combined analysis
└── campaign_summary.json
```

### Analysis Scripts

After campaign completion, run the λ/W extraction script:

```bash
python analysis/measure_lambda_W.py C5_TURBULENCE_LW/C5_TURB_f1.0_b0.5_turbphys_s42
```

This generates `lambda_W_summary.json` for each simulation with:
- `lambda_W`: Fragmentation wavelength in units of W
- `lambda_W_std`: Standard deviation of peak spacings
- `t_frag`: Fragmentation time in units of t_J
- `n_peaks`: Number of fragmentation peaks
- `quality_flag`: GOOD, FEW_PEAKS, SPURIOUS, or NO_PEAKS

## Scientific Impact

### How These Campaigns Address Referee Concerns

1. **Moderate Concern 8 (Turbulence λ/W Gap)**: Campaign 5 directly measures whether turbulence modifies λ/W, resolving the "entirely open" question about turbulence implications for the primary theoretical comparison.

2. **Moderate Concern 9 (β-Dependence Underexplored)**: Campaign 6 maps λ/W(β) for perpendicular-B filaments (90% of HGBS filaments), providing "a strong discriminant between field strength regimes" that can be used to "quantitatively constrain HGBS filament plasma beta."

3. **Major Concern 2 (Regime Mismatch)**: Campaign 7 maps the critical transition, resolving the "single largest source of systematic uncertainty" in the paper's theoretical comparison.

### Expected Paper Revisions

With results from these campaigns, the paper will be able to:

1. **Replace speculative turbulence statements** with direct λ/W measurements: "Either the wavelength should be measured in follow-up runs" → **Campaign 5 provides these measurements**

2. **Develop β-dependence into quantitative constraint**: Current paper states "This range (2.79-3.86) spans the observational result" but doesn't use it quantitatively. → **Campaign 6 provides perpendicular-B λ/W(β) calibration for constraint**

3. **Reduce extrapolation uncertainty**: Current paper flags λ/W extrapolation as "the single largest source of systematic uncertainty." → **Campaign 7 provides λ/W(f) calibration across the critical transition**

4. **Strengthen perpendicular-B statistics**: Current paper has N=3 genuine perpendicular-B λ/W measurements, which the referee notes "is a limitation." → **Campaign 6 provides N=~15-25 genuine measurements**

## Timeline

- **Campaign 5 (54 sims)**: ~9 hours on 200 cores
- **Campaign 6 (100 sims)**: ~2 days on 200 cores
- **Campaign 7 (135 sims)**: ~22 hours on 200 cores
- **Total**: ~3-4 days of cluster time

**Recommended Execution Order**:
1. Campaign 5 (highest priority per referee)
2. Campaign 6 (high priority, addresses perpendicular-B gap)
3. Campaign 7 (medium priority, calibrates extrapolation)

## Troubleshooting

### Common Issues

1. **Out of Memory Errors**:
   - Reduce max_parallel for Campaign 6 (from 12 to 8)
   - Check available memory with `free -h`

2. **Timeout Errors**:
   - Increase timeout in campaign specification YAML
   - Check if simulations are actually running (monitor `top`)

3. **HDF5 File Corruption**:
   - Check disk space with `df -h`
   - Reduce output frequency (increase `hdf5_dt`)

4. **Analysis Script Fails**:
   - Verify HDF5 snapshots exist: `ls -lh C5_TURB_*/Final*.hdf5`
   - Check snapshot content: `h5dump -h C5_TURB_*/Final*.hdf5`

## Contact and Support

For questions or issues with these campaigns, contact:
- **Author**: Glenn J. White (Open University)
- **Date**: 30 April 2026
- **Repository**: https://github.com/Tilanthi/ASTRA-dev

## References

1. Inutsuka & Miyama (1992): Fragmentation of isothermal gas cylinders
2. Nagasawa (1987): Linear stability analysis of magnetized filaments
3. Planck Collaboration (2016): Magnetic field geometries in HGBS filaments

---

**End of Documentation**
