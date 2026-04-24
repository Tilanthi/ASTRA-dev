# Targeted MHD Simulation Re-runs
## Peer Review Response - Priority 1 & 2

**Purpose**: Address peer review concerns by running 25 targeted simulations with extended (6-hour) wall-clock timeouts

**Campaign**: 25 Athena++ MHD simulations
**Target System**: External computer with 200 CPUs, Ray distributed task scheduler
**Completion Time**: ~150 hours (6.25 days) at 4 concurrent simulations

---

## CAMPAIGN OVERVIEW

### Priority 1: DTC "STABLE" Re-runs (15 simulations)
**Goal**: Quantify what fraction of DTC "STABLE" classifications are timeout artifacts

The original Definitive Transition Campaign (DTC) used 600-second wall-clock timeouts and identified STABLE configurations at β = 0.3, M = 1, f = 1.4–2.2. However, the supercritical campaign with 7200–10800 second timeouts showed eventual fragmentation. This raises the question: Are the DTC STABLE results physical or artifacts of insufficient runtime?

**Approach**: Re-run 15 representative "STABLE" grid points with 6-hour wall-clock timeout to determine whether they eventually fragment.

### Priority 2: Resolution Convergence (10 simulations)
**Goal**: Achieve true 256³ resolution convergence assessment

Original validation showed 256³ simulations timed out at 4 hours before reaching t_frag. With Phase 4 adiabatic runs reaching t > 30 t_J in 5 hours, 6 hours should be sufficient for completion.

**Approach**: Re-run 8-10 representative parameter points at 256³ with 6-hour timeout to compare with 128³ results.

---

## SIMULATION SPECIFICATIONS

### Common Parameters (All Simulations)
- **Code**: Athena++ v21.0
- **Physics**: Self-gravity, ideal MHD, isothermal EOS (γ = 1)
- **Grid**: 
  - 128³: 256×64×64 cells (MeshBlock: 32³)
  - 256³: 512×128×128 cells (MeshBlock: 32³)
- **Domain**: 8×2×2 λ_J (cubic)
- **Boundary conditions**: Periodic on all faces
- **Integrator**: VL2 (integrator), HLLD flux
- **Self-gravity**: FFT Poisson solver (four_pi_G = 4π²)
- **Turbulence**: Kolmogorov spectrum, 8 modes, amplitude δv = M × 10⁻⁴

### Athena++ Problem
- **File**: `filament_spacing_re-run.cpp` (provided)
- **Compilation instructions**: See `README_FIRST.md`

### Execution Configuration
- **Ray version**: 2.55.0 or later
- **Max concurrent**: 4 simulations
- **MPI ranks per simulation**: 16
- **Wall-clock timeout**: 6 hours (21600 seconds)
- **HDF5 output**: Disabled (not needed for t_frag measurement)
- **History output**: Enabled (0.05 t_J intervals)

---

## PRIORITY 1: DTC RE-RUN SPECIFICATIONS

### Simulation Grid (15 points)
Selected from DTC "STABLE" grid at β = 0.3, M = 1.0:

| Run ID | f (line-mass) | β (plasma) | M (Mach) | Seed | Resolution |
|--------|---------------|-------------|-----------|------|------------|
| dtc_rerun_001 | 1.4 | 0.3 | 1.0 | 1 | 128³ |
| dtc_rerun_002 | 1.4 | 0.3 | 1.0 | 2 | 128³ |
| dtc_rerun_003 | 1.5 | 0.3 | 1.0 | 1 | 128³ |
| dtc_rerun_004 | 1.5 | 0.3 | 1.0 | 2 | 128³ |
| dtc_rerun_005 | 1.6 | 0.3 | 1.0 | 1 | 128³ |
| dtc_rerun_006 | 1.6 | 0.3 | 1.0 | 2 | 128³ |
| dtc_rerun_007 | 1.7 | 0.3 | 1.0 | 1 | 128³ |
| dtc_rerun_008 | 1.8 | 0.3 | 1.0 | 1 | 128³ |
| dtc_rerun_009 | 1.8 | 0.3 | 1.0 | 2 | 128³ |
| dtc_rerun_010 | 1.9 | 0.3 | 1.0 | 1 | 128³ |
| dtc_rerun_011 | 1.9 | 0.3 | 1.0 | 2 | 128³ |
| dtc_rerun_012 | 2.0 | 0.3 | 1.0 | 1 | 128³ |
| dtc_rerun_013 | 2.0 | 0.3 | 1.0 | 2 | 128³ |
| dtc_rerun_014 | 2.1 | 0.3 | 1.0 | 1 | 128³ |
| dtc_rerun_015 | 2.2 | 0.3 | 1.0 | 1 | 128³ |

**Selection Rationale**:
- Spans the full f range (1.4-2.2) of DTC STABLE region
- Two seeds per f value to test stochasticity
- Most likely to fragment with longer runtime (low f, low β)

### Expected Outcomes:
- **FRAG**: Simulation reaches t_frag < 1.425 t_J → confirms DTC STABLE was timeout artifact
- **STABLE**: Simulation reaches timeout without t_frag → confirms true stability
- **MIXED**: Different outcomes between seeds → identifies stochastic boundary

---

## PRIORITY 2: RESOLUTION RE-RUN SPECIFICATIONS

### Simulation Grid (10 points)

Selected from supercritical campaign to test resolution dependence:

| Run ID | f | β | M | Seed | Resolution | Original 128³ t_frag |
|--------|---|---|---|------|------------|----------------------|
| res_rerun_001 | 1.5 | 0.3 | 2.0 | 1 | 256³ | 0.272 t_J |
| res_rerun_002 | 1.5 | 0.3 | 2.0 | 1 | 256³ | 0.272 t_J |
| res_rerun_003 | 1.5 | 1.0 | 2.0 | 1 | 256³ | 0.291 t_J |
| res_rerun_004 | 1.5 | 1.0 | 2.0 | 1 | 256³ | 0.291 t_J |
| res_rerun_005 | 2.0 | 0.3 | 1.0 | 1 | 256³ | 0.281 t_J |
| res_rerun_006 | 2.0 | 0.3 | 1.0 | 1 | 256³ | 0.281 t_J |
| res_rerun_007 | 2.0 | 1.0 | 1.0 | 1 | 256³ | 0.295 t_J |
| res_rerun_008 | 2.0 | 1.0 | 1.0 | 1 | 256³ | 0.295 t_J |
| res_rerun_009 | 2.5 | 0.3 | 1.0 | 1 | 256³ | 0.274 t_J |
| res_rerun_010 | 3.0 | 0.3 | 1.0 | 1 | 256³ | 0.251 t_J |

**Selection Rationale**:
- Spans f range 1.5-3.0 (supercritical regime)
- Tests β = 0.3 (strong field) and β = 1.0 (moderate field)
- Tests M = 1.0 and M = 2.0
- Resolution difference: 2× linear resolution (8× total cells)

### Expected Outcomes:
- **Agreement**: 256³ t_frag within 5% of 128³ t_frag → resolution convergence confirmed
- **Disagreement**: Systematic offset > 5% → resolution dependence quantified
- **Incomplete**: Still times out → documents resolution uncertainty

---

## ANALYSIS PIPELINE

### 1. Fragmentation Detection (Automatic)
Simulation is monitored for runaway Jeans collapse:
- **Criterion**: Δt < 10⁻⁸ tJ (CFL limit from collapsing core)
- **Action**: Terminate simulation and record t_frag
- **Classification**: FRAG (fragmented) or TIMEOUT (no fragmentation)

### 2. Post-Processing (For DTC Re-runs)
Compare with original DTC results:
- **Original classification**: STABLE (from 600s timeout)
- **New classification**: FRAG, STABLE, or TIMEOUT
- **Outcome measure**: Fraction of original STABLE points that fragment with longer runtime

### 3. Resolution Analysis (For Resolution Re-runs)
Compare 256³ results with 128³ reference:
- **Metric**: Relative difference in t_frag
- **Threshold**: <5% = converged, >5% = resolution-dependent
- **Outcome**: Quantify resolution uncertainty across parameter space

---

## OUTPUT REQUIREMENTS

### Per-Simulation Status File (JSON)
Each simulation produces `status_{run_id}.json`:

```json
{
  "run_id": "dtc_rerun_001",
  "f": 1.4,
  "beta": 0.3,
  "mach": 1.0,
  "seed": 1,
  "resolution": "128",
  "status": "FRAG | STABLE | TIMEOUT",
  "t_frag": 1.234,
  "t_frag_units": "t_J",
  "t_final": 1.234,
  "dt_min": 1.23e-08,
  "wall_time_seconds": 14500,
  "mpi_ranks": 16,
  "n_core_particles": 1
}
```

### Final Summary Report
After completion, generate `RE_RUN_SUMMARY.md` containing:

#### DTC Re-run Summary
- Total FRAG count
- Total STABLE count  
- Total TIMEOUT count
- Fraction of original DTC STABLE that were timeout artifacts
- Updated interpretation of Figure 2 reliability

#### Resolution Re-run Summary  
- Number of comparisons showing convergence (<5% difference)
- Number showing resolution dependence (>5% difference)
- Quantified resolution uncertainty
- Recommendation on 128³ vs 256³ for future work

---

## DIRECTORY STRUCTURE

```
targeted_re_runs/
├── README_FIRST.md              # START HERE
├── CAMPAIGN_SPEC.md               # This file
├── simulations/
│   ├── run_list.json            # Complete list of 25 runs
│   ├── athena_input_template.dat # Athena++ input file template
│   └── filament_spacing_reun.cpp  # Problem generator source code
├── ray_executor/
│   ├── launch_re_runs.py         # Main Ray launch script
│   ├── monitor_campaign.py       # Progress monitoring
│   └── analyze_results.py        # Post-processing analysis
├── analysis/
│   ├── extract_tfrag.py           # Extract t_frag from history files
│   ├── compare_resolution.py      # Resolution convergence analysis
│   ├── generate_summary.py        # Generate final report
│   └── plot_results.py           # Generate figures
└── output/
    ├── status/                   # Status JSON files
    ├── figures/                  # Analysis figures
    └── RE_RUN_SUMMARY.md         # Final report
```

---

## EXECUTION INSTRUCTIONS FOR REMOTE OPERATOR

### Step 1: Extract and Prepare
```bash
tar -xzf targeted_re_runs.tar.gz
cd targeted_re_runs
```

### Step 2: Compile Athena++ (First Time Only)
```bash
cd scripts
bash compile_athena.sh
# This produces the athena_reun binary
```

### Step 3: Install Python Dependencies
```bash
pip3 install ray numpy pandas matplotlib h5py scipy
```

### Step 4: Launch Campaign
```bash
cd ray_executor
python3 launch_re_runs.py --all
# OR for specific priorities:
python3 launch_re_runs.py --priority 1  # DTC re-runs only
python3 launch_re_runs.py --priority 2  # Resolution re-runs only
```

### Step 5: Monitor Progress
```bash
# In a separate terminal:
cd ray_executor
python3 monitor_campaign.py
# Shows real-time progress, estimated completion time
```

### Step 6: Analyze Results (After Completion)
```bash
cd analysis
python3 extract_tfrag.py
python3 compare_resolution.py
python3 generate_summary.py
python3 plot_results.py
```

### Step 7: Package Results
```bash
# Creates results package:
tar -czf ../re_run_results.tar.gz status/ figures/ RE_RUN_SUMMARY.md
```

---

## TIME ESTIMATES

### Per-Simulation Wall Time
- **128³ simulations**: ~1-1.5 hours (typical for near-critical)
- **256³ simulations**: ~3-5 hours (higher resolution, smaller timestep)

### Campaign Duration (at 4 concurrent)
- **Priority 1 (15 sims)**: 15 × 1.25 h / 4 = ~4.7 hours
- **Priority 2 (10 sims)**: 10 × 4 h / 4 = ~10 hours
- **Total**: ~15 hours + overhead ≈ 1 day of dedicated runtime

### With Resource Sharing (200 CPUs, 4 concurrent = 64 MPI ranks per sim)
- **Efficiency**: ~85% (some queue time, checkpoints)
- **Realistic total**: ~1.5 days

---

## CRITICAL: TIMEOUT HANDLING

The 6-hour (21600 second) timeout is CRITICAL and must be enforced:

```python
# In Ray executor
TIMEOUT_SECONDS = 21600  # 6 hours in seconds
```

**Do NOT reduce this timeout**. The entire scientific value of these re-runs depends on running simulations long enough to distinguish true stability from timeout artifacts.

---

## SUCCESS CRITERIA

### DTC Re-runs Successful If:
- At least 12 of 15 simulations complete
- Classification (FRAG/STABLE/TIMEOUT) is unambiguous
- Results can be compared meaningfully with original DTC

### Resolution Re-runs Successful If:
- At least 8 of 10 simulations complete  
- t_frag values can be extracted from history files
- Comparison with 128³ reference is possible

### Overall Campaign Successful If:
- Both Priority 1 and Priority 2 meet success criteria
- Uncertainties are quantified and can be propagated through paper
- Results enable honest discussion of limitations

---

## TROUBLESHOOTING

### Simulation crashes immediately
- Check input file syntax
- Verify MPI ranks per simulation matches available CPUs
- Check disk space (>10 GB per simulation for temporary files)

### All simulations timeout
- Reduce concurrent simulations from 4 to 2
- Check that MPI is properly configured

### History files not generated
- Verify HST output is enabled in input file
- Check file write permissions

### Ray initialization errors
```bash
ray stop
ray start --head
```

---

## CONTACT FOR SUPPORT

If you encounter any issues:
1. Check this README first
2. Check status/ directory for error logs
3. Monitor progress with monitor_campaign.py (shows verbose errors)
4. Document all failures in status/ for debugging

**IMPORTANT**: Each simulation should create a log file. If a simulation fails, save the log for debugging.

---

## Expected Deliverables to Author

After completion, provide the following to glenn@ou.ac.uk:

1. `status/` directory - All 25 status JSON files
2. `figures/` directory - Analysis figures (PDF format)
3. `RE_RUN_SUMMARY.md` - Comprehensive summary report
4. `analysis_results.tar.gz` - All analysis code and intermediate results

These will be integrated into the revised manuscript.
