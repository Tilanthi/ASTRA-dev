# Moderate Supercriticality Test - Summary

## Objective

Test the magnetic tension hypothesis for filament fragmentation by running self-gravitating MHD simulations in the **moderately supercritical regime** (f ≈ 1-3), where magnetic effects should be detectable.

## Background

The new fragmentation analysis in `filament_frag_analysis/` shows:
- **Highly supercritical filament** (f = 6.6): λ/W ≈ 0.94, **independent of β**
- **Observed filaments**: λ/W ≈ 2.1
- **IM92 near-critical**: λ/W ≈ 4.0

**Key insight**: The observed spacing (2.1) is between the highly supercritical limit (0.94) and the near-critical IM92 value (4.0). This suggests real filaments are **moderately supercritical** (f ≈ 2-3), where magnetic tension could reduce the spacing from the IM92 value.

## Simulation Design

| Parameter | Values | Rationale |
|-----------|--------|-----------|
| Central density ρ_c | 2.0, 3.0, 5.0 | Gives f ≈ 0.8, 1.2, 2.0 |
| Plasma β | 0.5, 1.0, 2.0 | Strong, equipartition, weak B-field |
| Random seeds | 42, 137 | Statistical robustness |
| **Total simulations** | **18** | 3 × 3 × 2 |

**Grid**: 192 × 48 × 48 (reduced from 256 × 64 × 64 for speed)
**Domain**: 20 R_fil × 5 R_fil × 5 R_fil (same as before)

## Expected Results

### Analytic Predictions (from modified IM92 + magnetic tension)

| ρ_c | f | β=0.5 | β=1.0 | β=2.0 |
|-----|---|-------|-------|-------|
| 2.0 | 0.8 | Sub-critical (no frag) | Sub-critical | Sub-critical |
| 3.0 | 1.2 | ~2.5 | ~3.0 | ~3.5 |
| 5.0 | 2.0 | ~1.5 | ~2.0 | ~2.5 |

**Critical test**: At ρ_c = 5.0, β = 1.0 (f = 2.0):
- **Prediction**: λ/W ≈ 2.0
- **Observation**: λ/W = 2.1 ± 0.1
- **If confirmed**: Smoking gun for magnetic tension!

### What Different Outcomes Mean

| Outcome | Interpretation |
|---------|----------------|
| λ/W ≈ 4 at all β (f≈1) | Magnetic fields don't matter near criticality → tension hypothesis rejected |
| λ/W decreases with β (f≈2) | Magnetic tension is the key mechanism → hypothesis confirmed |
| λ/W ≈ 1 at all β (f≈2) | Already in Jeans-dominated regime → need higher f resolution |

## Computational Budget

**Hardware**: 12 CPUs
**Time**: 12-24 hours
**Budget**: 144-288 CPU-hours

**Estimated runtime**:
- Per simulation: ~45 minutes (12 cores)
- Total: ~13.5 hours (if running sequentially)
- Can run 12 simulations in parallel: ~1-2 hours wall time

✓ **Fits comfortably in budget!**

## How to Run

### 1. Generate Input Files

```bash
cd W3_HGBS_filaments/athena++
python3 generate_athena_inputs.py
```

Creates `.athinput` files in `athena_inputs/` directory.

### 2. Create Submission Script

```bash
python3 create_submission_script.py
```

Creates SLURM, PBS, and serial scripts in `submission_scripts/`.

### 3. Edit Script

Edit the `ATHENA_EXE` path at the top of the submission script to point to your Athena++ installation:

```bash
ATHENA_EXE=/path/to/athena++/bin/athena
```

### 4. Submit

```bash
# For SLURM
sbatch submission_scripts/submit_slurm.sh

# For PBS
qsub submission_scripts/submit_pbs.sh

# Or run serially (for testing)
bash submission_scripts/run_serial.sh
```

### 5. Monitor Progress

```bash
# Watch for output files
watch -n 60 'ls -lh outputs/*/ *.tab'

# Check tail of log
tail -f filament_mhd_*.out
```

### 6. Analyze Results

```bash
python3 analyze_fragmentation.py
```

Generates:
- `fragmentation_results.json`: Full results
- Console output with summary table

## Files Created

| File | Purpose |
|------|---------|
| `moderate_supercriticality_test.py` | Design exploration and estimates |
| `generate_athena_inputs.py` | Create `.athinput` files |
| `create_submission_script.py` | Create submission scripts |
| `analyze_fragmentation.py` | Analyze simulation outputs |
| `moderate_supercriticality_design.json` | Simulation parameter list |

## Next Steps After Simulations Complete

1. **Verify results**: Do λ/W values match predictions?
2. **Update paper**: Add new figure showing f vs λ/W for different β
3. **Interpret**: Does magnetic tension explain the observations?

If results confirm magnetic tension hypothesis:
- Strong evidence for magnetized fragmentation
- Paper becomes much stronger
- Clear path to publication

If results reject magnetic tension hypothesis:
- Still valuable negative result
- Rules out magnetic tension as explanation
- Points to other mechanisms (accretion, geometry)
- Honest science is good science

## Notes

- **Sub-critical filaments**: ρ_c = 2.0 (f = 0.8) may not fragment at all—this is useful for defining the critical boundary
- **Convergence**: The 192×48×48 grid may be marginal for convergence—if results look promising, consider re-running with higher resolution
- **Evolution time**: Lower density means longer collapse time—may need to extend `tmax` in `.athinput` if fragmentation isn't well-developed
