# Sub-Isothermal Perpendicular Field Campaign - Setup Guide

## Campaign Overview

This package contains everything needed to run 72 Athena++ MHD simulations to resolve the critical gap in filament fragmentation physics: sub-isothermal perpendicular-field simulations at supercritical line masses (f ≥ 1.5).

**Total simulations**: 72 (4 f-values × 3 β-values × 3 γ-values × 2 random seeds)

**Scientific goal**: Definitively measure λ/W for perpendicular fields with γ < 1 to enable self-consistent Planck mixture calculation.

## System Requirements

### Hardware
- **CPU**: 220+ vCPUs recommended (can scale down for testing)
- **Memory**: ~8 GB per concurrent simulation
- **Storage**: ~10-20 GB per simulation (~720-1440 GB total for 72 sims)

### Software
- **Python**: 3.8 or higher
- **Ray**: 2.0 or higher (`pip install ray[default]`)
- **Athena++**: MHD code (must be compiled separately)
- **Python packages**: pandas, numpy, pyyaml, matplotlib, scipy, h5py, seaborn

## Installation Instructions

### 1. Install Ray

```bash
pip install ray[default]
```

### 2. Install Python Dependencies

```bash
pip install pandas numpy pyyaml matplotlib scipy h5py seaborn
```

### 3. Compile Athena++

Athena++ must be compiled separately with MHD and self-gravity enabled.

```bash
# Clone Athena++ (if not already available)
git clone https://github.com/PrincetonUniversity/athena-public-version
cd athena-public-version

# Configure with MHD and self-gravity
./configure.py --prob filament --flux hllc --coord cartesian --fb
                 --ghost=2 --nghost=2

# Compile
make all

# Add to PATH or note the executable location
```

### 4. Configure Campaign

Edit `config/ray_cluster.yaml` to match your system:

```yaml
cluster_id: subiso-perp-campaign
num_workers: 220           # Adjust to your CPU count
cpus_per_worker: 1
memory_per_worker_gb: 8    # Adjust to your available RAM
athena_executable: athena  # Path to Athena++ executable
output_base_dir: ./simulation_output
max_concurrent_jobs: 36    # Adjust based on memory constraints
```

### 5. Verify Setup

```bash
# Test Ray installation
python3 -c "import ray; print(ray.__version__)"

# Test Python dependencies
python3 -c "import pandas, numpy, yaml, matplotlib, scipy, h5py, seaborn"

# Verify Athena++ executable
which athena  # Or modify path in config/ray_cluster.yaml
```

## Running the Campaign

### Quick Start

```bash
# Navigate to campaign directory
cd SUBISOTHERMAL_PERPENDICULAR_CAMPAIGN

# Run the campaign (interactive confirmation)
./run_campaign.sh
```

### Advanced Options

```bash
# Setup Ray cluster only (don't run simulations)
./run_campaign.sh --setup_only

# Dry run (test setup without running simulations)
./run_campaign.sh --dry_run

# Skip confirmation by calling Python directly
python3 setup_ray_cluster.py \
    --cluster_config config/ray_cluster.yaml \
    --sim_params simulation_parameters.csv \
    --run
```

### Monitoring Progress

```bash
# Ray dashboard (default port 8265)
# Open in browser: http://localhost:8265

# Check log files
tail -f simulation_output/logs/campaign_execution.log

# Monitor simulation outputs
ls -l simulation_output/
```

## Expected Runtime

- **Per simulation**: ~4-8 hours (depending on parameters)
- **With 220 vCPUs**: ~24-48 hours total (36 concurrent jobs)
- **Checkpoint interval**: Every hour (configurable)

## Analysis Pipeline

Once simulations are complete, run the analysis:

```bash
# Run analysis on all completed simulations
./run_analysis.sh

# Or specify custom directories
./run_analysis.sh --sim_dir /path/to/simulation_output --output_dir /path/to/analysis
```

### Analysis Outputs

1. **Results database**: `analysis_results/campaign_results_database.csv`
2. **Summary statistics**: `analysis_results/campaign_summary.txt`
3. **Mixture calculation**: `analysis_results/mixture_calculation.txt`
4. **Diagnostic plots**: `analysis_results/*.png`

### Analysis Plots

- `lambda_W_vs_f_by_gamma.png`: λ/W vs f for different γ values
- `lambda_W_vs_beta_by_gamma.png`: λ/W vs β for different γ values
- `classification_map_gamma*.png`: Classification heatmap in (f, β) plane

## Troubleshooting

### Ray fails to initialize

```bash
# Stop any existing Ray instances
ray stop

# Clear Ray temp directory
rm -rf /tmp/ray

# Try again
./run_campaign.sh
```

### Out of memory errors

Reduce `max_concurrent_jobs` in `config/ray_cluster.yaml`:

```yaml
max_concurrent_jobs: 18  # Reduce from 36
```

### Athena++ executable not found

Update the path in `config/ray_cluster.yaml`:

```yaml
athena_executable: /full/path/to/athena
```

Or add to PATH:

```bash
export PATH="/path/to/athena/bin:$PATH"
```

### Simulation failures

Check individual simulation logs:

```bash
# Find failed simulations
grep -r "failed" simulation_output/

# Check specific simulation log
cat simulation_output/<sim_id>/log.txt
```

## File Structure

```
SUBISOTHERMAL_PERPENDICULAR_CAMPAIGN/
├── README.md                      # Campaign documentation
├── SETUP_GUIDE.md                 # This file
├── simulation_parameters.csv      # 72 simulation parameter sets
├── setup_ray_cluster.py          # Ray cluster setup script
├── run_campaign.sh               # Campaign execution script
├── run_analysis.sh               # Analysis execution script
├── config/
│   ├── ray_cluster.yaml          # Ray cluster configuration
│   └── filament_perpendicular.athinput  # Athena++ input template
└── analysis/
    ├── analyze_filament.py       # Individual simulation analysis
    └── batch_analysis.py         # Batch analysis and aggregation
```

## Scientific Context

### The Problem

The filament spacing paper identified a critical uncertainty:
- Isothermal perpendicular simulations: λ/W ≈ 1.25
- Sub-isothermal perpendicular physics: unknown (this campaign!)

This creates a large uncertainty in Planck-weighted predictions:
- Isoothermal mixture: ⟨λ/W⟩_Planck ≈ 1.5 (below HGBS)
- Sub-isothermal mixture: ⟨λ/W⟩_Planck ≈ 5.7 (above HGBS)

### The Solution

This campaign measures λ/W for perpendicular fields with γ < 1 at f ≥ 1.5, enabling:
1. Self-consistent Planck mixture calculation
2. Definitive assessment of Planck tension direction
3. Physics-based equation-of-state constraints

### Expected Outcomes

- Detect longitudinal beading in ≥80% of simulations
- Measure λ/W with uncertainty <15% across parameter space
- Identify γ-dependence trends for perpendicular fields
- Enable honest assessment of Planck tension

## Contact

For questions or issues, contact:
- Glenn (github: [your-github-username])
- Campaign documentation: README.md
- ASTRA project: /Users/gjw255/astrodata/SWARM/ASTRA-dev-main

## References

- Arzoumanian et al. 2019 (HGBS filament spacing measurements)
- Planck Collaboration 2016 (Magnetic field geometry statistics)
- Filament spacing paper (in preparation)
