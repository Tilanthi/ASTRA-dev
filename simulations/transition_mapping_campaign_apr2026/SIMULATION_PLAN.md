# Transition Mapping Campaign - Complete Setup

## Campaign Goal

Map the sharp fragmentation transition between f = 1.5 and f = 2.0 to determine:
1. The exact (f, β) boundary where magnetic suppression becomes dominant
2. Whether HGBS filaments (λ/W ≈ 2.11) can be explained by f ≈ 1.5-2.0, β ≈ 0.5-1.5

## Simulation Grid (240 total)

| Parameter | Values | Count |
|-----------|--------|-------|
| Supercriticality (f) | 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5 | 11 |
| Plasma beta (β) | 0.5, 0.7, 0.9, 1.1, 1.3, 1.5 | 6 |
| Mach number (M) | 1.0, 2.0, 3.0 | 3 |
| Random seed | 42, 137 | 2 |

**Total**: 11 × 6 × 3 × 2 = 240 simulations

## Resolution & Domain

- **Grid**: 256³ cells
- **Meshblocks**: 64³ cells (4×4×4 decomposition = 64 meshblocks)
- **Domain**: 16λ_J × 4λ_J × 4λ_J (periodic)
- **Runtime**: 4.0 t_J (41 snapshots: every 0.1 t_J)
- **Outputs**: VTK (every 1.0 t_J) + TAB files (every 0.1 t_J)

## Physics Configuration

### Code Units
- Sound speed: c_s = 1
- Critical density: ρ_crit = 1
- Gravitational constant: 4πG = 2.636 (for ρ_c = 10)

### Filament Profile
Gaussian: ρ(r) = ρ_c exp(-r²/2)
- Width: W = 1
- Central density: ρ_c = 2f / (√(2π) × G_code)

### Magnetic Field
- Geometry: Uniform along filament axis (x-direction)
- Strength: B₀ = c_s √(2ρ_c/β)

### Turbulence
- Spectrum: Kolmogorov
- Mach: M = σ_turb/c_s
- Random seed: For reproducibility

## Computational Requirements

### Per Simulation
- **Memory**: ~8 GB (64 cores)
- **Time**: ~2-4 hours
- **Disk**: ~5 GB (outputs)

### Full Campaign
- **Core-hours**: ~46,000 (46k)
- **Wall time**: ~24-48 hours on 200 cores
- **Disk**: ~1.2 TB (240 simulations × 5 GB)

## Files Generated

### 1. Configuration Files (`generate_simulations.py`)

Creates 240 directories with:
```
MSC_f1.5_b0.5_M1.0_s42/
├── athena_input.dat  # Athena++ configuration
├── *.tab            # Snapshot data (HDF5)
└── *.vtk            # Visualization data
```

### 2. Manifest (`simulation_manifest.json`)

Lists all simulations with parameters:
```json
{
  "run_id": "MSC_f1.5_b0.5_M1.0_s42",
  "f": 1.5,
  "beta": 0.5,
  "mach": 1.0,
  "seed": 42,
  "rho_c": 1.2345,
  "B0": 2.3456,
  "status": "pending"
}
```

### 3. Results (`transition_mapping_analysis.json`)

Fragmentation metrics for each simulation:
```json
{
  "run_id": "MSC_f1.5_b0.5_M1.0_s42",
  "C_final": 2.507,
  "n_peaks": 7,
  "lambda_frag": 2.0,
  "lambda_frag_std": 0.0,
  "peak_positions": [-6.99, -5.20, -3.24, -1.21, 0.90, 2.85, 7.07]
}
```

## Execution Steps

### Step 1: Generate Configurations

```bash
cd /path/to/simulations/transition_mapping_campaign_apr2026
python3 generate_simulations.py
```

Output:
- `simulation_manifest.json` with 240 entries
- 240 directories with `athena_input.dat` files

### Step 2: Run Simulations (with Ray)

```bash
python3 run_campaign.py --num-workers 200
```

Or use quickstart:
```bash
bash quickstart.sh --step 2
```

Features:
- Automatic load balancing
- Checkpoint/resume capability
- Progress monitoring
- Error handling and logging

### Step 3: Analyze Results

```bash
python3 analyze_campaign.py
```

Output:
- `transition_mapping_analysis.json` with all metrics
- Summary statistics table
- Fragmentation status (YES/MARGINAL/NO)

## Expected Scientific Results

Based on previous moderate supercriticality campaign:

| f | β | Expected C_final | Expected λ/W | Fragmentation |
|---|---|-----------------|--------------|---------------|
| 1.5 | 0.9 | 2.5-2.9 | ~2.0 | YES |
| 1.8 | 0.7 | 1.5-2.5 | ~2.0 | TRANSITION |
| 2.0 | 0.5 | <1.1 | - | NO |
| 2.5 | 0.5 | <1.1 | - | NO |

**Key hypothesis**: The transition boundary follows β ≈ 1.5/f

For HGBS (λ/W ≈ 2.11):
- If hypothesis correct: f ≈ 1.6-1.8, β ≈ 0.8-1.0
- Test: Do simulations at these parameters show λ/W ≈ 2.0-2.2?

## Integration with Paper

Results will update the paper's:

1. **Abstract**: Replace "urgently needed" with "new simulations show..."
2. **Parameter space section**: Add transition boundary plot
3. **Gravity-dominated section**: Refine interpretation of HGBS regime
4. **Conclusions**: Update with definitive (f, β) constraints

## Troubleshooting

### Issue: "Athena++ binary not found"
**Solution**: Update `ATHENA_BINARY` in `quickstart.sh`

### Issue: "Ray cluster not responding"
**Solution**:
```bash
ray stop
ray start --head --num-cpus 200
```

### Issue: "Out of memory"
**Solution**: Reduce `--num-workers` or increase meshblock size

### Issue: "Analysis fails with HDF5 error"
**Solution**:
```bash
pip install h5py h5py-mpi
```

## Contact

For questions about:
- Campaign design: See main paper
- Technical issues: Check Athena++ documentation
- Ray cluster: Check Ray documentation

---
*Campaign generated for ASTRA filament spacing paper - April 2026*
