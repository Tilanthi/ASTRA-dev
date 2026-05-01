# Master Index for Peer Review MHD Simulation Campaign

This document provides a complete index and quick reference for all materials in this package.

## Package Contents

```
peer_review_2026/
├── README.md                                    # Comprehensive usage guide
├── THEORETICAL_REVIEWER_ANALYSIS.md            # Detailed analysis of 6 reviewer concerns
├── MASTER_INDEX.md                             # This file
│
├── simulation_campaigns/                       # Campaign specifications
│   ├── calibration_campaign.json
│   ├── regime_boundary_campaign.json
│   ├── domain_size_campaign.json
│   ├── perpendicular_field_campaign.json
│   ├── physical_turbulence_campaign.json
│   └── eos_asymmetry_campaign.json
│
├── scripts/                                    # Analysis and execution scripts
│   ├── extract_lambda_W.py                     # Extract λ/W from HDF5 snapshots
│   ├── measure_tfrag.py                        # Measure fragmentation times
│   └── run_athena_simulation.sh                # Run single Athena++ simulation
│
└── ray_job_templates/                          # Ray cluster job management
    ├── submit_campaign.sh                      # Submit entire campaign to Ray
    └── monitor_jobs.py                         # Monitor job progress
```

## Quick Reference

### Theoretical Reviewer Concerns

| # | Concern | Priority | Campaign | Simulations |
|---|---------|----------|----------|-------------|
| 1 | λ_frag = 1.11 λ_MJ calibration | CRITICAL | calibration_campaign | 40 |
| 2 | Radial vs. longitudinal conflation | HIGH | regime_boundary_campaign | 60 |
| 3 | Domain size adequacy | MODERATE | domain_size_campaign | 24 |
| 4 | Perpendicular-field λ/W | HIGH | perpendicular_field_campaign | 24 |
| 5 | Non-physical turbulence | MODERATE | physical_turbulence_campaign | 72 |
| 6 | EOS asymmetry interpretation | MODERATE | eos_asymmetry_campaign | 120 |

### Campaign Launch Commands

```bash
# CRITICAL: Calibration campaign
./ray_job_templates/submit_campaign.sh \
    --campaign simulation_campaigns/calibration_campaign.json \
    --output ./results/calibration \
    --cores 200 \
    --concurrent 40

# HIGH: Regime boundary exploration
./ray_job_templates/submit_campaign.sh \
    --campaign simulation_campaigns/regime_boundary_campaign.json \
    --output ./results/regime_boundary \
    --cores 200 \
    --concurrent 30

# HIGH: Perpendicular-field λ/W
./ray_job_templates/submit_campaign.sh \
    --campaign simulation_campaigns/perpendicular_field_campaign.json \
    --output ./results/perpendicular_field \
    --cores 200 \
    --concurrent 40
```

### Analysis Commands

```bash
# Extract λ/W measurements
python scripts/extract_lambda_W.py \
    --simulation_dir ./results/calibration/sim_0001 \
    --output ./results/calibration/sim_0001/lambda_W.json

# Measure t_frag
python scripts/measure_tfrag.py \
    --simulation_dir ./results/calibration/sim_0001 \
    --output ./results/calibration/sim_0001/tfrag.json

# Monitor campaign progress
python ray_job_templates/monitor_jobs.py \
    --results ./results/calibration
```

## File Descriptions

### Core Documentation

**README.md**: Comprehensive guide for running simulations on Ray cluster
**THEORETICAL_REVIEWER_ANALYSIS.md**: Detailed analysis of each reviewer concern
**MASTER_INDEX.md**: This file - quick reference and navigation

### Campaign Specifications

Each JSON file contains:
- Campaign metadata (name, priority, purpose)
- Simulation parameters (f, β, M, seeds, etc.)
- Runtime requirements (timeout, snapshot retention, diagnostics)
- Analysis requirements (what metrics to extract)
- Output specifications (what files to generate)
- Success criteria

### Analysis Scripts

**extract_lambda_W.py**: Extracts λ/W measurements from HDF5 snapshots
- Inputs: Simulation directory, snapshot file
- Outputs: JSON with λ/W measurements and diagnostics
- Methods: Pairwise spacing, Fourier analysis

**measure_tfrag.py**: Measures fragmentation times from time series
- Inputs: Simulation directory
- Outputs: JSON with t_frag measurements
- Methods: Radial collapse, longitudinal beading, timestep watchdog

**run_athena_simulation.sh**: Runs single Athena++ simulation
- Inputs: Config JSON, output directory
- Process: Generates input file, runs Athena++, post-processes
- Outputs: HDF5 snapshots, time series, diagnostics

### Ray Job Templates

**submit_campaign.sh**: Submits entire campaign to Ray cluster
- Inputs: Campaign JSON, output directory, Ray settings
- Process: Parses JSON, generates job list, submits to Ray
- Outputs: Job list, results summary

**monitor_jobs.py**: Monitors Ray job progress
- Inputs: Results directory
- Process: Polls job status, displays progress
- Outputs: Real-time status, summary report

## Parameter Quick Reference

### Common Parameters

| Symbol | Description | Typical Values |
|--------|-------------|----------------|
| f | Line mass (relative to critical) | 1.0 - 3.0 |
| β | Plasma beta parameter | 0.3 - 5.0 |
| M | Mach number | 0.5 - 5.0 |
| γ | Adiabatic index | 0.8 - 5/3 |
| θ | B-field angle to axis | 0° (longitudinal), 90° (perpendicular) |
| seed | Random seed | 42, 43, 44, etc. |

### Domain Specifications

| Campaign | Domain (λ_J³) | Notes |
|----------|---------------|-------|
| Most campaigns | 8 × 2 × 2 | Standard domain |
| Domain size test | 16 × 2 × 2 | Double longitudinal length |

### Resolution

| Resolution | Grid points | Memory per core | Typical runtime |
|------------|-------------|-----------------|-----------------|
| 128³ | 2,097,152 | ~1 GB | 2-6 hours |
| 256³ | 16,777,216 | ~8 GB | 10-20 hours |

## Success Criteria

### Per Campaign

**Calibration**: >95% fragmentation rate, λ/W extracted for all runs
**Regime Boundary**: Clear regime transition identified, separate timescales measured
**Domain Size**: λ/W difference <5% between 8 and 16 λ_J domains
**Perpendicular Field**: λ/W measured for all runs, comparison with longitudinal
**Physical Turbulence**: Both seeding methods tested, impact quantified
**EOS Asymmetry**: EOS behavior mapped across regime boundary

### Overall

- All simulations fragment successfully (except adiabatic cases)
- λ/W measurements extracted for all relevant runs
- t_frag measurements extracted for all runs
- Comparison analyses completed
- Summary reports generated

## Expected Timeline

On a 200-core Ray cluster:

| Campaign | Simulations | Concurrent Jobs | Estimated Runtime |
|----------|-------------|-----------------|-------------------|
| Calibration | 40 | 40 | 2-4 hours |
| Regime Boundary | 60 | 30 | 4-8 hours |
| Domain Size | 24 | 24 | 2-4 hours |
| Perpendicular Field | 24 | 40 | 1-2 hours |
| Physical Turbulence | 72 | 30 | 6-12 hours |
| EOS Asymmetry | 120 | 30 | 10-20 hours |

**Total estimated runtime**: 25-50 hours (1-2 days) for all campaigns

## Output Deliverables

After all campaigns complete, you will have:

1. **HDF5 snapshots**: Full 3D data for all simulations
2. **λ/W measurements**: Extracted for each simulation
3. **t_frag measurements**: Extracted for each simulation
4. **Time series data**: Diagnostic evolution for each simulation
5. **Summary reports**: Per-campaign and overall
6. **Comparison plots**: Where applicable (domain size, turbulence, EOS)
7. **Calibration documentation**: Explicit procedure for λ_frag = 1.11 λ_MJ

## Contact and Support

For questions or issues:
- Check README.md for detailed troubleshooting
- Review THEORETICAL_REVIEWER_ANALYSIS.md for scientific context
- GitHub issues: https://github.com/Tilanthi/ASTRA-dev/

## Version History

- v1.0 (2026-04-25): Initial package created for theoretical reviewer response
