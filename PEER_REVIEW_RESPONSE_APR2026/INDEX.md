# PEER REVIEW RESPONSE MHD CAMPAIGN
# Complete Simulation Package for External 200-CPU Computer

## Overview

This campaign of **320 new Athena++ MHD simulations** is designed to address the four critical gaps identified in the peer review assessment:

1. **T3**: No perpendicular field simulations (90% of observed filaments have perpendicular B-fields)
2. **T1/T2**: Limited near-critical regime (f<1.4 not tested)
3. **T9**: No oblique field calibration (λ_frag = 1.11 λ_MJ not validated)
4. **T2**: No longitudinal peak detection (need to explicitly measure λ_frag from HDF5 snapshots)

---

## Campaign Structure

```
peer_review_response_APR2026/
├── INDEX.md                           # This file
├── run_campaign.sh                    # Master launch script
│
├── config/
│   ├── campaign_specification.json    # Campaign metadata
│   ├── simulation_manifest.json       # Complete simulation list
│   └── athena_config.json             # Athena++ configuration
│
├── scripts/
│   ├── launch_campaign.py             # Ray-based parallel execution
│   ├── analyze_campaign.py            # Analysis and figure generation
│   ├── compile_athena.sh              # Athena++ compilation script
│   └── extract_lambda.py              # Longitudinal peak detection
│
├── templates/
│   ├── athena_input_template.dat      # Athena++ input file template
│   └── filament_spacing_pr.cpp        # Problem generator source code
│
└── docs/
    ├── README.md                       # Complete documentation
    ├── QUICKSTART.md                   # Quick start guide
    └── DATA_RETURN_SPEC.md            # Required outputs for paper
```

---

## Campaign Specifications

### Phase 1: Near-Critical Campaign (80 simulations)

**Objective**: Address T1/T2 by testing f = 0.9--1.2 where longitudinal fragmentation should occur before radial collapse.

**Parameter space**:
- f = 0.9, 1.0, 1.05, 1.1, 1.15, 1.2 (near-critical to marginally supercritical)
- β = 0.3, 0.5, 0.7, 1.0, 1.5, 2.0
- M = 1.0, 2.0
- Seeds = {1, 2, 3}
- EOS = isothermal
- B-field = longitudinal
- Domain = 8×2×2 λJ
- Resolution = 256³

**Total**: 6×6×2×3 = **216 simulations** (reduced to 80 for core subset)

**Core subset (80 sims)**:
- f = 1.0, 1.05, 1.1, 1.15, 1.2
- β = 0.3, 0.5, 0.7, 1.0
- M = 1.0, 2.0
- Seeds = {1, 2}

**Key questions**:
1. At what f does longitudinal beading emerge before radial collapse?
2. What is the threshold f for beading detection?
3. How does t_frag depend on f and β in the near-critical regime?

**Success criteria**:
- At least one simulation shows ≥2 longitudinal peaks
- Direct measurement of λ_frag from HDF5 snapshots
- Characterization of the fragmentation threshold

---

### Phase 2: Perpendicular Field Campaign (96 simulations)

**Objective**: Address T3 by testing the magnetic geometry that applies to 90% of HGBS filaments.

**Parameter space**:
- f = 1.5, 2.0, 2.5, 3.0
- β = 0.3, 0.5, 0.7, 1.0, 1.5, 2.0
- M = 1.0, 2.0
- Seeds = {1, 2}
- B-field = perpendicular (θ = 90° to filament axis)
- Domain = 8×2×2 λJ
- Resolution = 256³

**Total**: 4×6×2×2 = **96 simulations**

**Key questions**:
1. Does perpendicular B suppress radial collapse and allow longitudinal beading?
2. What is the fragmentation spacing λ/W for perpendicular fields?
3. Does λ/W match HGBS observations better for perpendicular fields?

**Success criteria**:
- Direct measurement of λ_frag for perpendicular fields
- Comparison of λ/W between longitudinal and perpendicular geometries
- Statistical assessment of which geometry better matches HGBS (λ/W = 2.1)

---

### Phase 3: Oblique Field Calibration (90 simulations)

**Objective**: Address T9 by validating the λ_frag = 1.11 λ_MJ calibration for oblique field geometries.

**Parameter space**:
- θ = 30°, 45°, 60° (angle between B and filament axis)
- f = 1.5, 2.0, 2.5
- β = 0.5, 1.0, 2.0
- M = 1.0
- Seeds = {1, 2}
- B-field = oblique (B_x = B cosθ, B_y = B sinθ)
- Domain = 8×2×2 λJ
- Resolution = 256³

**Total**: 3×3×3×1×2 = **54 simulations**

**Extended subset (90 sims)**:
- Additional variations in M = 2.0 for selected points

**Key questions**:
1. Does the calibration λ_frag = 1.11 λ_MJ hold for oblique fields?
2. How does λ_frag vary with θ?
3. What is the optimal θ to match HGBS observations?

**Success criteria**:
- Direct measurement of λ_frag for θ = 30°, 45°, 60°
- Validation of λ_frag = 1.11 λ_MJ across field geometries
- Determination of which θ best reproduces λ/W = 2.1

---

### Phase 4: Near-Critical Adiabatic Extension (54 simulations)

**Objective**: Test whether adiabatic EOS (γ = 5/3) allows longitudinal fragmentation by slowing radial collapse.

**Parameter space**:
- f = 1.0, 1.05, 1.1, 1.15, 1.2
- β = 0.5, 1.0
- M = 1.0
- Seeds = {1, 2, 3}
- EOS = adiabatic (γ = 5/3)
- B-field = longitudinal
- Domain = 8×2×2 λJ
- Resolution = 256³

**Total**: 5×2×1×3 = **30 simulations**

**Core subset**: Selected points for robustness testing (54 sims total)

**Key questions**:
1. Does adiabatic EOS slow radial collapse enough for longitudinal beading?
2. How does λ_frag differ between isothermal and adiabatic cases?
3. Is the beading threshold f different for adiabatic EOS?

**Success criteria**:
- Comparison of beading emergence between isothermal and adiabatic
- Measurement of λ_frag for adiabatic cases
- Assessment of whether adiabatic EOS changes the fragmentation threshold

---

## Computational Requirements

**Platform**: 200 CPU system (AMD EPYC 7B13 or similar)

**Ray configuration**:
```python
ray.init(num_cpus=200)
max_concurrent = 12  # 12 concurrent simulations
mpi_ranks_per_sim = 16  # 16 MPI ranks per simulation
```

**Per-simulation resources**:
- CPUs: 16 MPI ranks
- RAM: ~2 GB
- Disk: ~1 GB for HDF5 outputs
- Wall time: 2-4 hours (adiabatic runs longer)

**Estimated total wall time**:
- Phase 1: 80 sims × 3 h = 240 h / 12 concurrent = 20 h
- Phase 2: 96 sims × 3 h = 288 h / 12 concurrent = 24 h
- Phase 3: 90 sims × 3 h = 270 h / 12 concurrent = 22.5 h
- Phase 4: 54 sims × 4 h = 216 h / 12 concurrent = 18 h
- **Total**: ~85 hours (3.5 days) of wall-clock time

---

## Output Requirements

### Critical Deliverables

1. **simulation_catalog.csv** - Master catalog of all 320 simulations
2. **fig1_beading_threshold.pdf** - Map showing where longitudinal beading emerges
3. **fig2_lambda_W_comparison.pdf** - λ/W vs field geometry
4. **fig3_oblique_calibration.pdf** - Validation of λ_frag = 1.11 λ_MJ
5. **fig4_nearcritical_adia.pdf** - Isothermal vs adiabatic comparison
6. **SUMMARY_REPORT.md** - Response to each peer review concern

### Per-Simulation Data

For each simulation, the status JSON must include:
```json
{
  "sim_id": "example_sim",
  "status": "FRAG" | "STABLE" | "TIMEOUT",
  "t_frag": 0.35,
  "dt_min": 1.2e-8,
  "rho_c_max": 245.3,
  "longitudinal_peaks": 3,
  "peak_positions": [128, 256, 384],
  "peak_amplitudes": [2.34, 2.56, 2.12],
  "lambda_frag": 1.23,
  "lambda_frag_uncertainty": 0.08,
  "fragmentation_quality": "excellent",
  "wall_time_seconds": 7200,
  "hdf5_outputs": 15
}
```

### HDF5 Snapshot Requirements

- **Output interval**: Δt = 0.05 tJ
- **Minimum snapshots**: 15 per simulation
- **Required data**: Density, velocity, magnetic field
- **Analysis**: Automated peak detection from density profiles

---

## Success Criteria

The campaign will be considered successful if it demonstrates:

1. **Longitudinal beading detection**: At least one regime shows ≥2 longitudinal peaks
2. **Perpendicular field λ_frag**: Direct measurement of λ/W for perpendicular fields
3. **Oblique calibration validation**: Confirmation of λ_frag = 1.11 λ_MJ across θ
4. **Near-critical characterization**: Identification of the beading threshold f
5. **EOS comparison**: Assessment of isothermal vs adiabatic fragmentation

---

## Execution Instructions

### Preparation (First time only)

```bash
# Extract package
tar -xzf peer_review_response_APR2026.tar.gz
cd peer_review_response_APR2026

# Compile Athena++
bash scripts/compile_athena.sh

# Verify Ray installation
python3 -c "import ray; print(ray.__version__)"
```

### Execution

```bash
# Interactive mode (recommended)
bash run_campaign.sh

# Direct Python execution
python3 scripts/launch_campaign.py --phase 1      # Near-critical only
python3 scripts/launch_campaign.py --phase 1-2    # Near-critical + perpendicular
python3 scripts/launch_campaign.py --all          # Full campaign
```

### Analysis

```bash
# After simulations complete
python3 scripts/analyze_campaign.py
```

---

## Integration with Paper

After successful campaign completion:

1. **Copy analysis outputs**:
   ```bash
   cp analysis_output/fig*.pdf /path/to/paper/figures/
   cp analysis_output/SUMMARY_REPORT.md /path/to/paper/
   ```

2. **Update paper sections**:
   - Abstract: Mention new simulations addressing concerns
   - Section 4: Add perpendicular field and oblique calibration results
   - Section 5: Update discussion with new evidence
   - Conclusions: Revise with new findings

3. **Generate response to reviewer**:
   - Document how each concern was addressed
   - Cite specific simulations showing beading
   - Include figures demonstrating perpendicular field fragmentation

---

## Version History

- **v1.0** (2026-04-23): Initial campaign specification
  - Addresses 4 critical peer review gaps
  - 320 simulations across 4 phases
  - Estimated 85 hours wall time

---

**Campaign prepared by**: ASTRA autonomous system
**Date**: 23 April 2026
**Purpose**: Peer review response for MNRAS filament spacing paper
