# Peer Review MHD Simulation Campaign

## Overview

This package contains specifications for new MHD simulations to address concerns raised by the theoretical expert reviewer. The simulations are designed to be run on a remote Ray cluster with 200 cores.

## Campaign Summary

| Campaign | Simulations | Priority | Purpose |
|----------|-------------|----------|---------|
| calibration_documentation | 40 | CRITICAL | Document λ_frag = 1.11 λ_MJ calibration |
| regime_boundary_exploration | 60 | HIGH | Distinguish radial vs. longitudinal fragmentation |
| domain_size_convergence_test | 24 | MODERATE | Verify 8 λ_J domain adequacy |
| perpendicular_field_lambda_W | 24 | HIGH | Direct λ/W measurements for perpendicular fields |
| physical_turbulence_test | 72 | MODERATE | Test physical vs. synthetic turbulence |
| eos_asymmetry_exploration | 120 | MODERATE | Understand EOS behavior across regime boundary |
| **TOTAL** | **340** | - | **All campaigns** |

## Directory Structure

```
peer_review_2026/
├── simulation_campaigns/
│   ├── calibration_campaign.json
│   ├── regime_boundary_campaign.json
│   ├── domain_size_campaign.json
│   ├── perpendicular_field_campaign.json
│   ├── physical_turbulence_campaign.json
│   └── eos_asymmetry_campaign.json
├── scripts/
│   ├── extract_lambda_W.py
│   ├── measure_tfrag.py
│   └── run_athena_simulation.sh
├── ray_job_templates/
│   ├── submit_campaign.sh
│   └── monitor_jobs.py
├── README.md (this file)
└── THEORETICAL_REVIEWER_ANALYSIS.md
```

## Quick Start

### 1. Extract the Package

```bash
cd /path/to/working/directory
tar -xzf peer_review_mhd_campaigns.tar.gz
cd peer_review_2026
```

### 2. Choose a Campaign

Each campaign has a JSON specification file in `simulation_campaigns/`.

- **CRITICAL**: Start with `calibration_campaign.json`
- **HIGH**: Then run `regime_boundary_campaign.json` and `perpendicular_field_campaign.json`
- **MODERATE**: Run remaining campaigns as time permits

### 3. Submit Jobs to Ray Cluster

The job submission script handles:
- Parameter file generation
- Athena++ execution
- Output management
- Post-processing

Example:
```bash
./ray_job_templates/submit_campaign.sh \
    --campaign simulation_campaigns/calibration_campaign.json \
    --output ./results/calibration \
    --cores 200
```

### 4. Monitor Job Progress

```bash
python scripts/monitor_jobs.py --results ./results/calibration
```

### 5. Analyze Results

Once simulations complete, extract λ/W and t_frag measurements:

```bash
python scripts/extract_lambda_W.py \
    --simulation_dir ./results/calibration/sim_001 \
    --output ./results/calibration/sim_001_lambda_W.json

python scripts/measure_tfrag.py \
    --simulation_dir ./results/calibration/sim_001 \
    --output ./results/calibration/sim_001_tfrag.json
```

## Campaign Specifications

### Calibration Documentation Campaign

**Purpose**: Extract λ/W measurements from near-critical simulations to document the λ_frag = 1.11 λ_MJ calibration

**Parameters**:
- f = 1.00, 1.05, 1.10, 1.15, 1.20
- β = 0.3, 1.0
- M = 1.0, 2.0
- 2 seeds per point

**Total**: 40 simulations

**Output**: Full HDF5 snapshots for λ/W extraction

**Analysis**: Document calibration procedure in paper supplement

### Regime Boundary Exploration Campaign

**Purpose**: Distinguish between radial collapse and longitudinal fragmentation across f ≈ 1.2-1.5

**Parameters**:
- f = 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0
- β = 0.3, 1.0
- M = 1.0
- 3 seeds per point

**Total**: 60 simulations

**Enhanced Diagnostics**: Track both radial collapse and longitudinal beading

**Output**: Time series data for both regimes

### Domain Size Convergence Test

**Purpose**: Verify that 8 λ_J domain does not suppress longitudinal modes

**Parameters**:
- f = 1.05, 1.10, 1.15 (near-critical)
- β = 0.3, 1.0
- M = 1.0, 2.0
- 2 seeds per point

**Domain**: 16 × 2 × 2 λ_J (double longitudinal length)

**Total**: 24 simulations

**Analysis**: Compare λ/W with existing 8 λ_J results

### Perpendicular-Field λ/W Campaign

**Purpose**: Direct λ/W measurements for perpendicular B-fields

**Parameters**:
- f = 2.0, 2.5, 3.0
- β = 0.3, 1.0
- M = 1.0, 2.0
- 2 seeds per point

**Total**: 24 simulations

**Field Geometry**: Perpendicular to filament axis

**Analysis**: Compare λ/W_perpendicular with λ/W_longitudinal

### Physical Turbulence Test Campaign

**Purpose**: Test physical (M × c_s) vs. synthetic (M × c_s × 10⁻⁴) turbulence

**Parameters**:
- f = 1.5, 2.0, 2.5
- β = 0.3, 1.0
- M = 1.0, 2.0, 3.0
- 2 seeds per point
- 2 turbulence variants per point

**Total**: 72 simulations

**Analysis**: Compare t_frag and λ/W between seeding methods

### EOS Asymmetry Exploration Campaign

**Purpose**: Understand EOS behavior across regime boundary

**Parameters**:
- f = 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0
- γ = 0.8, 0.9, 1.0, 1.2, 1.5, 5/3
- β = 1.0
- M = 1.0
- 2 seeds per point

**Total**: 120 simulations

**Extended Runtime**: 10 hour wall-clock for adiabatic cases

## Analysis Workflow

### For Each Simulation:

1. **Extract λ/W measurements**:
   ```bash
   python scripts/extract_lambda_W.py \
       --simulation_dir <sim_dir> \
       --output <sim_dir>/lambda_W.json
   ```

2. **Measure t_frag**:
   ```bash
   python scripts/measure_tfrag.py \
       --simulation_dir <sim_dir> \
       --output <sim_dir>/tfrag.json
   ```

3. **Compile campaign results**:
   ```bash
   python scripts/compile_campaign.py \
       --campaign_dir <campaign_results> \
       --output <campaign_summary>.json
   ```

### For Each Campaign:

1. **Generate summary statistics**
2. **Create comparison plots** (if applicable)
3. **Perform regime analysis** (if applicable)
4. **Document findings in summary report**

## Expected Outputs

### Calibration Campaign:
- λ/W measurements for all 40 runs
- Calibration factor calculation
- Documentation of procedure

### Regime Boundary Campaign:
- t_frag_radial and t_frag_longitudinal for all 60 runs
- Regime classification for each run
- Power law fits for each regime

### Domain Size Campaign:
- λ/W comparison: 8 vs. 16 λ_J domains
- Convergence assessment

### Perpendicular-Field Campaign:
- λ/W_perpendicular for all 24 runs
- Comparison with longitudinal-field results

### Physical Turbulence Campaign:
- t_frag and λ/W for both seeding methods
- Impact quantification

### EOS Asymmetry Campaign:
- Fragmentation rate vs. γ and f
- Physical interpretation of asymmetry

## Ray Cluster Configuration

### Recommended Settings:

```python
# Ray cluster configuration
ray.init(
    num_cpus=200,
    object_store_memory=10_000_000_000,  # 10 GB
    dashboard_host="0.0.0.0",
    dashboard_port=8265
)

# Resource allocation per simulation
@ray.remote(num_cpus=4, memory=1_000_000_000)
def run_simulation(config):
    # Simulation code here
    pass
```

### Job Monitoring:

The `monitor_jobs.py` script provides:
- Real-time job status
- Progress tracking
- Failure detection
- Resource utilization

## Troubleshooting

### Common Issues:

1. **Out of memory**: Reduce number of concurrent jobs
2. **Timeout errors**: Increase wall-clock timeout in config
3. **HDF5 write errors**: Check disk space
4. **Ray cluster connection**: Verify cluster is running

### Debug Mode:

Run single simulation for debugging:
```bash
./scripts/run_athena_simulation.sh \
    --config simulation_campaigns/calibration_campaign.json \
    --output ./test_output
```

## Contact

For questions or issues, contact:
- Glenn: [GitHub issues at https://github.com/Tilanthi/ASTRA-dev/]

## References

- Original paper: filament_spacing_streamlined_mnras.tex
- Theoretical reviewer analysis: THEORETICAL_REVIEWER_ANALYSIS.md
- Athena++ documentation: [Link to Athena++ docs]
