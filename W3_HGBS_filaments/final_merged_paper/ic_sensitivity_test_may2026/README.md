# IC Sensitivity Test - Near-Critical Filament Fragmentation
## May 2026 - Referee Response T3

**Purpose**: Test sensitivity of fragmentation wavelength (λ/W) to initial condition (IC) choices in the near-critical regime (f ≈ 1.0-1.3).

**Campaign**: 48 Athena++ MHD simulations testing two IC types across the near-critical parameter space.
**Target System**: External computer with 200+ CPUs, Ray distributed task scheduler
**Completion Time**: ~2-3 hours per simulation × 48 sims = ~4-6 days (with 16 concurrent sims)

---

## BACKGROUND

The referee raised an important concern (Technical point T3): our simulations have not tested IC sensitivity in the **near-critical regime** (f ≈ 1.0-1.3), where fragmentation behavior might be most sensitive to initial conditions.

Our previous campaigns focused on:
- **DTC Campaign**: f = 1.0-5.0, King profile IC only
- **Full 2193-simulation analysis**: f = 1.5-5.0, King profile IC only

**We have never tested**: Whether uniform density ICs produce different λ/W measurements in the near-critical regime.

This matters because:
1. Near-critical filaments (f ≈ 1.0-1.3) are theoretically expected to be most sensitive to IC details
2. If λ/W depends strongly on IC choice in this regime, our results may not be robust
3. If λ/W is IC-independent, this strengthens confidence in the theoretical predictions

---

## OBJECTIVE

Run a focused IC sensitivity test in the near-critical regime (f = 1.00-1.30) by:

1. Running simulations with **two different IC types**:
   - **King profile**: ρ(x,y) = ρ_0 / [1 + (r/r_core)²] (our standard setup)
   - **Uniform density**: ρ(x,y) = ρ_0 = constant (alternative IC)

2. Measuring λ/W from HDF5 snapshots for both IC types

3. Comparing results to test for systematic differences

4. Answering: **"Is the fragmentation wavelength in the near-critical regime sensitive to initial condition choice?"**

---

## SIMULATION SPECIFICATIONS

### Problem Generators
- **King profile**: `filament_king_ic.cpp` (standard PRR setup)
- **Uniform density**: `filament_uniform_ic.cpp` (new uniform IC setup)

### Common Parameters
- **Code**: Athena++ v21.0
- **Physics**: Self-gravity, ideal MHD, isothermal EOS (γ = 1)
- **Resolution**: 256³ (256×64×64 cells, MeshBlock: 32³)
- **Domain**: 8×2×2 λ_J (cubic)
- **Boundary conditions**: Periodic on all faces
- **Integrator**: VL2, HLLD flux
- **Self-gravity**: FFT Poisson solver (four_pi_G = 4π²)
- **Turbulence**: Kolmogorov spectrum, 8 modes, amplitude δv = M × 10⁻⁴
- **HDF5 output**: Every 0.1 t_J, retain for λ/W measurement

### Execution Configuration
- **Ray version**: 2.55.0 or later
- **Max concurrent**: 16 simulations (optimized for 200 CPU cluster)
- **MPI ranks per simulation**: 16
- **Wall-clock timeout**: 10800 seconds (3 hours) per simulation
- **Expected runtime**: ~1-2 hours per simulation

---

## SIMULATION GRID (48 total)

### Parameter Space
- **f (mass-to-flux ratio)**: 1.00, 1.10, 1.20, 1.30 (4 values)
- **β (plasma beta)**: 0.3, 0.5, 1.0 (3 values)
- **M (Mach number)**: 1.0, 2.0 (2 values)
- **IC type**: King, Uniform (2 types)
- **Seeds**: 1, 2 (2 seeds per unique point for redundancy)

**Total**: 4 × 3 × 2 × 2 × 2 = 48 simulations

### Expected Behavior

| f | Expected Fragmentation |
|---|------------------------|
| 1.00 | Marginal - may not fragment within 3 t_J |
| 1.10 | Near-critical - fragmentation likely |
| 1.20 | Near-critical - fragmentation expected |
| 1.30 | Weakly supercritical - fragmentation expected |

**Note**: f = 1.00 simulations may timeout (no fragmentation). This is acceptable - the absence of fragmentation is scientifically informative.

---

## EXECUTION INSTRUCTIONS

### Step 1: Extract and Prepare
```bash
tar -xzf ic_sensitivity_test_may2026.tar.gz
cd ic_sensitivity_test_may2026
```

### Step 2: Compile Athena++ with Both Problem Generators

The package includes two problem generator files that must be compiled into Athena++:

```bash
# Copy problem generators to Athena++ source directory
cp src/filament_king_ic.cpp /path/to/athena/src/pgen/
cp src/filament_uniform_ic.cpp /path/to/athena/src/pgen/

# Configure and compile Athena++
cd /path/to/athena
./configure --prob=file_king_ic --with-gas=hydro+mhd sgfft
make

# Recompile for uniform IC
./configure --prob=file_uniform_ic --with-gas=hydro+mhd sgfft
make
```

**Alternative**: If your Athena++ build system supports multiple pgen compilation, compile both at once.

### Step 3: Install Python Dependencies
```bash
pip3 install ray[default] numpy pandas h5py matplotlib scipy
```

### Step 4: Launch Campaign
```bash
python3 launch_ic_sensitivity.py --all
```

**Options**:
- `--all`: Run all 48 simulations
- `--king-only`: Run only King profile IC simulations (24)
- `--uniform-only`: Run only uniform density IC simulations (24)
- `--test`: Run 2 test simulations first

### Step 5: Monitor Progress
```bash
python3 monitor_sims.py
```

This will show:
- Number of simulations completed/remaining
- Current fragmentation status
- Estimated time to completion

### Step 6: Analysis (After Completion)
```bash
# Step 6a: Measure λ/W from HDF5 snapshots
python3 analyze_lambda_W.py

# Step 6b: Compare IC types
python3 compare_ic_sensitivity.py

# Step 6c: Generate figures
python3 generate_ic_comparison_figures.py
```

---

## EXPECTED OUTCOMES

### Scenario A: No IC Dependence (Ideal Result)
If λ/W(King) ≈ λ/W(Uniform) within 5-10%:
- Fragmentation wavelength is robust to IC choice
- Paper can state: "λ/W measurements in the near-critical regime are insensitive to initial condition details"
- Strengthens confidence in theoretical predictions

### Scenario B: Weak IC Dependence (Acceptable Result)
If λ/W differs by 10-20% between IC types:
- Some sensitivity to IC choice
- Paper should state: "λ/W shows mild dependence (~15%) on initial conditions in the near-critical regime"
- Recommend standardizing on one IC type for future work

### Scenario C: Strong IC Dependence (Problematic Result)
If λ/W differs by >30% between IC types:
- Near-critical fragmentation is highly IC-dependent
- Paper must state: "λ/W measurements in the near-critical regime are sensitive to initial condition choice"
- Theoretical predictions become more uncertain
- May require additional physics (non-ideal MHD, etc.) to explain

---

## OUTPUT FILES

### Each Simulation Produces
```
output/simulations/<run_id>/
├── athena_input_<run_id>.dat
├── <run_id>.hst              # History file (t_frag detection)
├── <run_id>.log              # Log file
├── <run_id>_out*.hdf5        # HDF5 snapshots (λ/W measurement)
└── status_<run_id>.json      # Status summary
```

### Final Analysis Produces
```
output/analysis/
├── lambda_W_measurements.json      # All λ/W values
├── ic_sensitivity_summary.json     # Statistical comparison
├── ic_comparison_figure.pdf        # King vs Uniform λ/W
├── ic_sensitivity_report.md        # Detailed findings
└── referee_response_T3.md          # Response to referee
```

---

## DATA ANALYSIS DETAILS

### λ/W Measurement Method

For each simulation that fragments:

1. **Load HDF5 snapshot**: Identify final snapshot with well-developed cores
2. **Extract column density**: Integrate ρ(x,y,z) along z-axis to get Σ(x,y)
3. **Identify cores**: Local maxima in Σ above threshold (1.5× background)
4. **Measure spacings**: Nearest-neighbor distances between cores
5. **Compute λ/W**: Median spacing / filament width (W = 2×r_core)

The analysis script `analyze_lambda_W.py` automates this process using the same methodology as the 2193-simulation analysis.

### Statistical Comparison

The comparison script computes:

1. **Mean difference**: ⟨λ/W_Uniform⟩ - ⟨λ/W_King⟩
2. **Normalized difference**: (⟨λ/W_Uniform⟩ - ⟨λ/W_King⟩) / ⟨λ/W_King⟩
3. **Parameter-by-parameter comparison**: Difference vs (f, β, M)
4. **Statistical significance**: t-test, KS test for distribution differences

---

## DELIVERABLES

After completion, provide:

1. **All 48 status JSON files** (fragmentation confirmation)
2. **λ/W measurements** for both IC types (CSV/JSON)
3. **Statistical comparison** between IC types
4. **IC comparison figure** (PDF/PNG)
5. **Referee response summary** for T3

These will be integrated into the revised manuscript as:
- New subsection on IC sensitivity in Section 4
- New figure showing King vs Uniform comparison
- Updated acknowledgments with campaign reference
- Response to referee Technical point T3

---

## SUCCESS CRITERIA

✓ All 48 simulations run (FRAG or TIMEOUT status acceptable)
✓ λ/W measured for all fragmenting simulations
✓ Statistical comparison completed between IC types
✓ Figure generated showing IC dependence (or lack thereof)
✓ Summary report written with recommendations for paper

**Note**: TIMEOUT at f = 1.00 is acceptable and expected. These non-fragmenting runs are scientifically informative.

---

## CRITICAL NOTES

1. **HDF5 output is REQUIRED** for λ/W measurement (unlike resolution reference campaign)
2. **Two different problem generators** must be compiled (King and Uniform IC)
3. **3-hour timeout** should be sufficient for most near-critical runs
4. **F = 1.00 runs may not fragment** - this is acceptable and expected
5. **Keep all other parameters identical** between IC types for clean comparison

---

## TIMELINE

- **Preparation**: 1 hour (compile Athena++ with both pgen)
- **Simulation runtime**: 4-6 days (48 sims × 1-2 hours, 16 concurrent)
- **Analysis**: 4-6 hours (λ/W measurement, comparison, figures)
- **Total**: ~1 week

---

## INTERPRETATION GUIDE

### For Referee Response

**If IC dependence is weak (<10% difference)**:
> "We have tested initial condition sensitivity by running 48 simulations in the near-critical regime (f = 1.0-1.3) with two different initial density profiles: a King profile (standard) and a uniform density profile. The fragmentation wavelength λ/W shows [minimal/mild] dependence on initial condition choice, with differences of [X%]. This [strengthens/confirms] the robustness of our theoretical predictions."

**If IC dependence is strong (>30% difference)**:
> "We have tested initial condition sensitivity by running 48 simulations in the near-critical regime (f = 1.0-1.3) with two different initial density profiles. The fragmentation wavelength λ/W shows significant dependence on initial condition choice, with differences of [X%]. This suggests that near-critical filament fragmentation is sensitive to initial condition details, and theoretical predictions in this regime should be interpreted with caution."

---

## CONTACT

For questions about this campaign:
- Glenn J. White: glenn@ou.ac.uk
- ASTRA system: autonomous analysis support

---

## REFERENCES

- Original DTC campaign: `DTC_results_summary.json`
- Full 2193-simulation analysis: `filament_spacing_streamlined_mnras.tex`
- Problem generator reference: `filament_dtc.cpp` (King profile IC)
- Uniform IC reference: `filament_uniform_ic.cpp` (new for this campaign)

---

## NEXT STEPS AFTER COMPLETION

1. Run analysis scripts to measure λ/W for all fragmenting simulations
2. Perform statistical comparison between King and Uniform IC results
3. Generate IC comparison figures
4. Integrate findings into paper Section 4
5. Write referee response for Technical point T3
6. Submit revised manuscript with complete IC sensitivity analysis
