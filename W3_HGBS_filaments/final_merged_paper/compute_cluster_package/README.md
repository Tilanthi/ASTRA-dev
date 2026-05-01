# ASTRA Filament Simulation Package
## For Peer Review Response and Critical Gap Resolution

**Date**: 29 April 2026  
**Purpose**: Definitive tests to address all peer review concerns  
**Status**: Ready for deployment on compute cluster

---

## Quick Start

### 1. Extract the package
```bash
tar -xzf compute_cluster_simulation_specs.tar.gz
cd compute_cluster_simulation_specs/
```

### 2. Install dependencies
```bash
# Create conda environment
conda create -n athena_sims python=3.10 -y
conda activate athena_sims

# Install Python packages
pip install -r requirements.txt

# Verify Ray installation
ray start --head
```

### 3. Configure for your cluster
Edit `cluster_config.yaml` to match your cluster setup:
- Adjust `max_workers` for your available cores
- Configure file paths in `file_mounts` section
- Update resource limits if needed

### 4. Run a test simulation
```bash
# Test single simulation
python run_single_simulation.py --campaign campaign1 --f 1.5 --beta 1.0

# Verify output
python analysis/measure_lambda_W.py outputs/campaign1_PERP_f1.5_beta1.0_seed1/
```

### 5. Run full campaign
```bash
# Campaign 1: Perpendicular-field λ/W measurements
python run_campaign.py --campaign campaign1 --parallel

# Monitor progress
ray status
```

---

## Package Contents

```
compute_cluster_simulation_specs/
├── README.md                          # This file
├── SPECIFICATION.md                   # Full specification document
├── requirements.txt                   # Python dependencies
├── cluster_config.yaml                # Ray cluster configuration
├── run_campaign.py                    # Campaign execution script
├── run_single_simulation.py           # Single simulation test
│
├── analysis/
│   ├── measure_lambda_W.py           # λ/W measurement (PRIMARY)
│   ├── measure_dispersion.py         # Dispersion relation (Campaign 3)
│   ├── bundle_projection.py          # Multi-fibre projection (Campaign 2)
│   ├── compile_results.py            # Campaign summary
│   └── validate_results.py           # Quality control
│
└── templates/
    ├── athena_input_perp.inp         # Template: Campaign 1
    ├── athena_input_bundle.inp       # Template: Campaign 2
    ├── athena_input_nonideal.inp     # Template: Campaign 3
    └── athena_input_nearcrit.inp     # Template: Campaign 4
```

---

## Campaign Descriptions

### Campaign 1: Perpendicular-Field λ/W Measurements (HIGHEST PRIORITY)

**Objective**: Measure fragmentation wavelength for θ = 90° magnetic field

**Key Question**: Does perpendicular-field fragmentation produce λ/W ≈ 4.0 or λ/W ≈ 2.8?

**Parameter Space**:
- f: 1.2, 1.5, 2.0, 2.5
- β: 0.5, 1.0, 2.0, 3.0
- Seeds: 3 per parameter point
- **Total**: 96 simulations

**Runtime**: 6 hours per simulation × 96 = 576 core-hours

**Critical Setup**:
```python
# MUST use extended runtime
max_time = 2.5  # t_J units (vs. previous 1.0)
wallclock = 21600  # 6 hours

# MUST use dense snapshots
snapshot_interval = 0.05  # t_J
snapshot_start = 0.5  # t_J
```

**Expected Output**: λ/W for each (f, β) combination with quality flags

---

### Campaign 2: Multi-Fibre Bundle Simulations (SECONDARY PRIORITY)

**Objective**: Test hierarchical structure explanation

**Key Question**: Does √N_fibres compression produce λ/W ≈ 2.8?

**Parameter Space**:
- N_fibres: 1, 2, 4, 6, 8
- Separation: 1.5, 2.0, 2.5 W
- f: 1.2, 1.5
- β: 1.0, 2.0
- **Total**: 120 simulations (subset of full space)

**Runtime**: 8 hours per simulation × 120 = 960 core-hours

**Critical Setup**:
```python
# Bundle geometry
geometry = 'cylinder_bundle'
arrangement = 'hexagonal_close_packed'
fibre_radius = 0.5 * W
separation = variable  # 1.5-2.5 W
```

**Expected Output**: Apparent λ/W vs. N_fibres, compression factor

---

### Campaign 3: Non-Ideal MHD Linear Growth (TERTIARY PRIORITY)

**Objective**: Test ambipolar diffusion effects on fragmentation wavelength

**Key Question**: Does λ increase or decrease with non-ideal coupling?

**Parameter Space**:
- f: 1.0, 1.2, 1.5
- x_e: 1e-7, 3e-7, 1e-6
- χ_AD: 0.1, 0.5, 1.0
- β: 0.5, 1.0, 2.0
- **Total**: 80 simulations

**Runtime**: 12 hours per simulation × 80 = 960 core-hours

**Critical Setup**:
```python
# Non-ideal MHD module
ambipolar_diffusion: true
hall_effect: true  # can disable if unstable

# STOP AT LINEAR GROWTH
max_time = 1.0  # t_J (stop before non-linear)
snapshot_interval = 0.05  # t_J
```

**Expected Output**: Dispersion relation σ(k) and λ_max for each parameter

---

### Campaign 4: Near-Critical λ/W Calibration (VALIDATION PRIORITY)

**Objective**: Validate baseline λ/W measurements for f ≤ 1.2

**Key Question**: Do near-critical simulations produce λ/W ≈ 3.5-4.0?

**Parameter Space**:
- f: 1.00, 1.05, 1.10, 1.15, 1.20
- β: 0.5, 1.0, 2.0
- Resolution: 128, 256
- **Total**: 90 simulations

**Runtime**: 4 hours per simulation × 90 = 360 core-hours

**Expected Output**: λ/W baseline for field-geometry calibration

---

## Execution Order

### Phase 1: Week 1-2 (Immediate)
- Campaign 4 (Near-Critical) - Quick validation
- Campaign 1 (Perpendicular) - Primary gap

**Parallel execution**: Can run simultaneously on different nodes

### Phase 2: Weeks 3-6 (Conditional)
- Campaign 2 (Multi-fibre) - Only if Campaign 1 warrants

**Trigger**: Campaign 1 shows λ/W ≠ 2.8

### Phase 3: Weeks 7-10 (Tertiary)
- Campaign 3 (Non-Ideal) - Only if needed

**Trigger**: Campaigns 1+2 inconclusive OR referee request

---

## Output Format

### Primary Results File
Each simulation produces `lambda_W_summary.json`:
```json
{
    "simulation_id": "PERP_f1.5_beta1.0_res128_seed1",
    "final_lambda_W": 3.7,
    "final_quality_flag": "GOOD",
    "n_peaks": 5,
    "parameters": {
        "f": 1.5,
        "beta": 1.0,
        "resolution": 128
    }
}
```

### Campaign Summary
Each campaign produces `campaign_summary.json`:
```json
{
    "campaign": "campaign1_perp_lambda",
    "n_simulations": 96,
    "n_successful": 84,
    "mean_lambda_W": 3.7,
    "comparison_with_observation": {
        "observed": 2.8,
        "simulated": 3.7,
        "overlap": true
    }
}
```

---

## Quality Control

### Pre-Simulation Checks
```bash
# Validate simulation setup
python analysis/validate_results.py --check setup campaign1/
```

### Post-Simulation Validation
```bash
# Validate results
python analysis/validate_results.py campaign1/
```

### Quality Flags
- `GOOD`: >= 3 peaks, consistent spacing
- `FEW_PEAKS`: 1-2 peaks, unreliable statistics
- `NO_PEAKS`: No longitudinal structure (radial collapse only)

---

## Troubleshooting

### Issue: "NO_PEAKS" quality flag
**Cause**: Simulation stopped too early (radial collapse dominated)

**Solution**: Increase runtime:
```python
max_time = 3.0  # t_J (extend from 2.5)
wallclock = 28800  # 8 hours
```

### Issue: Ray cluster won't start
**Cause**: Port conflicts or resource limits

**Solution**: 
```bash
# Kill existing Ray processes
ray stop

# Clear Ray socket
rm -rf /tmp/ray

# Restart with explicit port
ray start --head --port=6379
```

### Issue: Out of memory
**Cause**: Too many parallel simulations

**Solution**: Reduce `max_workers` in `cluster_config.yaml`

---

## Contact and Support

For questions about:
- **Simulation setup**: See `templates/` directory
- **Analysis scripts**: See `analysis/` directory
- **Ray configuration**: See `cluster_config.yaml`

For Athena++ documentation: https://princetonuniversity.github.io/Athena++/

---

## Checklist Before Deployment

- [ ] Ray cluster configured and tested
- [ ] File paths updated in `cluster_config.yaml`
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Test simulation runs successfully
- [ ] Analysis scripts tested on test output
- [ ] Sufficient disk space available (~1 TB for all campaigns)
- [ ] Runtime quota confirmed with cluster admin

---

**Ready for deployment on Glenn's GitHub repository**
