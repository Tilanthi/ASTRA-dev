# Expanded Referee Response Campaign — Ray Cluster Package

**Version**: 1.0
**Date**: 2026-05-13
**Total Simulations**: 204 (3 sub-campaigns)

## Quick Start

```bash
# 1. Extract package
tar -xzf referee_response_may2026_package.tar.gz
cd referee_response_may2026_package

# 2. Configure paths
vim config.sh  # Update ATHENA_BIN and BASE_DIR paths

# 3. Install Ray (if not already installed)
pip install ray[default]

# 4. Run the campaign
python run_ray_campaign.py

# 5. Analyse results (after campaign completes)
python analyse_campaign.py /data/referee_response_may2026/ctzm_perp
python analyse_campaign.py /data/referee_response_may2026/eos_sensitivity
python analyse_campaign.py /data/referee_response_may2026/turb_amplitude

# 6. Package results for transfer
python package_results.sh
```

---

## System Requirements

### Hardware
- **CPUs**: 220+ cores recommended (adjust RAY_NUM_CPUS in config.sh)
- **Memory**: 4 GB+ per concurrent simulation (6 concurrent = 24 GB+)
- **Storage**: 100 GB+ free space for HDF5 outputs (before pruning)
- **Network**: Low-latency interconnect for Ray communication

### Software
- **Python**: 3.8+
- **Ray**: 2.0+ (pip install ray[default])
- **MPI**: OpenMPI or MPICH for mpirun
- **Athena++**: Compiled binary with filament_spacing_pr problem generator
- **Dependencies**: numpy, scipy, h5py, matplotlib

---

## Configuration

### 1. Edit `config.sh`

```bash
# Athena++ binary path (REQUIRED)
export ATHENA_BIN="/path/to/athena/bin/athena"

# Output directory (REQUIRED)
export BASE_DIR="/data/referee_response_may2026"

# Ray settings
export RAY_NUM_CPUS=220
export RAY_NUM_WORKERS=6

# Simulation parameters
export WALL_TIME=14400  # 4 hours per sim
```

### 2. Source configuration

```bash
source config.sh
```

---

## Running the Campaign

### Full Campaign (All 204 Simulations)

```bash
python run_ray_campaign.py
```

This will run campaigns sequentially:
1. CTZM_PERP (96 sims, ~12 hours)
2. EOS_SENSITIVITY (48 sims, ~6 hours)
3. TURB_AMPLITUDE (60 sims, ~8 hours)

### Single Campaign Only

Edit `run_ray_campaign.py` and comment out the campaigns you don't want:

```python
# In main(), modify:
for campaign in ["CTZM_PERP"]:  # Only run CTZM_PERP
    results = run_campaign(campaign, sims)
```

### Monitor Progress

Results are saved incrementally:
- `/data/referee_response_may2026/ctzm_perp/ctzm_perp_partial.json`
- `/data/referee_response_may2026/eos_sensitivity/eos_sensitivity_partial.json`
- `/data/referee_response_may2026/turb_amplitude/turb_amplitude_partial.json`

Check progress:
```bash
# Count completed simulations
grep -c "\"outcome\": \"FRAG\"" /data/referee_response_may2026/ctzm_perp/ctzm_perp_partial.json
```

---

## Analyzing Results

### After Campaign Completes

Each campaign directory will contain:
- `{campaign}_results.json` — Basic simulation outcomes
- `{campaign}_analysed.json` — Full analysis with λ/W measurements
- `{campaign}_summary.json` — Aggregated statistics
- `figures/` — Diagnostic plots

### Run Analysis

```bash
# Analyse CTZM_PERP
python analyse_campaign.py /data/referee_response_may2026/ctzm_perp

# Analyse EOS_SENSITIVITY
python analyse_campaign.py /data/referee_response_may2026/eos_sensitivity

# Analyse TURB_AMPLITUDE
python analyse_campaign.py /data/referee_response_may2026/turb_amplitude
```

### Expected Outputs

For each campaign:

| File | Contents |
|------|----------|
| `{campaign}_analysed.json` | Full per-simulation results with λ/W measurements |
| `{campaign}_summary.json` | Aggregated statistics (means, stds, counts) |
| `figures/{campaign}_classifications.png` | Classification bar chart |
| `figures/{campaign}_lw_distribution.png` | λ/W histogram |
| `figures/{campaign}_*.png` | Campaign-specific plots |

---

## Packaging Results for Transfer

### Automatic Packaging

```bash
bash package_results.sh
```

This creates:
- `referee_response_results.tar.gz` — All campaign results
- `results_summary.json` — Quick reference summary

### Manual Packaging

```bash
cd /data/referee_response_may2026
tar -czf referee_response_results.tar.gz \
    ctzm_perp/ctzm_perp_analysed.json \
    ctzm_perp/ctzm_perp_summary.json \
    ctzm_perp/figures/ \
    eos_sensitivity/eos_sensitivity_analysed.json \
    eos_sensitivity/eos_sensitivity_summary.json \
    eos_sensitivity/figures/ \
    turb_amplitude/turb_amplitude_analysed.json \
    turb_amplitude/turb_amplitude_summary.json \
    turb_amplitude/figures/
```

### Transfer to Local Machine

```bash
# From remote cluster
scp /data/referee_response_may2026/referee_response_results.tar.gz \
    user@local machine:/path/to/destination/

# Or use rsync for large files
rsync -avz /data/referee_response_may2026/ \
    user@local machine:/path/to/destination/
```

---

## Troubleshooting

### Ray Initialization Fails

**Symptom**: `RuntimeError: Ray failed to initialize`

**Solution**:
```bash
# Stop existing Ray instance
ray stop

# Clear Ray temp files
rm -rf /tmp/ray

# Restart Ray with explicit resources
ray start --head --num-cpus=220
```

### Athena++ Binary Not Found

**Symptom**: `athena: command not found`

**Solution**:
1. Update `ATHENA_BIN` in `config.sh`
2. Verify binary is executable: `chmod +x /path/to/athena/bin/athena`
3. Test manually: `mpirun -np 32 /path/to/athena/bin/athena -i test.athinput`

### HDF5 Files Accumulating

**Symptom**: Disk space filling up

**Solution**:
The runner automatically prunes HDF5 files, but if issues occur:
```bash
# Manually clean HDF5 files from a simulation
find /data/referee_response_may2026/ctzm_perp/ -name "*.athdf" -delete
find /data/referee_response_may2026/ctzm_perp/ -name "*.xdmf" -delete
```

### Simulation Timeouts

**Symptom**: Many TIMEOUT classifications

**Solution**:
Increase `WALL_TIME` in `config.sh` (default is 14400 seconds = 4 hours):
```bash
export WALL_TIME=21600  # 6 hours
```

### Analysis Script Fails

**Symptom**: `FileNotFoundError` or `KeyError` in analyse_campaign.py

**Solution**:
1. Verify campaign ran successfully: check `{campaign}_results.json` exists
2. Check that HDF5 files are present in simulation directories
3. Run analysis with verbose output:
   ```bash
   python analyse_campaign.py /data/referee_response_may2026/ctzm_perp --verbose
   ```

---

## File Structure

```
referee_response_may2026_package/
├── README.md                           # This file
├── TEST_DESIGN_SPECIFICATIONS.md       # Detailed test designs
├── config.sh                           # Configuration template
├── run_ray_campaign.py                 # Main Ray runner
├── analyse_campaign.py                 # Analysis script
├── package_results.sh                  # Results packaging script
└── RESULTS_TEMPLATE.json               # Expected results format
```

After running:

```
/data/referee_response_may2026/
├── ctzm_perp/
│   ├── CTZMP_f1p2_b0p3_m1p0_s0/      # Individual sim directories
│   ├── ctzm_perp_results.json          # Basic outcomes
│   ├── ctzm_perp_analysed.json        # Full analysis
│   ├── ctzm_perp_summary.json         # Aggregated stats
│   └── figures/                        # Diagnostic plots
├── eos_sensitivity/
│   └── (same structure)
└── turb_amplitude/
    └── (same structure)
```

---

## Expected Runtime

On a 220-core Ray cluster:

| Campaign | Simulations | Concurrent | Wall Time |
|----------|-------------|------------|-----------|
| CTZM_PERP | 96 | 6 | ~12 hours |
| EOS_SENSITIVITY | 48 | 6 | ~6 hours |
| TURB_AMPLITUDE | 60 | 6 | ~8 hours |
| **Total** | **204** | **6** | **~26 hours** |

---

## Verification Checklist

Before starting the full campaign, verify:

- [ ] Ray cluster is operational: `ray status`
- [ ] Athena++ binary is found and executable
- [ ] Base directory has sufficient disk space (100 GB+)
- [ ] Single test simulation completes successfully
- [ ] HDF5 analysis script processes test output correctly
- [ ] Results can be transferred to local machine

---

## Support and Documentation

### Test Design Details
See `TEST_DESIGN_SPECIFICATIONS.md` for:
- Scientific motivation for each campaign
- Parameter space justification
- Success criteria
- Statistical analysis plan

### Expected Results Format
See `RESULTS_TEMPLATE.json` for:
- JSON structure of analysed results
- Required fields for paper integration
- How to feed results back to Claude

### Ray Cluster Documentation
- Ray documentation: https://docs.ray.io/
- Ray cluster setup: https://docs.ray.io/en/latest/cluster/vms.html

---

## Citation and Acknowledgment

If you use these simulation results in a publication, please acknowledge:

> "The expanded referee response simulations were performed using Athena++ on a Ray computing cluster. Campaign design and analysis by Claude (ASTRA System), 2026."

And cite:
- Athena++: Stone et al. (2020)
- Ray: Moritz et al. (2018)
