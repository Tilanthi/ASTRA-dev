# Targeted MHD Simulation Re-runs
## Peer Review Response Campaign - START HERE

**Purpose**: Address peer review concerns by running 25 targeted Athena++ MHD simulations with extended (6-hour) wall-clock timeouts

**Campaign**: 25 simulations total
- Priority 1: 15 DTC "STABLE" re-runs (quantify timeout artifacts)
- Priority 2: 10 resolution convergence re-runs (256^3 vs 128^3)

**Target System**: External computer with 200 CPUs, Ray distributed task scheduler (NOT Slurm)

**Completion Time**: ~1.5 days at 4 concurrent simulations

---

## QUICK START (5 minutes)

### 1. Extract Package
```bash
tar -xzf targeted_re_runs.tar.gz
cd targeted_re_runs
```

### 2. Verify Environment
```bash
# Check Python version (need 3.8+)
python3 --version

# Check MPI
mpirun --version

# Check available CPUs
nproc
```

### 3. Install Dependencies
```bash
pip3 install ray[default] numpy pandas matplotlib h5py scipy
```

### 4. Compile Athena++ (First Time Only - ~10 minutes)
```bash
cd scripts
bash compile_athena.sh
# Verify binary exists
ls -lh ../athena_reun
cd ..
```

### 5. Launch Campaign
```bash
cd ray_executor
python3 launch_re_runs.py --all
```

### 6. Monitor Progress (In Separate Terminal)
```bash
cd ray_executor
python3 monitor_campaign.py
```

---

## DETAILED INSTRUCTIONS

### Step 1: System Requirements

**Hardware**:
- 200 CPUs recommended (64 CPUs minimum)
- 10 GB free disk space per simulation (temporary files)
- 8+ GB RAM

**Software**:
- Python 3.8 or later
- MPI (OpenMPI or MPICH)
- Ray 2.55.0 or later
- GCC/G++ compiler (for Athena++)
- HDF5 library (optional, for debugging)

### Step 2: Extract and Navigate

```bash
# Extract the tarball
tar -xzf targeted_re_runs.tar.gz

# Enter the directory
cd targeted_re_runs

# Verify contents
ls -l
```

You should see:
```
README_FIRST.md          # This file
CAMPAIGN_SPEC.md         # Detailed campaign specifications
simulations/             # Simulation configurations
  run_list.json         # Complete list of 25 runs
  athena_input_template.dat  # Athena++ input file template
ray_executor/           # Ray execution scripts
  launch_re_runs.py     # Main launcher
  monitor_campaign.py   # Progress monitor
  analyze_results.py    # Post-processing analysis
scripts/                # Utility scripts
  compile_athena.sh     # Athena++ compilation script
output/                 # Created during runtime
  status/               # Status JSON files
  simulations/          # Simulation output directories
  analysis/             # Analysis results
```

### Step 3: Compile Athena++

**IMPORTANT**: You must compile Athena++ before running simulations.

```bash
cd scripts
bash compile_athena.sh
```

This script:
1. Downloads Athena++ v21.0 if not present
2. Configures with self-gravity, MPI, FFT
3. Compiles the `athena_reun` binary
4. Places it in the parent directory

**Expected output**: `athena_reun` binary (~50 MB) in `targeted_re_runs/`

**Troubleshooting**:
- If compilation fails: Check GCC version, HDF5 installation
- If FFT errors: Install FFTW3 library (`apt install libfftw3-dev`)
- If MPI errors: Install OpenMPI (`apt install openmpi-bin`)

### Step 4: Install Python Dependencies

```bash
pip3 install ray[default] numpy pandas matplotlib h5py scipy
```

**Optional**: Create virtual environment first
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install ray[default] numpy pandas matplotlib h5py scipy
```

### Step 5: Review Campaign Specifications

Before launching, review the campaign:

```bash
# View simulation list
cat simulations/run_list.json | python3 -m json.tool

# Read detailed specifications
less CAMPAIGN_SPEC.md
```

**Key parameters to verify**:
- Timeout: 21600 seconds (6 hours) - DO NOT REDUCE THIS
- MPI ranks: 16 per simulation
- Max concurrent: 4 simulations
- Total CPUs needed: 4 × 16 = 64 (200 recommended)

### Step 6: Launch Campaign

**Option A: Launch All Simulations**
```bash
cd ray_executor
python3 launch_re_runs.py --all
```

**Option B: Launch by Priority**
```bash
# Priority 1 only (DTC re-runs)
python3 launch_re_runs.py --priority 1

# Priority 2 only (Resolution re-runs)
python3 launch_re_runs.py --priority 2
```

**Option C: Launch Specific Simulation**
```bash
# For testing/debugging
python3 launch_re_runs.py --run-id dtc_rerun_001
```

**What happens**:
1. Ray initializes distributed task scheduler
2. Simulations launched up to 4 concurrent
3. Each simulation runs with 16 MPI ranks
4. Wall-clock timeout enforced at 6 hours
5. Status files written to `output/status/`

### Step 7: Monitor Progress

**In a separate terminal**:

```bash
cd ray_executor
python3 monitor_campaign.py
```

This displays:
- Progress bar with completion percentage
- Status breakdown (PENDING, RUNNING, FRAG, STABLE, TIMEOUT, FAILED)
- Estimated time remaining
- Recent activity
- Priority breakdown

**Detailed status**:
```bash
python3 monitor_campaign.py --detail
```

### Step 8: Post-Processing Analysis

After all simulations complete:

```bash
cd analysis
python3 extract_tfrag.py           # Extract t_frag from history files
python3 compare_resolution.py      # Resolution convergence analysis
python3 generate_summary.py        # Generate final report
python3 plot_results.py            # Generate figures
```

Or use the all-in-one analyzer:
```bash
cd ray_executor
python3 analyze_results.py
```

This generates:
- `output/analysis/ANALYSIS_SUMMARY.md` - Human-readable summary
- `output/analysis/dtc_analysis.json` - DTC re-run statistics
- `output/analysis/resolution_analysis.json` - Resolution comparison
- `output/figures/` - Analysis figures (PDF/PNG)

---

## EXPECTED OUTCOMES

### Priority 1 (DTC Re-runs)

**Goal**: Quantify what fraction of DTC "STABLE" classifications are timeout artifacts

**Expected classifications**:
- **FRAG**: Simulation reaches t_frag < 1.425 t_J → confirms DTC STABLE was timeout artifact
- **STABLE**: Simulation reaches timeout without t_frag → confirms true stability
- **TIMEOUT**: Incomplete (should not happen with 6-hour timeout)

**Key metric**: Fraction of original STABLE points that fragment with longer runtime

### Priority 2 (Resolution Re-runs)

**Goal**: Achieve true 256^3 resolution convergence assessment

**Expected outcomes**:
- **Converged**: t_frag(256) within 5% of t_frag(128) → resolution independent
- **Not converged**: t_frag(256) differs by >5% → resolution dependent
- **Incomplete**: 256^3 times out → documents resolution uncertainty

**Key metric**: Percentage of parameter points showing resolution convergence

---

## TIME ESTIMATES

### Per-Simulation Wall Time
- **128^3 simulations** (Priority 1): ~1-1.5 hours each
- **256^3 simulations** (Priority 2): ~3-5 hours each

### Campaign Duration (at 4 concurrent)
- **Priority 1 (15 sims)**: 15 × 1.25 h / 4 = ~4.7 hours
- **Priority 2 (10 sims)**: 10 × 4 h / 4 = ~10 hours
- **Total**: ~15 hours + overhead ≈ 1 day

### With 200 CPUs (4 concurrent × 16 MPI)
- **Efficiency**: ~85% (queue time, checkpoints)
- **Realistic total**: ~1.5 days

---

## CRITICAL: TIMEOUT HANDLING

The 6-hour (21600 second) timeout is **CRITICAL** and must be enforced:

```python
# In launch_re_runs.py
TIMEOUT_SECONDS = 21600  # DO NOT CHANGE
```

**Do NOT reduce this timeout**. The entire scientific value of these re-runs depends on running simulations long enough to distinguish true stability from timeout artifacts.

If you encounter issues:
- **All simulations timing out**: Reduce concurrent from 4 to 2
- **Individual simulation timeout**: This is expected behavior (STABLE classification)
- **Simulation crashes**: Check log files in output/simulations/<run_id>/

---

## SUCCESS CRITERIA

### DTC Re-runs Successful If:
- At least 12 of 15 simulations complete
- Classification (FRAG/STABLE/TIMEOUT) is unambiguous
- Results can be compared meaningfully with original DTC

### Resolution Re-runs Successful If:
- At least 8 of 10 simulations complete
- t_frag values can be extracted from history files
- Comparison with 128^3 reference is possible

### Overall Campaign Successful If:
- Both Priority 1 and Priority 2 meet success criteria
- Uncertainties are quantified and can be propagated through paper
- Results enable honest discussion of limitations

---

## TROUBLESHOOTING

### Ray initialization errors
```bash
ray stop
ray start --head
# Then retry launch
```

### Simulation crashes immediately
- Check input file syntax
- Verify MPI ranks per simulation matches available CPUs
- Check disk space (>10 GB per simulation for temporary files)

### All simulations timeout
- Reduce concurrent simulations from 4 to 2
- Check that MPI is properly configured
- Verify 6-hour timeout is being enforced

### History files not generated
- Verify HST output is enabled in input file
- Check file write permissions
- Look for errors in simulation log files

### Out of memory errors
- Reduce concurrent simulations
- Reduce MeshBlock size in input file (nx1, nx2, nx3 in <meshblock>)

### Permission errors
```bash
chmod +x ray_executor/*.py
chmod +x scripts/*.sh
```

---

## OUTPUT FILES

### Per-Simulation Output
Each simulation creates:
```
output/simulations/<run_id>/
  ├── athena_input_<run_id>.dat    # Input file used
  ├── <run_id>.hst                 # History file (time, dt, etc.)
  ├── <run_id>.log                 # Simulation log
  └── status_<run_id>.json         # Status file (auto-generated)
```

### Central Status Files
```
output/status/
  ├── status_dtc_rerun_001.json
  ├── status_dtc_rerun_002.json
  ├── ...
  └── status_res_rerun_010.json
```

### Analysis Results
```
output/analysis/
  ├── ANALYSIS_SUMMARY.md          # Human-readable summary
  ├── dtc_analysis.json            # DTC statistics
  ├── resolution_analysis.json     # Resolution comparison
  └── campaign_summary.json        # Complete results

output/figures/
  ├── dtc_frag_fraction.pdf        # DTC fragmentation rate
  ├── resolution_comparison.pdf    # 128 vs 256 comparison
  └── uncertainty_quantification.pdf # Combined uncertainty analysis
```

---

## DELIVERABLES

After completion, provide the following to glenn@ou.ac.uk:

1. **output/status/** directory - All 25 status JSON files
2. **output/analysis/** directory - All analysis results
3. **output/figures/** directory - Analysis figures (PDF format)
4. **ANALYSIS_SUMMARY.md** - Comprehensive summary report

These will be integrated into the revised manuscript.

---

## CONTACT FOR SUPPORT

If you encounter any issues:
1. Check this README first
2. Check status/ directory for error logs
3. Monitor progress with monitor_campaign.py (shows verbose errors)
4. Document all failures in status/ for debugging

**IMPORTANT**: Each simulation should create a log file. If a simulation fails, save the log for debugging.

---

## NEXT STEPS AFTER COMPLETION

1. Run analysis scripts (see Step 8 above)
2. Review ANALYSIS_SUMMARY.md
3. Package results:
   ```bash
   cd output
   tar -czf re_run_results.tar.gz status/ analysis/ figures/
   ```
4. Send to glenn@ou.ac.uk for integration into paper revision

---

## ACKNOWLEDGMENTS

This campaign is part of the peer review response for:
"Filament Spacing in the Herschel Gould Belt Survey:
A Novel Test of Magnetic Field Geometry"

Principal Investigators:
- Glenn J. White (Open University) - glenn@ou.ac.uk
- Robin Dey (VBRL Holdings Inc)

Computational Resources:
- External computer cluster with 200 CPUs
- Ray distributed task scheduler
- Athena++ v21.0 MHD code
