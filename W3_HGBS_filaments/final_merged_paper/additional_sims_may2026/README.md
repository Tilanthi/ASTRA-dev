# Additional Resolution Comparison Simulations
## May 2026 - Paper Enhancement

**Purpose**: Complete the resolution convergence analysis by running 128³ reference simulations with matching problem generator to the 256³ re-runs.

**Campaign**: 10 Athena++ MHD simulations at 128³ resolution
**Target System**: External computer with 200 CPUs, Ray distributed task scheduler
**Completion Time**: ~30-45 minutes per simulation × 10 sims = ~5-7 hours total

---

## BACKGROUND

The April 2026 targeted re-runs (Priority 2) tested 10 simulations at 256³ resolution, all of which fragmented successfully. However, the reference 128³ values used for comparison came from the **DTC problem generator** (`filament_dtc`), which uses different initial conditions than the **PRR problem generator** (`filament_validation.cpp`) used for the 256³ re-runs.

The 2.4-4.2× ratio between 256³ and 128³ t_frag values therefore reflects **pgen differences**, not pure resolution effects.

---

## OBJECTIVE

Run the same 5 unique parameter points (plus duplicate seeds) at **128³ resolution using the PRR problem generator** to enable a clean resolution convergence comparison.

This will allow us to answer: **"What is the true resolution dependence of t_frag for our simulation setup?"**

---

## SIMULATION SPECIFICATIONS

### Problem Generator
- **File**: `filament_validation.cpp` (PRR pgen)
- **Initial conditions**: King profile filament + PRR perturbations
- **four_pi_G**: 4π² (same as 256³ re-runs)

### Common Parameters
- **Code**: Athena++ v21.0
- **Physics**: Self-gravity, ideal MHD, isothermal EOS (γ = 1)
- **Resolution**: 128³ (256×64×64 cells, MeshBlock: 32³)
- **Domain**: 8×2×2 λ_J (cubic)
- **Boundary conditions**: Periodic on all faces
- **Integrator**: VL2, HLLD flux
- **Self-gravity**: FFT Poisson solver (four_pi_G = 4π²)
- **Turbulence**: Kolmogorov spectrum, 8 modes, amplitude δv = M × 10⁻⁴

### Execution Configuration
- **Ray version**: 2.55.0 or later
- **Max concurrent**: 10 simulations (run all at once for efficiency)
- **MPI ranks per simulation**: 16
- **Wall-clock timeout**: 7200 seconds (2 hours) per simulation
- **Expected runtime**: ~30-45 minutes per simulation

---

## SIMULATION GRID (10 total)

| Run ID | f | β | M | Seed | Resolution | Expected t_frag |
|--------|---|---|---|------|------------|------------------|
| res_ref_001 | 1.5 | 0.30 | 2.0 | 1 | 128³ | ~1.15 t_J |
| res_ref_002 | 1.5 | 0.30 | 2.0 | 1 | 128³ | ~1.15 t_J |
| res_ref_003 | 1.5 | 1.00 | 2.0 | 1 | 128³ | ~0.77 t_J |
| res_ref_004 | 1.5 | 1.00 | 2.0 | 1 | 128³ | ~0.77 t_J |
| res_ref_005 | 2.0 | 0.30 | 1.0 | 1 | 128³ | ~0.95 t_J |
| res_ref_006 | 2.0 | 0.30 | 1.0 | 1 | 128³ | ~0.95 t_J |
| res_ref_007 | 2.0 | 1.00 | 1.0 | 1 | 128³ | ~0.69 t_J |
| res_ref_008 | 2.0 | 1.00 | 1.0 | 1 | 128³ | ~0.69 t_J |
| res_ref_009 | 2.5 | 0.30 | 1.0 | 1 | 128³ | ~0.81 t_J |
| res_ref_010 | 3.0 | 0.30 | 1.0 | 1 | 128³ | ~0.71 t_J |

**Note**: Expected t_frag values are estimated from the 256³ re-run results, scaled by the approximate resolution dependence factor.

---

## EXECUTION INSTRUCTIONS

### Step 1: Extract and Prepare
```bash
tar -xzf additional_sims_may2026.tar.gz
cd additional_sims_may2026
```

### Step 2: Verify Athena++ Binary
Ensure the `athena_reun` binary from the previous campaign is available. If not, compile using:
```bash
cd ../targeted_re_runs/scripts
bash compile_athena.sh
```

### Step 3: Install Python Dependencies
```bash
pip3 install ray[default] numpy pandas
```

### Step 4: Launch Campaign
```bash
python3 launch_resolution_ref.py --all
```

### Step 5: Monitor Progress
```bash
python3 monitor_sims.py
```

### Step 6: Analysis (After Completion)
```bash
python3 compare_resolution_clean.py
python3 generate_final_figure.py
```

---

## EXPECTED OUTCOMES

### Scenario A: Clean Resolution Convergence
If t_frag(128³) ≈ t_frag(256³) within 5-10%:
- Resolution dependence is minimal
- 128³ resolution is adequate
- Paper can state: "Fragmentation timescales are resolution-independent to within 10%"

### Scenario B: Systematic Resolution Dependence
If t_frag(256³) > t_frag(128³) by >10%:
- Higher resolution delays fragmentation
- Paper should state: "Fragmentation occurs at later times with higher resolution"
- Quantify the resolution scaling factor

### Scenario C: Complex Behavior
If some points converge while others don't:
- Resolution dependence may be parameter-dependent
- Paper should state: "Resolution dependence varies with (f, β, M)"
- Identify which parameters show resolution sensitivity

---

## OUTPUT FILES

Each simulation produces:
```
output/simulations/<run_id>/
├── athena_input_<run_id>.dat
├── <run_id>.hst
├── <run_id>.log
└── status_<run_id>.json
```

Final analysis produces:
```
output/analysis/
├── resolution_comparison_clean.json
├── final_summary.md
└── figure_resolution_convergence_final.pdf
```

---

## DELIVERABLES

After completion, provide:
1. All 10 status JSON files
2. Final summary report
3. Resolution convergence figure (PDF/PNG)
4. Comparison with 256³ re-run results

These will be integrated into the revised manuscript as:
- Updated resolution convergence section
- New figure showing clean 128³ vs 256³ comparison
- Updated acknowledgments with figure reference

---

## CONTACT

For questions about this campaign:
- Glenn J. White: glenn@ou.ac.uk
- ASTRA system: autonomous analysis support

---

## SUCCESS CRITERIA

✓ All 10 simulations complete (FRAG status)
✓ t_frag values extracted from all simulations
✓ Comparison with 256³ results shows clear convergence trend
✓ Figure generated showing clean resolution comparison
✓ Summary report written with recommendations for paper

---

## CRITICAL NOTES

1. **Use the PRR problem generator** (`filament_validation.cpp`), NOT the DTC pgen
2. **Keep all other parameters identical** to the 256³ re-runs
3. **2-hour timeout is sufficient** - these 128³ runs should fragment in <1 hour
4. **No HDF5 output needed** - history files are sufficient for t_frag measurement

---

## TIMELINE

- **Preparation**: 30 minutes
- **Simulation runtime**: 5-7 hours (10 sims × 30-45 min, 10 concurrent = ~1 batch)
- **Analysis**: 1 hour
- **Total**: <1 day

---

## NEXT STEPS AFTER COMPLETION

1. Run analysis scripts to generate comparison figure
2. Integrate results into paper
3. Update resolution convergence section with clean comparison
4. Submit revised manuscript with complete resolution analysis
