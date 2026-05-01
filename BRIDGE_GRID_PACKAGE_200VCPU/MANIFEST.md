# BRIDGE_GRID Campaign - 200 vCPU Package Manifest

**Package Name**: BRIDGE_GRID_PACKAGE_200VCPU
**Version**: 1.0
**Created**: 2026-04-28
**Purpose**: Address Peer Review Issue #3 - BRIDGE_GRID Contradiction

---

## Package Contents

### Configuration Files (48 simulations)

```
bridge_grid/
├── config_BRIDGE_GRID_f1.1_beta0.3_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.1_beta0.3_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.1_beta1.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.1_beta1.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.1_beta5.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.1_beta5.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.2_beta0.3_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.2_beta0.3_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.2_beta1.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.2_beta1.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.2_beta5.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.2_beta5.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.3_beta0.3_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.3_beta0.3_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.3_beta1.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.3_beta1.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.3_beta5.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.3_beta5.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.4_beta0.3_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.4_beta0.3_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.4_beta1.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.4_beta1.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.4_beta5.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.4_beta5.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.5_beta0.3_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.5_beta0.3_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.5_beta1.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.5_beta1.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.5_beta5.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.5_beta5.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.6_beta0.3_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.6_beta0.3_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.6_beta1.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.6_beta1.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.6_beta5.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.6_beta5.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.8_beta0.3_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.8_beta0.3_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.8_beta1.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.8_beta1.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f1.8_beta5.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f1.8_beta5.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f2.0_beta0.3_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f2.0_beta0.3_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f2.0_beta1.0_M1.0_theta90.0_s42.json
├── config_BRIDGE_GRID_f2.0_beta1.0_M1.0_theta90.0_s137.json
├── config_BRIDGE_GRID_f2.0_beta5.0_M1.0_theta90.0_s42.json
└── config_BRIDGE_GRID_f2.0_beta5.0_M1.0_theta90.0_s137.json
```

**Total**: 48 configuration files

### Parameter Coverage

| f | β | M | Seeds | Total |
|---|---|---|-------|-------|
| 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0 (8 values) | 0.3, 1.0, 5.0 (3 values) | 1.0 | 42, 137 | 8 × 3 × 1 × 2 = 48 |

### Execution Scripts

- `run_bridge_grid_200vcpu.py` - Main execution script for 200 vCPU machine
- `analyze_results.py` - Analysis script for extracting λ measurements
- `extract_beading.py` - Peak detection from HDF5 snapshots
- `monitor_progress.py` - Progress monitoring utility
- `compile_athena.sh` - Athena++ compilation script

### Documentation

- `README.md` - Comprehensive setup and execution instructions
- `MANIFEST.md` - This file

---

## Campaign Specifications

### Physical Parameters

- **f (line mass ratio)**: 1.1 to 2.0 (8 values, dense sampling)
- **β (plasma beta)**: 0.3 (weak field), 1.0 (intermediate), 5.0 (strong field)
- **M (Mach number)**: 1.0 (fiducial turbulence)
- **θ (field angle)**: 90° (perpendicular to filament axis)
- **Seeds**: 42, 137 (2 random seeds per parameter point)

### Domain Configuration

- **Longitudinal length**: L = 12λJ (intermediate between standard 8λJ and extended 16λJ)
- **Transverse size**: Ly = Lz = 2λJ
- **Resolution**: 384 × 48 × 48 cells
- **Grid spacing**: Δx = 12/384 λJ = 0.031 λJ

### Output Configuration

- **Timeout**: 600 seconds (wall clock)
- **HST output**: Every 0.01 tJ (high temporal resolution)
- **Snapshot outputs**: Every 0.1 tJ
- **Required fields**: Density, velocity, magnetic field

---

## Computational Requirements

### Hardware

- **CPUs**: 200 vCPU (AMD EPYC 7B13 or similar)
- **RAM**: ~400 GB total (2 GB per simulation)
- **Disk**: ~100 GB for outputs

### Ray Configuration

```python
max_concurrent = 12  # 12 simulations running at once
cores_per_sim = 16   # 16 MPI ranks per simulation
```

### Per-Simulation Resources

- CPUs: 16 cores
- RAM: ~2 GB
- Disk: ~1 GB for HDF5 outputs
- Wall time: ~2-3 hours

### Total Estimated Resources

- **Total simulations**: 48
- **CPU-hours per sim**: ~48 hours (16 cores × 3 hours)
- **Total CPU-hours**: ~2,304
- **Wall time**: ~10 hours (with 12 concurrent)

---

## Expected Outputs

### Per-Simulation

Each simulation produces:

1. **HDF5 snapshots**: Density, velocity, magnetic field evolution
2. **HST files**: Time series of core properties
3. **Status JSON**: Classification (FRAG/STABLE/TIMEOUT)
4. **Log files**: Athena++ output and error logs

### Campaign-Level

After analysis, the campaign produces:

1. **lambda_measurements.csv**: All λ/W measurements with uncertainties
2. **fig_lambda_vs_f.pdf**: λ vs f for all β values
3. **fig_lambda_W_comparison.pdf**: λ/W comparison with HGBS observations
4. **fig_transition_analysis.pdf**: Transition regime characterization
5. **SUMMARY_REPORT.md**: Executive summary of findings

---

## Validation Checks

### Pre-Execution

```bash
# Verify config files
ls bridge_grid/*.json | wc -l  # Should be 48

# Check Athena++ executable
./athena-public-version/bin/athena -h

# Test Python environment
python3 -c "import ray, h5py, numpy, scipy, pandas, matplotlib"
```

### Post-Execution

```bash
# Check completion status
python3 -c "
import json
import glob
results = []
for f in glob.glob('outputs/*/status.json'):
    with open(f) as fp:
        results.append(json.load(fp))
print(f'FRAG: {sum(1 for r in results if r[\"status\"]==\"FRAG\")}')
print(f'STABLE: {sum(1 for r in results if r[\"status\"]==\"STABLE\")}')
print(f'TIMEOUT: {sum(1 for r in results if r[\"status\"]==\"TIMEOUT\")}')
"
```

---

## Integration with Paper

### Files to Copy

After successful completion:

```bash
# Copy results
cp lambda_measurements.csv /path/to/paper/data/
cp figures/*.pdf /path/to/paper/figures/
cp SUMMARY_REPORT.md /path/to/paper/
```

### Paper Updates Required

1. **Abstract**: Mention BRIDGE_GRID campaign
2. **Section 4**: Add BRIDGE_GRID results
3. **Figures**: Include new λ vs f plot
4. **Discussion**: Address referee concern directly

### Response to Referee

> "To address the referee's concern about the contradiction between linear perturbation theory and non-linear MHD results, we performed the BRIDGE_GRID campaign of 48 new simulations densely sampling f = 1.1-2.0. The results show [FINDINGS], which [RESOLVES/CONFIRMS] the contradiction."

---

## Version Control

**Package Version**: 1.0
**Creation Date**: 2026-04-28
**Source Repository**: github.com/Tilanthi/ASTRA-dev
**Branch**: main
**Commit**: [To be filled]

---

## Contact

**Package Creator**: ASTRA autonomous system
**Project Lead**: Tilanthi
**Institution**: [Your institution]
**For questions**: [Contact email]

---

**END OF MANIFEST**
