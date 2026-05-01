# Definitive 2D Fragmentation Transition Campaign
# Complete (f, β) Parameter Space Mapping

## Campaign Overview

This is the **FINAL MHD campaign** for the ASTRA filament spacing paper. It will definitively map the 2D fragmentation transition boundary in (f, β) space, answering whether the transition depends primarily on f, β, or a combination.

### Scientific Questions

1. **Does the transition depend on f only?** → Vertical boundary in (f, β) plane
2. **Does the transition depend on β only?** → Horizontal boundary in (f, β) plane
3. **Does it depend on f·β or f/β?** → Diagonal boundary in (f, β) plane
4. **Does Mach number affect the transition?** → Boundary shifts with M

### What Makes This Definitive

1. **Complete 2D coverage**: 9 f values × 6 β values = 54 (f, β) pairs
2. **Statistical robustness**: 2 seeds per parameter set
3. **Mach independence test**: 5 Mach numbers (1.0, 2.0, 3.0, 4.0, 5.0)
4. **Sufficient resolution**: 256³ cells (well-resolved fragmentation)
5. **No follow-up needed**: This should be the final word on the transition

## Simulation Grid: 648 Runs Total

### Primary Grid: 324 simulations

| Parameter | Values | Count |
|-----------|--------|-------|
| f (supercriticality) | 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2 | 9 |
| β (plasma beta) | 0.3, 0.5, 0.7, 0.9, 1.1, 1.3 | 6 |
| M (Mach) | 1.0, 2.0, 3.0 | 3 |
| Seeds | 42, 137 | 2 |

### Extended Grid: 108 simulations

Same (f, β) grid with M = 4.0, 5.0 to test supersonic regime.

### Resolution & Domain

- **Grid**: 256 × 256 × 256 cells (64³ meshblocks)
- **Domain**: 16λ_J × 4λ_J × 4λ_J (periodic)
- **Runtime**: 4.0 t_J with 40 snapshots
- **Physics**: HLLD solver, FFT self-gravity, isothermal EOS

## Computational Requirements

| Metric | Value |
|--------|-------|
| **Per simulation** | ~3-5 hours on 64 cores |
| **Total core-hours** | ~155,000 (155k) |
| **Wall time (200 cores)** | ~77 hours (3.2 days) |
| **Disk space** | ~3.2 TB |

## Quick Start

### 1. Update Paths

Edit `quickstart.sh` and set:
```bash
ATHENA_BINARY="/path/to/your/athena/bin/athena"
SIMULATION_BASE="/path/to/simulations/definitive_transition_campaign_apr2026"
```

### 2. Generate Configurations

```bash
python3 generate_simulations.py
```

Creates 648 directories with `athena_input.dat` files.

### 3. Run Campaign (with Ray)

**Option A: Run all at once**
```bash
bash quickstart.sh
```

**Option B: Run in phases**
```bash
# Phase 1: Primary grid (M = 1.0, 2.0, 3.0)
python3 run_campaign.py --phase primary --num-workers 200

# Phase 2: Extended grid (M = 4.0, 5.0)
python3 run_campaign.py --phase extended --num-workers 200
```

**Option C: Resume from interruption**
```bash
bash quickstart.sh --resume
```

### 4. Analyze Results

```bash
python3 analyze_campaign.py
```

Outputs:
- `definitive_transition_analysis.json` - All metrics
- `figures/transition_boundary_M*.pdf` - 2D transition maps
- `figures/cross_sections_M*.pdf` - Cross-sectional plots

## Expected Scientific Results

### Hypothesis Testing

| Hypothesis | Prediction | How to Test |
|------------|------------|-------------|
| **H1: f-only** | Vertical boundary | C_final independent of β at fixed f |
| **H2: β-only** | Horizontal boundary | C_final independent of f at fixed β |
| **H3: f·β or f/β** | Diagonal boundary | C_final constant along f·β = const or f/β = const |
| **H4: Mach-dependent** | Boundary shifts with M | Compare transition at M = 1.0 vs 5.0 |

### Expected Transition Zone

Based on moderate supercriticality (β = 2/f²) results:

| f \ β | 0.3 | 0.5 | 0.7 | 0.9 | 1.1 | 1.3 |
|-------|-----|-----|-----|-----|-----|-----|
| **1.4** | SUPP | SUPP | TRANS | FRAG | FRAG | FRAG |
| **1.5** | SUPP | SUPP | TRANS | FRAG | FRAG | FRAG |
| **1.6** | SUPP | SUPP | TRANS | FRAG | FRAG | FRAG |
| **1.7** | SUPP | SUPP | SUPP | TRANS | FRAG | FRAG |
| **1.8** | SUPP | SUPP | SUPP | TRANS | FRAG | FRAG |
| **1.9** | SUPP | SUPP | SUPP | SUPP | TRANS | FRAG |
| **2.0** | SUPP | SUPP | SUPP | SUPP | TRANS | FRAG |
| **2.1** | SUPP | SUPP | SUPP | SUPP | SUPP | TRANS |
| **2.2** | SUPP | SUPP | SUPP | SUPP | SUPP | TRANS |

Legend:
- **FRAG**: C_final > 2.0 (vigorous fragmentation)
- **SUPP**: C_final < 1.5 (suppressed)
- **TRANS**: 1.5 < C_final < 2.0 (transition zone)

## Key Deliverables

### 1. Complete Dataset
- 648 × (C_final, n_cores, λ_frag, λ/W)
- Full 2D coverage of (f, β) space
- Statistical robustness from 2 seeds

### 2. Transition Boundary Function
- Functional fit: f_crit(β) or β_crit(f)
- Uncertainty quantification
- Mach dependence (if any)

### 3. Publication Figures
- 2D colormap of C_final(f, β) for each M
- Cross-sections: C_final vs f (by β)
- Cross-sections: C_final vs β (by f)

### 4. Scientific Conclusions
- Definitive answer: f, β, or combination?
- Allowed (f, β) region for HGBS filaments
- Predictive model for fragmentation state

## Integration with Paper

### Abstract Update
```
"A definitive 648-simulation campaign mapping the 2D fragmentation
transition boundary reveals that [CONCLUSION]. The transition
depends primarily on [PARAMETER], with functional form
[FORMULA]. For HGBS filaments (λ/W = 2.11), this constrains
the allowed parameter space to f ≈ X-Y, β ≈ A-B."
```

### New Section: "Definitive Transition Boundary"
- 2D colormaps of C_final(f, β)
- Transition boundary fit
- Mach independence test

### Future Work Update
- **Remove**: "Expanded simulation grid at f ≈ 1.5-2.5"
- **Add**: "Observational tests: (1) Fiber-resolved spacing, (2) Polarimetric β measurements"

## Troubleshooting

### Athena++ not found
```bash
# Update ATHENA_BINARY in quickstart.sh
ATHENA_BINARY="/correct/path/to/athena/bin/athena"
```

### Ray cluster issues
```bash
# Check cluster status
ray status

# Restart cluster
ray stop
ray start --head --num-cpus 200
```

### Out of memory
```bash
# Reduce concurrent simulations
python3 run_campaign.py --num-workers 150
```

### Analysis fails with HDF5 error
```bash
# Install HDF5 libraries
pip install h5py h5py-mpi
```

## Success Criteria

✓ **Complete coverage**: No gaps in (f, β) space around transition
✓ **Statistical robustness**: 2 seeds per parameter set
✓ **Mach independence**: Test M = 1.0, 2.0, 3.0, 4.0, 5.0
✓ **Definitive boundary**: Functional form with uncertainties
✓ **No follow-up needed**: This is the final MHD campaign

## Files Generated

```
definitive_transition_campaign_apr2026/
├── README.md
├── quickstart.sh
├── definitive_transition_spec.md
├── generate_simulations.py
├── run_campaign.py
├── analyze_campaign.py
├── simulation_manifest.json
└── DTC_f1.4_b0.3_M1.0_s42/
    ├── athena_input.dat
    └── ... (snapshots)
```

## Timeline

- **Day 1**: Generate configs, start runs
- **Day 2-3**: Run simulations (3 days total)
- **Day 4**: Analyze results, generate figures
- **Day 5**: Update paper with definitive results

---
*Definitive campaign for ASTRA filament spacing paper - April 2026*
*Total: 648 simulations, 3 days on 200 vCPUs*
*Final MHD campaign - no additional runs needed*
