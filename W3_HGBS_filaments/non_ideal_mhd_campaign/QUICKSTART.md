# Non-Ideal MHD Campaign - Quick Start Guide

## For Glenn White - External 200 CPU Ray Cluster

### Step 1: Transfer Files to External Cluster

```bash
# On your local machine, after extracting the .gz file:
scp -r non_ideal_mhd_campaign user@external.cluster:/path/to/workdir/
```

### Step 2: Build Athena++ with Non-Ideal MHD

```bash
# On the external cluster
cd /path/to/athena++

# Configure with non-ideal MHD support
./configure --prob=fountain_ambipolar --h5double=yes --with-non-ideal-mhd=yes

# Build
make clean
make -j 32

# Verify binary exists
ls -lh bin/athena_pg
```

**NOTE**: You may need to create a custom problem generator. The `fountain_ambipolar` problem provides a template. You'll need to modify it for cylindrical filament geometry. See the `athena_config_template.cpp` file in this directory.

### Step 3: Update Campaign Configuration

```bash
cd /path/to/workdir/non_ideal_mhd_campaign

# Edit run_campaign.py and update the Athena++ binary path:
# Line 72: ATHENA_BINARY = "/actual/path/to/athena++/bin/athena_pg"

vim run_campaign.py  # or use your preferred editor
```

### Step 4: Start Ray Cluster

```bash
# Find your IP address
export RAY_CLUSTER_IP=$(hostname -I | awk '{print $1}')

# Start Ray head node
ray start --head --port=6379 --num-cpus=200 --dashboard-port=8265

# In another terminal, verify Ray is running
ray status

# Check dashboard at: http://localhost:8265
```

### Step 5: Run the Campaign

```bash
cd /path/to/workdir/non_ideal_mhd_campaign

# Run the campaign (will take ~18 hours)
python run_campaign.py 2>&1 | tee campaign.log

# Monitor progress:
# - Check campaign.log for updates
# - Check Ray dashboard at http://localhost:8265
# - Check checkpoints in /data/non_ideal_mhd_runs/
```

### Step 6: Analyze Results

```bash
# After campaign completes, analyze results
python analyze_results.py

# Results will be in expected_output/ directory
ls expected_output/
```

### Expected Outputs

After successful completion:
- `expected_output/fig_lambda_vs_Am.pdf` - Primary result figure
- `expected_output/fig_timescales.pdf` - Fragmentation timescales
- `expected_output/fig_detection_rate.pdf` - Detection rate vs Am
- `expected_output/fig_density_profiles.pdf` - Sample density profiles
- `expected_output/table_lambda_W.tex` - LaTeX table for paper
- `expected_output/summary.txt` - Text summary of findings

### Troubleshooting

#### Issue: Ray fails to start
```bash
# Check if port is already in use
lsof -i :6379
lsof -i :8265

# Kill existing Ray processes
ray stop
ray start --head --port=6379 --num-cpus=200
```

#### Issue: Simulations crash immediately
- Check Athena++ binary path in run_campaign.py
- Verify binary has execute permissions
- Check campaign.log for error messages

#### Issue: Out of memory
- Reduce `max_concurrent_sims` in config.json
- Reduce `meshblock_size` in athena_config.txt

#### Issue: Taking too long
- Check Ray dashboard for stuck simulations
- Kill and restart individual stuck jobs if needed
- Consider reducing parameter grid (remove Am = 2.0 or f = 2.5)

### Contact

If you encounter issues not covered here:
1. Check campaign.log for error messages
2. Check individual simulation directories for .log files
3. Verify Athena++ compiles with non-ideal MHD support

### Files in This Package

- `README.md` - Detailed campaign documentation
- `QUICKSTART.md` - This file
- `config.json` - Campaign configuration
- `run_campaign.py` - Ray execution script
- `analyze_results.py` - Analysis script
- `athena_config_template.cpp` - Template problem generator for Athena++

Good luck with the simulations!
