# Peer Review Response Simulation Scripts

Set of Python scripts for executing the peer review response simulation campaigns on a 200 CPU Ray cluster.

## Overview

These scripts implement the simulation plan described in `PEER_REVIEW_SIMULATION_PLAN_Apr2026.md`, which addresses 4 critical concerns from the peer review:

1. **Regime Mismatch/Negative Result**: SUPERCRITICAL-LONG campaign measures λ/W directly in supercritical regime
2. **Extrapolation Validation**: BRIDGE-GRID campaign validates f-dependence scaling
3. **Timeout Artifact**: TIMEOUT-CONVERGENCE campaign ensures timeout adequacy
4. **Calibration Formula**: CALIBRATION-VALIDATION campaign re-derives 1.11±0.12 factor with full uncertainty breakdown

## Scripts

### generate_configs.py

Generate all Athena++ simulation configurations for the campaigns.

**Usage:**
```bash
python generate_configs.py
```

**Output:**
- `peer_review_simulation_configs/` directory with all campaign configs
- `MANIFEST.json` with campaign summary and resource estimates

**Campaigns generated:**
- SUPERCRITICAL-LONG: Extended domains (16-32λJ)
- BRIDGE-GRID: Dense f sampling (1.1-2.0)
- TIMEOUT-CONVERGENCE: Systematic timeout validation
- CALIBRATION-VALIDATION: Hierarchical Bayesian calibration
- DOMAIN-CONVERGENCE: Domain size convergence tests

### submit_campaign.py

Submit a campaign to the Ray cluster for execution.

**Usage:**
```bash
# Connect to existing Ray cluster
python submit_campaign.py SUPERCRITICAL_LONG \
    --config-dir peer_review_simulation_configs \
    --concurrent 3 \
    --athena /path/to/athena_pp \
    --ray-address auto

# Or start local Ray instance
python submit_campaign.py BRIDGE_GRID \
    --concurrent 2
```

**Parameters:**
- `--concurrent`: Maximum concurrent simulations (default: 3)
- `--athena`: Path to Athena++ binary (default: athena_pp)
- `--ray-address`: Ray cluster address (default: None = local)

**Resource allocation:**
- 64 cores per simulation
- 200 GB RAM per simulation
- Up to 3 concurrent on 200-core cluster

### monitor_progress.py

Monitor simulation progress and generate status reports.

**Usage:**
```bash
# Single scan
python monitor_progress.py SUPERCRITICAL_LONG --html

# Continuous monitoring (update every 5 minutes)
python monitor_progress.py SUPERCRITICAL_LONG --continuous --interval 300
```

**Output:**
- HTML progress report with color-coded status table
- Text summary with statistics
- Failed/stalled simulation identification

### extract_beading.py

Extract beading patterns from simulation outputs.

**Usage:**
```bash
# Analyze single snapshot
python extract_beading.py path/to/snapshot.h5 --Lx 16.0

# Analyze full campaign
python extract_beading.py outputs/SUPERCRITICAL_LONG \
    --campaign SUPERCRITICAL_LONG \
    --output beading_results.json
```

**Metrics extracted:**
- Number of density peaks
- Peak positions and spacing
- Longitudinal variance
- Density contrast (C = ρ_max/ρ_0)
- λ/W ratio

## Campaign Parameters

### SUPERCRITICAL-LONG Campaign

**Purpose:** Direct λ/W measurement in supercritical regime (f=1.5-3.0)

**Domain configurations:**
- LONG-1: L = 16λJ, Resolution: 512×64×64
- LONG-2: L = 24λJ, Resolution: 768×64×64
- LONG-3: L = 32λJ, Resolution: 1024×64×64

**Parameter space:**
- f = 1.5, 2.0, 2.5
- β = 0.3, 1.0, 5.0
- M = 1.0
- Seeds: 3 per point
- **Total: ~120 simulations**

### BRIDGE-GRID Campaign

**Purpose:** Validate extrapolation from near-critical to supercritical

**Parameter space:**
- f = 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0
- β = 0.3, 1.0, 5.0
- M = 1.0
- Domain: L = 12λJ
- Seeds: 2 per point
- **Total: ~48 simulations**

### TIMEOUT-CONVERGENCE Campaign

**Purpose:** Validate timeout adequacy across parameter space

**Parameter space:**
- f = 1.4-2.2 (5 values)
- β = 0.3, 0.5, 1.0
- M = 1.0, 2.0, 3.0
- **Total: ~45 simulations**

### CALIBRATION-VALIDATION Campaign

**Purpose:** Re-derive calibration factor with uncertainty breakdown

**Parameter space:**
- f = 1.5, 2.0, 2.5
- β = 0.5, 1.0, 2.0
- M = 1.0, 2.0
- θ = 30°, 60°, 90°
- Seeds: 3 per point
- **Total: ~162 simulations**

## Execution Workflow

### 1. Setup and Validation (Week 1)

```bash
# Generate all configs
python generate_configs.py

# Review generated configs
ls peer_review_simulation_configs/

# Test with 2-3 simulations per campaign
python submit_campaign.py SUPERCRITICAL_LONG --concurrent 1

# Monitor test runs
python monitor_progress.py SUPERCRITICAL_LONG --continuous --interval 60
```

### 2. Main Execution (Weeks 2-3)

```bash
# Run SUPERCRITICAL-LONG (highest priority)
python submit_campaign.py SUPERCRITICAL_LONG --concurrent 3

# In another terminal, monitor progress
python monitor_progress.py SUPERCRITICAL_LONG --continuous --interval 300

# After completion, run BRIDGE-GRID
python submit_campaign.py BRIDGE_GRID --concurrent 3

# Run TIMEOUT-CONVERGENCE
python submit_campaign.py TIMEOUT_CONVERGENCE --concurrent 3
```

### 3. Analysis and Reporting (Weeks 4-5)

```bash
# Extract beading patterns from all completed simulations
python extract_beading.py outputs/SUPERCRITICAL_LONG \
    --campaign SUPERCRITICAL_LONG \
    --output analysis/supercritical_long_beading.json

python extract_beading.py outputs/BRIDGE_GRID \
    --campaign BRIDGE_GRID \
    --output analysis/bridge_grid_beading.json

# Generate calibration analysis results
python analyze_calibration.py  # (to be implemented)
```

## Resource Estimates

**Total simulations:** ~470
**Per-simulation time:**
- Standard domain (8λJ): ~4 hours
- Extended domain (16-24λJ): ~12-24 hours
- Very long domain (32λJ): ~36 hours

**Total CPU-hours:** ~10,000
**On 200-core cluster:** ~50 hours wall time (with 3 concurrent)
**Practical timeline:** 5 weeks (includes setup, analysis, contingency)

## Ray Cluster Setup

### Starting a Ray Cluster

```bash
# On head node
ray start --head --port=6379

# On worker nodes
ray start --address=<head-node-ip>:6379
```

### Verifying Connection

```bash
python -c "import ray; ray.init(address='auto'); print(ray.available_resources())"
```

## Troubleshooting

### Issue: Simulations timeout or fail

**Symptoms:** Status shows 'failed' or 'timeout'

**Solutions:**
- Check log files for error messages
- Reduce `--concurrent` to lower resource contention
- Increase `tlim` in config if physics requires longer time
- Check disk space on output directory

### Issue: No beading detected

**Symptoms:** extract_beading.py reports 'no_beading'

**This is expected** for supercritical simulations - this is the negative result we're testing for!

**To verify:**
- Check longitudinal variance metric (should be <0.02 for radial collapse)
- Visualize density profiles manually
- Compare with near-critical simulations that should show beading

### Issue: Ray cluster connection fails

**Symptoms:** "Connection refused" or "Ray not reachable"

**Solutions:**
- Verify Ray is running: `ps aux | grep ray`
- Check firewall rules (port 6379 must be open)
- Try local Ray instance: omit `--ray-address` argument

## Output File Structure

```
peer_review_response_package_20260427/
├── configs/                    # All simulation configs
│   ├── supercritical_long/
│   ├── bridge_grid/
│   ├── timeout_convergence/
│   └── calibration_validation/
├── submissions/                # Ray submission files
│   ├── SUPERCRITICAL_LONG/
│   └── ...
├── outputs/                    # Simulation outputs
│   ├── SUPERCRITICAL_LONG/
│   │   ├── SUPERCRITICAL_LONG_f1.5_beta0.3_M1.0_theta90.0_s42/
│   │   │   ├── *.h5           # Snapshot files
│   │   │   └── *.log          # Log files
│   │   └── ...
│   └── ...
├── analysis/                   # Analysis results
│   ├── beading_results.json
│   ├── calibration_results.json
│   └── figures/
│       ├── fig_lambda_vs_f.pdf
│       └── ...
└── reports/                    # Final reports
    ├── executive_summary.pdf
    ├── final_report.ipynb
    └── peer_review_response.md
```

## Success Criteria

Each campaign will be considered successful if:

1. **SUPERCRITICAL-LONG**: Direct λ/W measurement in at least 2 of 3 supercritical cases
2. **BRIDGE-GRID**: Continuous λ(f) mapping from f=1.1 to 2.0 with <20% uncertainty
3. **TIMEOUT-CONVERGENCE**: Clear classification of timeout-safe vs timeout-uncertain regions
4. **CALIBRATION-VALIDATION**: Calibration factor re-derived with <5% uncertainty breakdown

## Contact

For questions or issues with these scripts, please refer to:
- Simulation plan: `PEER_REVIEW_SIMULATION_PLAN_Apr2026.md`
- Non-Ideal MHD campaign report: `NIMHD_CAMPAIGN_REPORT_Apr2026.md`
- Main paper: `filament_spacing_streamlined_mnras.tex`
