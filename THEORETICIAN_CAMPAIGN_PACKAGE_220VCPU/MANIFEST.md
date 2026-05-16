# THEORETICIAN_CAMPAIGN_PACKAGE_220VCPU - Manifest

**Package Name**: THEORETICIAN_CAMPAIGN_PACKAGE_220VCPU
**Version**: 1.0
**Created**: 2026-05-01
**Purpose**: Address theoretician peer review concerns (Concerns 5, 6, 7)

---

## Package Contents

### Configuration Files (225 simulations)

```
configs/
├── STV/   (75 configs - Supercritical Transition Validation)
│   ├── config_STV_f1.5_beta0.3_M1.0_theta0.0_s42.json
│   ├── config_STV_f1.5_beta0.3_M1.0_theta0.0_s137.json
│   ├── ... (73 more)
│   └── config_STV_f3.0_beta3.0_M1.0_theta0.0_s499.json
│
├── PFS/   (60 configs - Perpendicular-Field Systematics)
│   ├── config_PFS_f1.0_beta0.3_M1.0_theta90.0_s42.json
│   ├── config_PFS_f1.0_beta0.3_M1.0_theta90.0_s137.json
│   ├── ... (58 more)
│   └── config_PFS_f2.0_beta3.0_M1.0_theta90.0_s499.json
│
└── NCRI/  (90 configs - Near-Critical Resolution Investigation)
    ├── config_NCRI_f1.0_beta0.3_M1.0_theta0.0_s42.json
    ├── config_NCRI_f1.0_beta0.3_M1.0_theta0.0_s137.json
    ├── ... (88 more)
    └── config_NCRI_f1.5_beta0.3_M1.0_theta0.0_s251.json
```

### Parameter Coverage

#### STV Campaign (75 simulations)
| Parameter | Values | Count |
|-----------|--------|-------|
| f | 1.5, 1.8, 2.0, 2.5, 3.0 | 5 |
| β | 0.3, 1.0, 3.0 | 3 |
| M | 1.0 | 1 |
| θ | 0° (longitudinal) | 1 |
| Seeds | 42, 137, 251, 367, 499 | 5 |
| **Total** | 5 × 3 × 1 × 1 × 5 | **75** |

#### PFS Campaign (60 simulations)
| Parameter | Values | Count |
|-----------|--------|-------|
| f | 1.0, 1.2, 1.5, 2.0 | 4 |
| β | 0.3, 1.0, 3.0 | 3 |
| M | 1.0 | 1 |
| θ | 90° (perpendicular) | 1 |
| Seeds | 42, 137, 251, 367, 499 | 5 |
| **Total** | 4 × 3 × 1 × 1 × 5 | **60** |

#### NCRI Campaign (90 simulations)
| Parameter | Values | Count |
|-----------|--------|-------|
| f | 1.0, 1.2, 1.3, 1.4, 1.5 | 5 |
| β | 0.3 | 1 |
| M | 1.0 | 1 |
| θ | 0° (longitudinal) | 1 |
| Domain | standard, bridge, long | 3 |
| Resolution | 128³, 256³, 512×64×64 | 3 (varies) |
| Seeds | 42, 137, 251 | 3 |
| **Total** | ~30 (f×domain×res) × 3 seeds | **90** |

---

## Domain Specifications

### STV (Supercritical Transition Validation)
- **Domain**: L = 24λJ × 1.5λJ × 1.5λJ (extended longitudinal)
- **Resolution**: 768 × 64 × 64 cells
- **Purpose**: Capture multiple wavelengths before radial collapse dominates
- **Expected outputs**: Direct λ/W measurements at f ≥ 1.5

### PFS (Perpendicular-Field Systematics)
- **Domain**: L = 16λJ × 1.0λJ × 1.0λJ (longitudinal)
- **Resolution**: 512 × 64 × 64 cells
- **Purpose**: Time-series analysis of beading → collapse evolution
- **Special**: Multiple snapshot outputs (every 0.1 tJ)

### NCRI (Near-Critical Resolution Investigation)
- **Domains**:
  - Standard: 8λJ × 2λJ × 2λJ
  - Bridge: 12λJ × 1.5λJ × 1.5λJ
  - Long: 16λJ × 1λJ × 1λJ
- **Resolutions**: 128³, 256³, 512×64×64 (varies by domain)
- **Purpose**: Identify minimum domain/resolution for reliable beading

---

## Execution Scripts

- `run_campaign.py` - Main Ray execution script
- `monitor_progress.py` - Progress monitoring utility
- `compile_athena.sh` - Athena++ compilation

### Analysis Scripts

- `analyze_stv.py` - STV campaign analysis
- `analyze_pfs.py` - PFS campaign analysis
- `analyze_ncri.py` - NCRI campaign analysis
- `analyze_integrated.py` - Integrated cross-campaign analysis

### Analysis Utilities

- `analysis_utils/extract_beading.py` - Peak detection from HDF5
- `analysis_utils/time_series_analysis.py` - Time evolution tracking
- `analysis_utils/classification.py` - Quantitative GOOD/FLAT criteria
- `analysis_utils/statistical_tests.py` - χ², bootstrap, Bayesian

---

## Computational Requirements

### Hardware
- **CPUs**: 220 vCPU (AMD EPYC 7B13 or similar)
- **RAM**: ~400 GB total
- **Disk**: ~500 GB for outputs

### Ray Configuration
```python
max_concurrent = 12  # 12 simulations running at once
cores_per_sim = 16   # 16 MPI ranks per simulation
total_cores = 192    # Leaves headroom for system
```

### Resource Estimates

| Campaign | Simulations | Wall Time (each) | Total CPU Hours |
|----------|-------------|------------------|-----------------|
| STV | 75 | 2-3 hours | ~2,400 |
| PFS | 60 | 2 hours | ~1,920 |
| NCRI | 90 | 1-2 hours | ~1,440 |
| **Total** | **225** | - | **~5,760** |

### Wall Time Estimate
- **With 12 concurrent**: ~5,760 CPU-hours / 192 cores = ~30 hours
- **With overhead**: ~40-45 hours (2 days)

---

## Expected Outputs

### Per-Simulation Outputs

Each simulation produces:
1. **HDF5 snapshots**: Density, velocity, magnetic field
2. **HST files**: Time series of global quantities
3. **Status JSON**: Classification and metadata
4. **Log files**: Athena++ output

### Campaign-Level Outputs

After analysis:

#### STV
- `lambda_vs_f.csv`: λ/W measurements with uncertainties
- `extrapolation_test.json`: Comparison with near-critical calibration
- `stv_summary.pdf`: λ/W vs f for all β values

#### PFS
- `time_evolution_maps.pdf`: Beading probability vs (f, β, t)
- `classification_summary.json`: GOOD/FLAT/RADIAL_COLLAPSE counts
- `phase_diagram.pdf`: (f, β) parameter space

#### NCRI
- `domain_resolution_study.pdf`: Recovery of beading
- `requirements_analysis.json`: Minimum domain/resolution
- `campaign8_explanation.pdf`: Why FLAT entries occur

#### Integrated
- `INTEGRATED_ANALYSIS.md`: Cross-campaign synthesis
- `CALIBRATION_REVISION.md`: Updated λ_frag calibration
- `RECOMMENDATIONS.md`: Minimum requirements for future campaigns

---

## Success Criteria

### STV Campaign
- [ ] Direct λ/W measurements at all f ≥ 1.5 values
- [ ] Quantified uncertainties from seed-to-seed variation
- [ ] Statistical test of extrapolation (χ² or similar)
- [ ] Either validates or revises λ_frag = 1.11 λ_MJ

### PFS Campaign
- [ ] Clear definition of "GOOD" measurement criteria
- [ ] Time-evolution maps showing beading → collapse
- [ ] Assessment of λ/W = 1.25 representativeness
- [ ] Phase diagram of perpendicular-field fragmentation

### NCRI Campaign
- [ ] Explanation of FLAT entries at f=1.5, β=0.3
- [ ] Domain size and/or resolution requirements identified
- [ ] Confirmation that Phase 1 results are robust
- [ ] Minimum requirements for reliable λ/W measurements

---

## Integration with Paper

### New Sections
1. "Supercritical Fragmentation: Direct λ/W Measurements"
2. "Perpendicular-Field Fragmentation: Time Evolution"
3. "Minimum Requirements for Reliable Measurements"

### New Figures
1. λ/W vs f curve (direct measurements, not extrapolation)
2. Perpendicular-field phase diagram
3. Domain/resolution convergence plot
4. Integrated comparison with HGBS (λ/W = 2.05)

### Referee Response
> "To address Concern 5, we performed 75 new simulations with f = 1.5-3.0, finding [result]. To address Concern 6, we performed 60 perpendicular-field simulations with time-series analysis, showing [result]. To address Concern 7, we performed 90 simulations testing domain size and resolution effects, identifying [explanation]."

---

## Version Control

**Package Version**: 1.0
**Creation Date**: 2026-05-01
**Source**: ASTRA-dev repository
**Branch**: main
**Configs Generated**: 2026-05-01

---

## Contact

**Package Creator**: ASTRA autonomous system
**Project Lead**: Tilanthi
**For Questions**: Refer to plan at `/Users/gjw255/.claude/plans/shimmering-gliding-breeze.md`

---

**END OF MANIFEST**
