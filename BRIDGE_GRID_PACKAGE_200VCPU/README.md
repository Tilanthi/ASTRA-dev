# BRIDGE_GRID Campaign - 200 vCPU Package

**Purpose**: Address Peer Review Issue #3 - BRIDGE_GRID Contradiction

## The Problem (Issue #3)

**Peer Review Concern**:
> "Linear perturbation theory predicts strong f-dependence of λ/W, but non-linear MHD results show weak/no f-dependence. This contradiction needs resolution."

**What This Campaign Does**:
- Dense sampling of f = 1.1 to 2.0 (8 values)
- Tests β = 0.3, 1.0, 5.0 (weak to strong magnetic field)
- 2 random seeds per parameter point for statistics
- **48 simulations total**

**Goal**: Map the transition from near-critical (f ≈ 1.0) to supercritical (f > 1.5) behavior and determine where the λ/W scaling changes.

---

## Quick Start (200 vCPU Machine)

```bash
# 1. Extract package (if reading from tar.gz)
tar -xzf BRIDGE_GRID_PACKAGE_200VCPU.tar.gz
cd BRIDGE_GRID_PACKAGE_200VCPU

# 2. Compile Athena++ (one-time setup)
bash compile_athena.sh

# 3. Install Python dependencies
pip3 install ray h5py numpy scipy pandas matplotlib

# 4. Run campaign
python3 run_bridge_grid_200vcpu.py

# 5. Analyze results (after completion)
python3 analyze_results.py
```

---

## Computational Requirements

**Hardware**: 200 vCPU (AMD EPYC or similar)

**Ray Configuration**:
```python
max_concurrent = 12  # 12 simulations running at once
cores_per_sim = 16   # 16 MPI ranks per simulation
```

**Per-Simulation Resources**:
- CPUs: 16 cores
- RAM: ~2 GB
- Disk: ~1 GB for HDF5 outputs
- Wall time: ~2-3 hours each

**Total Estimated Wall Time**:
- 48 simulations × 2.5 hours = 120 CPU-hours
- With 12 concurrent: ~10 hours total

---

## Campaign Parameters

### Physical Parameters
- **f** (line mass ratio): 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0 (8 values)
- **β** (plasma beta): 0.3, 1.0, 5.0 (3 values)
- **M** (Mach number): 1.0 (fiducial)
- **Seeds**: 42, 137 (2 random seeds)

### Domain Configuration
- **Longitudinal length**: L = 12λJ (intermediate between standard 8λJ and extended 16λJ)
- **Transverse size**: Ly = Lz = 2λJ
- **Resolution**: 384 × 48 × 48 cells
- **Aspect ratio**: Optimized for filament geometry

### Output Configuration
- **Timeout**: 600 seconds (wall clock)
- **HST output**: Every 0.01 tJ (high temporal resolution)
- **Snapshot outputs**: Every 0.1 tJ
- **Required data**: Density, velocity, magnetic field

---

## Expected Outcomes

### Success Criteria

1. **Continuous λ vs f curve**: Measurements across f = 1.1-2.0
2. **Transition identification**: Locate f_crit where behavior changes
3. **Power-law validation**: Test λ ∝ f^α scaling
4. **Comparison with theory**: Compare against linear perturbation predictions

### Key Deliverables

1. **lambda_measurements.csv**: All λ/W measurements with uncertainties
2. **fig_lambda_vs_f.pdf**: λ/W vs f for all β values
3. **fig_transition_analysis.pdf**: Identification of critical f
4. **fig_comparison_theory.pdf**: Comparison with perturbation theory
5. **SUMMARY_REPORT.md**: Executive summary of findings

---

## File Structure

```
BRIDGE_GRID_PACKAGE_200VCPU/
├── README.md                        # This file
├── run_bridge_grid_200vcpu.py       # Main execution script (to be created)
├── analyze_results.py               # Analysis script
├── extract_beading.py               # Peak detection from HDF5
├── monitor_progress.py              # Progress monitoring
├── compile_athena.sh                # Athena++ compilation
├── bridge_grid/                     # 48 simulation configs
│   ├── config_BRIDGE_GRID_f1.1_beta0.3_M1.0_theta90.0_s42.json
│   ├── config_BRIDGE_GRID_f1.1_beta0.3_M1.0_theta90.0_s137.json
│   ├── ...
│   └── config_BRIDGE_GRID_f2.0_beta5.0_M1.0_theta90.0_s137.json
└── outputs/                         # Simulation outputs (created during run)
    ├── BRIDGE_GRID_f1.1_beta0.3_M1.0_theta90.0_s42/
    │   ├── *.hst                    # History files
    │   ├── *.rst                    # Restart files
    │   └── final_snapshot.h5        # HDF5 output
    └── ...
```

---

## Detailed Execution Instructions

### Step 1: Athena++ Compilation

```bash
# Clone Athena++ (if not already present)
git clone https://github.com/PrincetonUniversity/athena-public-version
cd athena-public-version
git checkout v21.0  # Use stable version

# Configure for filament fragmentation problem
./configure --h5double --mpi --prob=filament_spacing

# Compile
make all

# Verify executable
ls -lh bin/athena
```

The `compile_athena.sh` script automates this process.

### Step 2: Environment Setup

```bash
# Load required modules (HPC cluster)
module load openmpi
module load python/3.9
module load hdf5

# Install Python packages
pip3 install --user ray h5py numpy scipy pandas matplotlib

# Verify Ray installation
python3 -c "import ray; print(f'Ray version: {ray.__version__}')"
```

### Step 3: Run Campaign

```bash
# Start Ray cluster (if not auto-started)
ray start --head --num-cpus=200

# Run campaign
python3 run_bridge_grid_200vcpu.py

# Monitor progress in another terminal
python3 monitor_progress.py
```

### Step 4: Analysis

```bash
# After all simulations complete
python3 analyze_results.py

# Results will be in:
# - lambda_measurements.csv
# - figures/
# - SUMMARY_REPORT.md
```

---

## Output Format

### Simulation Status JSON

Each simulation creates a status file:

```json
{
  "sim_id": "BRIDGE_GRID_f1.5_beta1.0_M1.0_theta90.0_s42",
  "config_file": "bridge_grid/config_BRIDGE_GRID_f1.5_beta1.0_M1.0_theta90.0_s42.json",
  "status": "FRAG" | "STABLE" | "TIMEOUT",
  "t_frag": 0.35,
  "dt_min": 1.2e-8,
  "rho_c_max": 245.3,
  "longitudinal_peaks": 3,
  "peak_positions": [96, 192, 288],
  "peak_amplitudes": [2.34, 2.56, 2.12],
  "lambda_frag": 1.23,
  "lambda_frag_uncertainty": 0.08,
  "fragmentation_quality": "excellent",
  "wall_time_seconds": 7200,
  "n_hdf5_outputs": 15
}
```

### Analysis CSV Format

```csv
sim_id,f,beta,M,seed,status,n_peaks,lambda_frag,lambda_frag_err,t_frag
BRIDGE_GRID_f1.1_beta0.3_M1.0_theta90.0_s42,1.1,0.3,1.0,42,FRAG,3,1.12,0.05,0.28
BRIDGE_GRID_f1.2_beta0.3_M1.0_theta90.0_s42,1.2,0.3,1.0,42,FRAG,3,1.18,0.06,0.25
...
```

---

## Troubleshooting

### Issue: Ray cluster won't start

```bash
# Check if Ray is already running
ray status

# Stop existing cluster
ray stop

# Clean restart
ray start --head --num-cpus=200 --port=6379
```

### Issue: Simulations timeout early

**Possible cause**: Default 600s timeout too short for high-f cases

**Solution**: Edit config files to increase `timeout_seconds`

```bash
# In each config file, change:
"timeout_seconds": 600
# to:
"timeout_seconds": 3600  # 1 hour
```

### Issue: No HDF5 outputs

**Possible cause**: HDF5 output not enabled in Athena++ build

**Solution**: Recompile with HDF5 support

```bash
cd athena-public-version
./configure --h5double --mpi --prob=filament_spacing
make clean
make all
```

### Issue: Out of memory

**Possible cause**: Running too many concurrent simulations

**Solution**: Reduce `max_concurrent` in run script

```python
# In run_bridge_grid_200vcpu.py, change:
max_concurrent = 12
# to:
max_concurrent = 8  # Fewer concurrent simulations
```

---

## Validation Checks

### Before Running

```bash
# Check config files exist
ls bridge_grid/*.json | wc -l  # Should show 48

# Verify Athena++ executable
./athena-public-version/bin/athena -h  # Should show help

# Test Ray
python3 -c "import ray; ray.init(num_cpus=200); print('OK')"
```

### During Run

```bash
# Monitor progress
python3 monitor_progress.py

# Check CPU usage
htop  # Should show ~200 cores utilized

# Check disk space
df -h .  # Should have > 100 GB available
```

### After Completion

```bash
# Verify all simulations completed
python3 -c "
import json
import glob
results = []
for f in glob.glob('outputs/*/status.json'):
    with open(f) as fp:
        results.append(json.load(fp))
print(f'Total: {len(results)}')
print(f'FRAG: {sum(1 for r in results if r[\"status\"]==\"FRAG\")}')
print(f'STABLE: {sum(1 for r in results if r[\"status\"]==\"STABLE\")}')
print(f'TIMEOUT: {sum(1 for r in results if r[\"status\"]==\"TIMEOUT\")}')
"
```

---

## Integration with Paper

After successful campaign completion:

1. **Copy results to paper directory**:
   ```bash
   cp lambda_measurements.csv /path/to/paper/data/
   cp figures/*.pdf /path/to/paper/figures/
   cp SUMMARY_REPORT.md /path/to/paper/
   ```

2. **Update paper sections**:
   - Add new λ/W vs f plot
   - Discuss transition f_crit
   - Compare with perturbation theory
   - Address reviewer concern directly

3. **Cite in response**:
   > "To address the referee's concern about the BRIDGE_GRID contradiction, we performed 48 new MHD simulations densely sampling f = 1.1-2.0. The results show..."

---

## Scientific Background

### Why This Range?

- **f < 1.2**: Near-critical regime where linear theory applies
- **f = 1.2-1.6**: Transition regime where non-linear effects emerge
- **f > 1.6**: Supercritical regime dominated by radial collapse

### What Determines λ/W?

1. **Linear perturbation theory**: Predicts λ ∝ f^α with α ≈ 0.5-1.0
2. **Non-linear MHD**: May show different scaling due to:
   - Radial collapse competing with longitudinal instability
   - Magnetic tension effects
   - Turbulent seeding

### Expected Outcomes

- **If linear theory holds**: Clear λ ∝ f^α trend across all f
- **If non-linear effects dominate**: Break in scaling at f_crit
- **Intermediate case**: Smooth transition with changing α

---

## Contact and Support

**Package created**: 28 April 2026
**Campaign**: BRIDGE_GRID (Peer Review Response)
**Purpose**: Address Issue #3 - f-dependence contradiction

For questions or issues, refer to:
- Main simulation plan: `PEER_REVIEW_SIMULATION_PLAN_Apr2026.md`
- Athena++ documentation: https://princetonuniversity.github.io/athena-public-version/
- Ray documentation: https://docs.ray.io/

---

**Estimated completion time**: ~10 hours on 200 vCPU
**Total simulations**: 48
**Expected scientific output**: First λ/W measurements across f = 1.1-2.0 transition
